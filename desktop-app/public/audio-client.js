/**
 * Audio Client for Overlay Window
 *
 * Manages audio capture and WebSocket streaming for Teams meetings.
 * Runs in the renderer process.
 */

class AudioClient {
    constructor(serverUrl = 'ws://localhost:8000/ws/voice') {
        this.serverUrl = serverUrl;
        this.ws = null;
        this.audioCapture = null;
        this.isConnected = false;
        this.isRecording = false;
        this.bytesStreamed = 0;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 2000;
    }

    /**
     * Initialize and connect to server
     */
    async initialize(options = {}) {
        const {
            captureMicrophone = true,
            captureSystemAudio = true,
            mixStreams = true,
            sampleRate = 16000
        } = options;

        console.log('[AudioClient] Initializing...');

        try {
            // Initialize audio capture (using Web APIs, no electron required)
            await this.initializeAudioCapture({
                captureMicrophone,
                captureSystemAudio,
                mixStreams,
                sampleRate
            });

            console.log('[AudioClient] Audio capture initialized');

            // Connect to WebSocket server
            await this.connectWebSocket();

            return true;

        } catch (error) {
            console.error('[AudioClient] Initialization failed:', error);
            throw error;
        }
    }

    /**
     * Initialize audio capture using Web APIs
     */
    async initializeAudioCapture(options) {
        const { captureMicrophone, captureSystemAudio, mixStreams, sampleRate } = options;

        // Create audio context
        const audioContext = new (window.AudioContext || window.webkitAudioContext)({ sampleRate });

        // Capture microphone
        let micStream = null;
        if (captureMicrophone) {
            micStream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true,
                    sampleRate: sampleRate,
                    channelCount: 1
                },
                video: false
            });
        }

        // For system audio capture, we need to use screen sharing with audio
        let systemStream = null;
        if (captureSystemAudio) {
            try {
                systemStream = await navigator.mediaDevices.getDisplayMedia({
                    video: {
                        displaySurface: 'monitor'
                    },
                    audio: {
                        echoCancellation: false,
                        noiseSuppression: false,
                        sampleRate: sampleRate,
                        channelCount: 1
                    }
                });

                // Stop the video track immediately (we only want audio)
                const videoTrack = systemStream.getVideoTracks()[0];
                if (videoTrack) {
                    videoTrack.stop();
                    systemStream.removeTrack(videoTrack);
                }
            } catch (error) {
                console.warn('[AudioClient] System audio capture not available:', error.message);
            }
        }

        // Create simple audio capture manager
        this.audioCapture = {
            audioContext,
            micStream,
            systemStream,
            processorNode: null,
            isCapturing: false,

            start: function() {
                if (this.isCapturing) return;

                console.log('[AudioCapture] Starting...');
                this.isCapturing = true;

                // Create a destination to mix streams
                const destination = audioContext.createMediaStreamDestination();

                // Connect microphone
                if (micStream) {
                    const micSource = audioContext.createMediaStreamSource(micStream);
                    micSource.connect(destination);
                }

                // Connect system audio
                if (systemStream) {
                    const systemSource = audioContext.createMediaStreamSource(systemStream);
                    systemSource.connect(destination);
                }

                // Create processor to get PCM data
                const processorNode = audioContext.createScriptProcessor(4096, 1, 1);
                const source = audioContext.createMediaStreamSource(destination.stream);
                source.connect(processorNode);
                processorNode.connect(audioContext.destination);

                const self = this;
                processorNode.onaudioprocess = function(e) {
                    if (!self.isCapturing) return;

                    const inputData = e.inputBuffer.getChannelData(0);

                    // Convert float32 to int16 PCM
                    const pcmData = new Int16Array(inputData.length);
                    for (let i = 0; i < inputData.length; i++) {
                        const s = Math.max(-1, Math.min(1, inputData[i]));
                        pcmData[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
                    }

                    // Send to callback
                    if (self.onAudioDataCallback) {
                        self.onAudioDataCallback(pcmData.buffer);
                    }
                };

                this.processorNode = processorNode;
                this.onAudioDataCallback = (buffer) => {
                    if (this.isCapturing) {
                        window.audioClient.sendAudioData(buffer);
                    }
                };
            },

            stop: function() {
                console.log('[AudioCapture] Stopping...');
                this.isCapturing = false;

                if (this.processorNode) {
                    this.processorNode.disconnect();
                    this.processorNode = null;
                }
            },

            cleanup: async function() {
                this.stop();

                if (this.micStream) {
                    this.micStream.getTracks().forEach(track => track.stop());
                    this.micStream = null;
                }

                if (this.systemStream) {
                    this.systemStream.getTracks().forEach(track => track.stop());
                    this.systemStream = null;
                }

                if (this.audioContext && this.audioContext.state !== 'closed') {
                    await this.audioContext.close();
                }
            },

            getStatus: function() {
                return {
                    isCapturing: this.isCapturing,
                    hasMicrophone: !!this.micStream,
                    hasSystemAudio: !!this.systemStream
                };
            }
        };

        // Store reference for callback
        window.audioClient = this;
    }

    /**
     * Connect to WebSocket server
     */
    connectWebSocket() {
        return new Promise((resolve, reject) => {
            console.log('[AudioClient] Connecting to WebSocket:', this.serverUrl);

            this.ws = new WebSocket(this.serverUrl);

            this.ws.onopen = () => {
                console.log('[AudioClient] WebSocket connected');
                this.isConnected = true;
                this.reconnectAttempts = 0;
                resolve();
            };

            this.ws.onclose = () => {
                console.log('[AudioClient] WebSocket disconnected');
                this.isConnected = false;
                this.handleDisconnect();
            };

            this.ws.onerror = (error) => {
                console.error('[AudioClient] WebSocket error:', error);
                reject(error);
            };

            this.ws.onmessage = (event) => {
                this.handleServerMessage(event.data);
            };
        });
    }

    /**
     * Handle server messages (transcriptions, translations, etc.)
     */
    handleServerMessage(data) {
        try {
            const message = JSON.parse(data);

            if (message.type === 'ready') {
                console.log('[AudioClient] Server ready');
                this.emit('ready', message);

            } else if (message.type === 'transcription') {
                console.log('[AudioClient] Transcription received:', message);
                this.emit('transcription', message);

            } else if (message.type === 'new_speaker_detected') {
                console.log('[AudioClient] New speaker detected:', message);
                this.emit('transcription', message);  // Use same handler in overlay

            } else if (message.type === 'error') {
                console.error('[AudioClient] Server error:', message.message);
                this.emit('error', message);
            }

        } catch (error) {
            console.error('[AudioClient] Failed to parse server message:', error);
        }
    }

    /**
     * Send audio data to server
     */
    sendAudioData(audioBuffer) {
        if (!this.isConnected || !this.isRecording) {
            return;
        }

        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(audioBuffer);
            this.bytesStreamed += audioBuffer.byteLength;
        }
    }

    /**
     * Start recording and streaming
     */
    start() {
        if (!this.audioCapture) {
            throw new Error('Audio capture not initialized');
        }

        console.log('[AudioClient] Starting recording...');
        this.isRecording = true;
        this.bytesStreamed = 0;
        this.audioCapture.start();
        this.emit('started');
    }

    /**
     * Stop recording
     */
    stop() {
        console.log('[AudioClient] Stopping recording...');
        this.isRecording = false;

        if (this.audioCapture) {
            this.audioCapture.stop();
        }

        this.emit('stopped');
    }

    /**
     * Handle WebSocket disconnect
     */
    async handleDisconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`[AudioClient] Reconnecting (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);

            await new Promise(resolve => setTimeout(resolve, this.reconnectDelay));

            try {
                await this.connectWebSocket();
                console.log('[AudioClient] Reconnected successfully');
            } catch (error) {
                console.error('[AudioClient] Reconnection failed:', error);
                this.handleDisconnect(); // Try again
            }

        } else {
            console.error('[AudioClient] Max reconnection attempts reached');
            this.emit('disconnected');
        }
    }

    /**
     * Get current status
     */
    getStatus() {
        return {
            isConnected: this.isConnected,
            isRecording: this.isRecording,
            bytesStreamed: this.bytesStreamed,
            audioCapture: this.audioCapture ? this.audioCapture.getStatus() : null
        };
    }

    /**
     * Cleanup and release resources
     */
    async cleanup() {
        console.log('[AudioClient] Cleaning up...');

        this.stop();

        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }

        if (this.audioCapture) {
            await this.audioCapture.cleanup();
            this.audioCapture = null;
        }

        this.listeners = [];

        console.log('[AudioClient] Cleanup complete');
    }

    /**
     * Event emitter
     */
    listeners = [];

    on(event, callback) {
        this.listeners.push({ event, callback });
    }

    emit(event, data) {
        this.listeners
            .filter(l => l.event === event)
            .forEach(l => l.callback(data));
    }
}

// Make available globally for overlay window
window.AudioClient = AudioClient;
