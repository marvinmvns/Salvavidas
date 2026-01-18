/**
 * Audio Capture Module
 *
 * Captures audio from Teams meetings without disrupting the conference.
 * Supports:
 * - System audio (loopback) - what you hear from Teams
 * - Microphone input - your voice
 * - Mixed/separated streams
 */

const { desktopCapturer } = require('electron');

class AudioCaptureManager {
    constructor() {
        this.mediaStream = null;
        this.audioContext = null;
        this.microphoneStream = null;
        this.systemAudioStream = null;
        this.isCapturing = false;
        this.onAudioDataCallback = null;

        // Audio processing nodes
        this.microphoneSource = null;
        this.systemAudioSource = null;
        this.mixerNode = null;
        this.processorNode = null;
    }

    /**
     * Initialize audio capture
     *
     * @param {Object} options - Capture options
     * @param {boolean} options.captureMicrophone - Capture user's microphone
     * @param {boolean} options.captureSystemAudio - Capture system audio (loopback)
     * @param {boolean} options.mixStreams - Mix mic + system audio into one stream
     * @param {number} options.sampleRate - Sample rate (default: 16000)
     * @param {Function} options.onAudioData - Callback for audio data
     */
    async initialize(options = {}) {
        const {
            captureMicrophone = true,
            captureSystemAudio = true,
            mixStreams = true,
            sampleRate = 16000,
            onAudioData = null
        } = options;

        this.onAudioDataCallback = onAudioData;

        console.log('[AudioCapture] Initializing with options:', {
            captureMicrophone,
            captureSystemAudio,
            mixStreams,
            sampleRate
        });

        // Create audio context
        this.audioContext = new AudioContext({ sampleRate });

        try {
            // Capture microphone if requested
            if (captureMicrophone) {
                await this.captureMicrophone();
            }

            // Capture system audio if requested
            if (captureSystemAudio) {
                await this.captureSystemAudio();
            }

            // Setup audio processing
            await this.setupAudioProcessing(mixStreams);

            console.log('[AudioCapture] Initialization complete');
            return true;

        } catch (error) {
            console.error('[AudioCapture] Initialization failed:', error);
            throw error;
        }
    }

