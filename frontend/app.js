// Salvavidas Frontend Application
let ws = null;
let mediaRecorder = null;
let audioContext = null;
let isRecording = false;
let audioChunks = [];

// Language flags
const languageFlags = {
    'en': '🇺🇸',
    'pt': '🇧🇷',
    'es': '🇪🇸',
    'fr': '🇫🇷',
    'de': '🇩🇪',
    'it': '🇮🇹',
    'ja': '🇯🇵',
    'zh': '🇨🇳',
};

// Initialize on page load
document.addEventListener('DOMContentLoaded', async () => {
    await loadConfig();
    await loadSpeakers();
    connectWebSocket();
});

// Load configuration from server
async function loadConfig() {
    try {
        const response = await fetch('/api/config');
        const config = await response.json();

        // Populate form
        document.getElementById('processing_mode').value = config.processing_mode || 'local';
        document.getElementById('target_language').value = config.target_language || 'en';
        document.getElementById('latency_priority').value = config.latency_priority || 'realtime';
        document.getElementById('enable_speaker_id').checked = config.enable_speaker_id !== false;
        document.getElementById('enable_suggestions').checked = config.enable_suggestions !== false;
        document.getElementById('use_intel_gpu').checked = config.use_intel_gpu === true;
    } catch (error) {
        console.error('Error loading config:', error);
    }
}

// Save configuration
async function saveConfig() {
    const configs = {
        processing_mode: document.getElementById('processing_mode').value,
        target_language: document.getElementById('target_language').value,
        latency_priority: document.getElementById('latency_priority').value,
        enable_speaker_id: document.getElementById('enable_speaker_id').checked,
        enable_suggestions: document.getElementById('enable_suggestions').checked,
        use_intel_gpu: document.getElementById('use_intel_gpu').checked,
    };

    for (const [key, value] of Object.entries(configs)) {
        try {
            await fetch('/api/config', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ key, value }),
            });
        } catch (error) {
            console.error(`Error saving ${key}:`, error);
        }
    }

    alert('Configuration saved! Reconnecting...');
    connectWebSocket();
}

// Load speakers
async function loadSpeakers() {
    try {
        const response = await fetch('/api/speakers');
        const speakers = await response.json();

        const speakersList = document.getElementById('speakers-list');

        if (speakers.length === 0) {
            speakersList.innerHTML = '<p style="color: #718096; font-size: 0.9rem;">No speakers yet</p>';
            return;
        }

        speakersList.innerHTML = speakers.map(speaker => `
            <div class="speaker-chip">
                <div>
                    <span class="speaker-flag">${languageFlags[speaker.language] || '🗣️'}</span>
                    <strong>${speaker.name || speaker.speaker_id}</strong>
                </div>
                <small>${(speaker.confidence * 100).toFixed(0)}%</small>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error loading speakers:', error);
    }
}

// Connect to WebSocket
function connectWebSocket() {
    if (ws) {
        ws.close();
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    ws = new WebSocket(`${protocol}//${window.location.host}/ws/voice`);

    ws.onopen = () => {
        updateStatus('connected', 'Connected');
        console.log('WebSocket connected');
    };

    ws.onclose = () => {
        updateStatus('disconnected', 'Disconnected');
        console.log('WebSocket disconnected');
    };

    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        updateStatus('disconnected', 'Error');
    };

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleWebSocketMessage(data);
    };
}

// Handle WebSocket messages
function handleWebSocketMessage(data) {
    if (data.type === 'ready') {
        console.log('Server ready');
    } else if (data.type === 'transcription') {
        displayConversationTurn(data);
        loadSpeakers(); // Refresh speakers list
    } else if (data.type === 'error') {
        console.error('Server error:', data.message);
        alert(`Error: ${data.message}`);
    } else if (data.type === 'history_cleared') {
        document.getElementById('conversation-area').innerHTML = `
            <p style="text-align: center; color: #718096; margin-top: 50px;">
                Conversation cleared. Start recording to begin...
            </p>
        `;
    }
}

// Update status indicator
function updateStatus(status, text) {
    const indicator = document.getElementById('status-indicator');
    const statusText = document.getElementById('status-text');

    indicator.className = `status-indicator ${status}`;
    statusText.textContent = text;
}

// Start recording
async function startRecording() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({
            audio: {
                channelCount: 1,
                sampleRate: 16000,
            }
        });

        audioContext = new AudioContext({ sampleRate: 16000 });
        const source = audioContext.createMediaStreamSource(stream);
        const processor = audioContext.createScriptProcessor(4096, 1, 1);

        source.connect(processor);
        processor.connect(audioContext.destination);

        processor.onaudioprocess = (e) => {
            if (!isRecording) return;

            const inputData = e.inputBuffer.getChannelData(0);
            const outputData = new Int16Array(inputData.length);

            // Convert float to int16
            for (let i = 0; i < inputData.length; i++) {
                const s = Math.max(-1, Math.min(1, inputData[i]));
                outputData[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
            }

            // Send to server
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(outputData.buffer);
            }
        };

        isRecording = true;
        updateStatus('recording', 'Recording...');
        document.getElementById('start-btn').style.display = 'none';
        document.getElementById('stop-btn').style.display = 'inline-block';

    } catch (error) {
        console.error('Error starting recording:', error);
        alert('Error accessing microphone. Please grant permission.');
    }
}

// Stop recording
function stopRecording() {
    isRecording = false;

    if (audioContext) {
        audioContext.close();
        audioContext = null;
    }

    updateStatus('connected', 'Connected');
    document.getElementById('start-btn').style.display = 'inline-block';
    document.getElementById('stop-btn').style.display = 'none';
}

// Display conversation turn
function displayConversationTurn(data) {
    const conversationArea = document.getElementById('conversation-area');

    // Remove placeholder text
    if (conversationArea.querySelector('p[style*="text-align: center"]')) {
        conversationArea.innerHTML = '';
    }

    const messageDiv = document.createElement('div');
    messageDiv.className = 'message';

    const timestamp = new Date(data.timestamp).toLocaleTimeString();
    const speakerFlag = languageFlags[data.speaker_language] || '🗣️';

    let suggestionsHTML = '';
    if (data.suggestions && data.suggestions.length > 0) {
        suggestionsHTML = `
            <div class="suggestions">
                <div class="suggestions-title">💡 Suggested responses:</div>
                ${data.suggestions.map((s, i) => `
                    <span class="suggestion-item" onclick="copySuggestion('${s.text.replace(/'/g, "\\'")}')">
                        ${s.text}
                    </span>
                `).join('')}
            </div>
        `;
    }

    messageDiv.innerHTML = `
        <div class="message-header">
            <div class="speaker-info">
                ${speakerFlag} ${data.speaker_name || data.speaker_id}
            </div>
            <div class="timestamp">${timestamp}</div>
        </div>
        <div class="message-content">
            <div class="original-text">
                <strong>${data.source_language.toUpperCase()}:</strong> ${data.original_text}
            </div>
            <div class="translated-text">
                <strong>${data.target_language.toUpperCase()}:</strong> ${data.translated_text}
            </div>
            ${suggestionsHTML}
        </div>
    `;

    conversationArea.appendChild(messageDiv);
    conversationArea.scrollTop = conversationArea.scrollHeight;
}

// Copy suggestion to clipboard
function copySuggestion(text) {
    navigator.clipboard.writeText(text);
    alert('Copied to clipboard!');
}

// Clear conversation
function clearConversation() {
    if (confirm('Clear conversation history?')) {
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: 'clear_history' }));
        }
    }
}