    /**
     * Capture microphone audio (user's voice)
     */
    async captureMicrophone() {
        try {
            console.log('[AudioCapture] Capturing microphone...');

            this.microphoneStream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true,
                    sampleRate: this.audioContext.sampleRate,
                    channelCount: 1
                },
                video: false
            });

            this.microphoneSource = this.audioContext.createMediaStreamSource(this.microphoneStream);
            console.log('[AudioCapture] Microphone captured successfully');

        } catch (error) {
            console.error('[AudioCapture] Failed to capture microphone:', error);
            throw new Error('Microphone access denied or not available');
        }
    }

    /**
     * Capture system audio (what you hear from Teams)
     * This uses screen/audio capture with system audio enabled
     */
    async captureSystemAudio() {
        try {
            console.log('[AudioCapture] Capturing system audio...');

            // Get available audio sources (screen/window sharing with audio)
            const sources = await desktopCapturer.getSources({
                types: ['window', 'screen']
            });

            // Find Teams window or use primary screen
            let targetSource = sources.find(source =>
                source.name.toLowerCase().includes('teams') ||
                source.name.toLowerCase().includes('microsoft teams')
            );

            if (!targetSource) {
                // Fallback to primary display
                targetSource = sources.find(source => source.name.includes('Screen')) || sources[0];
            }

            console.log('[AudioCapture] Target source:', targetSource?.name);

            if (!targetSource) {
                throw new Error('No audio source available');
            }

            // Capture with system audio
            // Note: This requires specific Chrome flags or using displayMedia API
            this.systemAudioStream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    mandatory: {
                        chromeMediaSource: 'desktop',
                        chromeMediaSourceId: targetSource.id
                    }
                },
                video: {
                    mandatory: {
                        chromeMediaSource: 'desktop',
                        chromeMediaSourceId: targetSource.id,
                        minWidth: 1280,
                        maxWidth: 1280,
                        minHeight: 720,
                        maxHeight: 720
                    }
                }
            });

            // Extract audio track only
            const audioTracks = this.systemAudioStream.getAudioTracks();
            if (audioTracks.length > 0) {
                const audioStream = new MediaStream([audioTracks[0]]);
                this.systemAudioSource = this.audioContext.createMediaStreamSource(audioStream);
                console.log('[AudioCapture] System audio captured successfully');
            } else {
                console.warn('[AudioCapture] No audio track in system capture, using alternative method');
                await this.captureSystemAudioFallback();
            }

        } catch (error) {
            console.error('[AudioCapture] Failed to capture system audio:', error);
            // Try fallback method
            await this.captureSystemAudioFallback();
        }
    }

    /**
     * Fallback method for system audio capture
     * Uses loopback device if available
     */
    async captureSystemAudioFallback() {
        try {
            console.log('[AudioCapture] Using fallback system audio capture...');

            // Try to get system audio using getDisplayMedia (modern approach)
            this.systemAudioStream = await navigator.mediaDevices.getDisplayMedia({
                audio: {
                    echoCancellation: false,
                    noiseSuppression: false,
                    autoGainControl: false,
                    sampleRate: this.audioContext.sampleRate
                },
                video: {
                    width: 1280,
                    height: 720,
                    frameRate: 1 // Minimal video to reduce overhead
                }
            });

            const audioTracks = this.systemAudioStream.getAudioTracks();
            if (audioTracks.length > 0) {
                const audioStream = new MediaStream([audioTracks[0]]);
                this.systemAudioSource = this.audioContext.createMediaStreamSource(audioStream);
                console.log('[AudioCapture] System audio fallback successful');
            } else {
                throw new Error('No audio track available in fallback');
            }

        } catch (error) {
            console.error('[AudioCapture] Fallback also failed:', error);
            console.warn('[AudioCapture] Proceeding with microphone only');
        }
    }

    /**
     * Setup audio processing pipeline
     *
     * @param {boolean} mixStreams - Whether to mix mic + system audio
     */
    async setupAudioProcessing(mixStreams = true) {
        console.log('[AudioCapture] Setting up audio processing...');

        if (mixStreams && this.microphoneSource && this.systemAudioSource) {
            // Create mixer node to combine microphone + system audio
            this.mixerNode = this.audioContext.createGain();
            this.mixerNode.gain.value = 1.0;

            this.microphoneSource.connect(this.mixerNode);
            this.systemAudioSource.connect(this.mixerNode);

            // Create processor for mixed audio
            this.processorNode = this.audioContext.createScriptProcessor(4096, 1, 1);
            this.mixerNode.connect(this.processorNode);

            console.log('[AudioCapture] Mixing microphone + system audio');

        } else if (this.microphoneSource) {
            // Microphone only
            this.processorNode = this.audioContext.createScriptProcessor(4096, 1, 1);
            this.microphoneSource.connect(this.processorNode);

            console.log('[AudioCapture] Processing microphone audio only');

        } else if (this.systemAudioSource) {
            // System audio only
            this.processorNode = this.audioContext.createScriptProcessor(4096, 1, 1);
            this.systemAudioSource.connect(this.processorNode);

            console.log('[AudioCapture] Processing system audio only');

        } else {
            throw new Error('No audio source available for processing');
        }

        // Connect processor to destination (required for processing to work)
        this.processorNode.connect(this.audioContext.destination);

        // Setup audio data callback
        this.processorNode.onaudioprocess = (event) => {
            if (!this.isCapturing) return;

            const inputData = event.inputBuffer.getChannelData(0);
            const outputData = new Int16Array(inputData.length);

            // Convert float32 to int16
            for (let i = 0; i < inputData.length; i++) {
                const s = Math.max(-1, Math.min(1, inputData[i]));
                outputData[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
            }

            // Send audio data via callback
            if (this.onAudioDataCallback) {
                this.onAudioDataCallback(outputData.buffer);
            }
        };
    }

    /**
     * Start capturing audio
     */
    start() {
        console.log('[AudioCapture] Starting audio capture...');
        this.isCapturing = true;

        if (this.audioContext.state === 'suspended') {
            this.audioContext.resume();
        }
    }

    /**
     * Stop capturing audio
     */
    stop() {
        console.log('[AudioCapture] Stopping audio capture...');
        this.isCapturing = false;

        if (this.audioContext && this.audioContext.state !== 'closed') {
            this.audioContext.suspend();
        }
    }

    /**
     * Release all resources
     */
    async cleanup() {
        console.log('[AudioCapture] Cleaning up resources...');

        this.stop();

        // Stop all tracks
        if (this.microphoneStream) {
            this.microphoneStream.getTracks().forEach(track => track.stop());
            this.microphoneStream = null;
        }

        if (this.systemAudioStream) {
            this.systemAudioStream.getTracks().forEach(track => track.stop());
            this.systemAudioStream = null;
        }

        // Disconnect audio nodes
        if (this.microphoneSource) {
            this.microphoneSource.disconnect();
            this.microphoneSource = null;
        }

        if (this.systemAudioSource) {
            this.systemAudioSource.disconnect();
            this.systemAudioSource = null;
        }

        if (this.mixerNode) {
            this.mixerNode.disconnect();
            this.mixerNode = null;
        }

        if (this.processorNode) {
            this.processorNode.disconnect();
            this.processorNode = null;
        }

        // Close audio context
        if (this.audioContext) {
            await this.audioContext.close();
            this.audioContext = null;
        }

        this.onAudioDataCallback = null;

        console.log('[AudioCapture] Cleanup complete');
    }

    /**
     * Get current capture status
     */
    getStatus() {
        return {
            isCapturing: this.isCapturing,
            hasMicrophone: !!this.microphoneSource,
            hasSystemAudio: !!this.systemAudioSource,
            sampleRate: this.audioContext?.sampleRate || 0,
            state: this.audioContext?.state || 'closed'
        };
    }
}

module.exports = AudioCaptureManager;
