// Salvavidas Frontend - Optimized for Real-time Performance
let ws = null;
let audioContext = null;
let audioProcessor = null;
let isRecording = false;
let processingIndicator = null;

// Performance metrics
let metrics = {
    messagesProcessed: 0,
    avgLatency: 0,
    lastMessageTime: null
};

// Language flags
const languageFlags = {
    'en': '🇺🇸', 'pt': '🇧🇷', 'es': '🇪🇸', 'fr': '🇫🇷',
    'de': '🇩🇪', 'it': '🇮🇹', 'ja': '🇯🇵', 'zh': '🇨🇳',
};

// Initialize
document.addEventListener('DOMContentLoaded', async () => {
    await Promise.all([
        loadConfig(),
        loadSpeakers()
    ]);
    connectWebSocket();
    initPerformanceMonitor();
});

// Performance monitor
function initPerformanceMonitor() {
    const perfDiv = document.createElement('div');
    perfDiv.id = 'perf-monitor';
    perfDiv.style.cssText = `
        position: fixed;
        top: 10px;
        right: 10px;
        background: rgba(0,0,0,0.8);
        color: #0f0;
        padding: 10px;
        border-radius: 5px;
        font-family: monospace;
        font-size: 11px;
        z-index: 10000;
        display: none;
    `;
    document.body.appendChild(perfDiv);

    // Update every second
    setInterval(() => {
        if (perfDiv.style.display === 'block') {
            perfDiv.innerHTML = `
                Messages: ${metrics.messagesProcessed}<br>
                Avg Latency: ${metrics.avgLatency.toFixed(0)}ms<br>
                WS State: ${ws ? ws.readyState : 'N/A'}<br>
                Recording: ${isRecording}
            `;
        }
    }, 1000);

    // Toggle with Ctrl+P
    document.addEventListener('keydown', (e) => {
        if (e.ctrlKey && e.key === 'p') {
            e.preventDefault();
            perfDiv.style.display = perfDiv.style.display === 'none' ? 'block' : 'none';
        }
    });
}

// Load config (cached)
let configCache = null;
async function loadConfig() {
    if (configCache) return configCache;

    try {
        const response = await fetch('/api/config');
        const config = await response.json();
        configCache = config;

        // Populate form (batch DOM updates)
        requestAnimationFrame(() => {
            document.getElementById('processing_mode').value = config.processing_mode || 'local';
            document.getElementById('target_language').value = config.target_language || 'en';
            document.getElementById('latency_priority').value = config.latency_priority || 'realtime';
            document.getElementById('enable_speaker_id').checked = config.enable_speaker_id !== false;
            document.getElementById('enable_suggestions').checked = config.enable_suggestions !== false;
            document.getElementById('use_intel_gpu').checked = config.use_intel_gpu === true;
        });

        return config;
    } catch (error) {
        console.error('Error loading config:', error);
        return {};
    }
}

// Save configuration (optimized)
async function saveConfig() {
    const configs = {
        processing_mode: document.getElementById('processing_mode').value,
        target_language: document.getElementById('target_language').value,
        latency_priority: document.getElementById('latency_priority').value,
        enable_speaker_id: document.getElementById('enable_speaker_id').checked,
        enable_suggestions: document.getElementById('enable_suggestions').checked,
        use_intel_gpu: document.getElementById('use_intel_gpu').checked,
    };

    // Invalidate cache
    configCache = null;

    // Parallel requests
    const promises = Object.entries(configs).map(([key, value]) =>
        fetch('/api/config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ key, value }),
        }).catch(err => console.error(`Error saving ${key}:`, err))
    );

    await Promise.all(promises);

    showNotification('Configuration saved! Reconnecting...', 'success');
    connectWebSocket();
}

// Load speakers (optimized)
let speakersCache = new Map();
async function loadSpeakers() {
    try {
        const response = await fetch('/api/speakers');
        const speakers = await response.json();

        const speakersList = document.getElementById('speakers-list');

        if (speakers.length === 0) {
            speakersList.innerHTML = '<p style="color: #718096; font-size: 0.9rem;">No speakers yet</p>';
            return;
        }

        // Use DocumentFragment for batch DOM updates
        const fragment = document.createDocumentFragment();

        speakers.forEach(speaker => {
            speakersCache.set(speaker.speaker_id, speaker);

            const div = document.createElement('div');
            div.className = 'speaker-chip';
            div.innerHTML = `
                <div>
                    <span class="speaker-flag">${languageFlags[speaker.language] || '🗣️'}</span>
                    <strong>${speaker.name || speaker.speaker_id}</strong>
                </div>
                <small>${(speaker.confidence * 100).toFixed(0)}%</small>
            `;
            fragment.appendChild(div);
        });

        speakersList.innerHTML = '';
        speakersList.appendChild(fragment);
    } catch (error) {
        console.error('Error loading speakers:', error);
    }
}

// WebSocket with auto-reconnect
let reconnectTimeout = null;
function connectWebSocket() {
    if (ws) {
        ws.close();
    }

    clearTimeout(reconnectTimeout);

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    ws = new WebSocket(`${protocol}//${window.location.host}/ws/voice`);

    // Binary type for audio
    ws.binaryType = 'arraybuffer';

    ws.onopen = () => {
        updateStatus('connected', 'Connected');
        console.log('WebSocket connected');
        showNotification('Connected to server', 'success', 2000);
    };

    ws.onclose = () => {
        updateStatus('disconnected', 'Disconnected');
        console.log('WebSocket disconnected');

        // Auto-reconnect after 3s
        reconnectTimeout = setTimeout(() => {
            console.log('Attempting to reconnect...');
            connectWebSocket();
        }, 3000);
    };

    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        updateStatus('disconnected', 'Error');
    };

    ws.onmessage = (event) => {
        const startTime = performance.now();
        const data = JSON.parse(event.data);
        handleWebSocketMessage(data);

        // Track latency
        const latency = performance.now() - startTime;
        metrics.avgLatency = (metrics.avgLatency * metrics.messagesProcessed + latency) / (metrics.messagesProcessed + 1);
        metrics.messagesProcessed++;
    };
}

// Handle messages (optimized)
function handleWebSocketMessage(data) {
    if (data.type === 'ready') {
        console.log('Server ready');
        hideProcessingIndicator();
    } else if (data.type === 'transcription') {
        hideProcessingIndicator();
        displayConversationTurnOptimized(data);

        // Throttled speaker list update (max every 2s)
        throttle(() => loadSpeakers(), 2000)();

    } else if (data.type === 'error') {
        console.error('Server error:', data.message);
        hideProcessingIndicator();
        showNotification(`Error: ${data.message}`, 'error');
    } else if (data.type === 'history_cleared') {
        const conversationArea = document.getElementById('conversation-area');
        conversationArea.innerHTML = `
            <p style="text-align: center; color: #718096; margin-top: 50px;">
                Conversation cleared. Start recording to begin...
            </p>
        `;
    }
}

// Processing indicator
function showProcessingIndicator() {
    if (!processingIndicator) {
        processingIndicator = document.createElement('div');
        processingIndicator.className = 'processing-indicator';
        processingIndicator.innerHTML = `
            <div class="spinner"></div>
            <span>Processing...</span>
        `;
        processingIndicator.style.cssText = `
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: rgba(102, 126, 234, 0.95);
            color: white;
            padding: 20px 40px;
            border-radius: 10px;
            display: flex;
            align-items: center;
            gap: 15px;
            z-index: 9999;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        `;

        const style = document.createElement('style');
        style.textContent = `
            .spinner {
                width: 20px;
                height: 20px;
                border: 3px solid rgba(255,255,255,0.3);
                border-top-color: white;
                border-radius: 50%;
                animation: spin 0.8s linear infinite;
            }
            @keyframes spin {
                to { transform: rotate(360deg); }
            }
        `;
        document.head.appendChild(style);
    }

    if (!document.body.contains(processingIndicator)) {
        document.body.appendChild(processingIndicator);
    }
}

function hideProcessingIndicator() {
    if (processingIndicator && document.body.contains(processingIndicator)) {
        processingIndicator.remove();
    }
}

// Notification system
function showNotification(message, type = 'info', duration = 3000) {
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 25px;
        background: ${type === 'success' ? '#48bb78' : type === 'error' ? '#f56565' : '#667eea'};
        color: white;
        border-radius: 8px;
        box-shadow: 0 5px 15px rgba(0,0,0,0.3);
        z-index: 10000;
        animation: slideIn 0.3s ease-out;
    `;
    notification.textContent = message;

    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideIn {
            from {
                transform: translateX(400px);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
    `;
    document.head.appendChild(style);

    document.body.appendChild(notification);

    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease-in';
        setTimeout(() => notification.remove(), 300);
    }, duration);
}

// Update status (optimized)
function updateStatus(status, text) {
    requestAnimationFrame(() => {
        const indicator = document.getElementById('status-indicator');
        const statusText = document.getElementById('status-text');

        indicator.className = `status-indicator ${status}`;
        statusText.textContent = text;
    });
}

// Start recording (optimized)
async function startRecording() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({
            audio: {
                channelCount: 1,
                sampleRate: 16000,
                echoCancellation: true,
                noiseSuppression: true,
                autoGainControl: true,
            }
        });

        audioContext = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 16000 });
        const source = audioContext.createMediaStreamSource(stream);

        // Use AudioWorklet for better performance (fallback to ScriptProcessor)
        if (audioContext.audioWorklet) {
            // Modern approach - would need separate worklet file
            // For now, use ScriptProcessor with optimizations
            setupScriptProcessor(source);
        } else {
            setupScriptProcessor(source);
        }

        isRecording = true;
        updateStatus('recording', '🎤 Recording...');
        document.getElementById('start-btn').style.display = 'none';
        document.getElementById('stop-btn').style.display = 'inline-block';

        showNotification('Recording started', 'success', 2000);

    } catch (error) {
        console.error('Error starting recording:', error);
        showNotification('Error accessing microphone. Please grant permission.', 'error');
    }
}

function setupScriptProcessor(source) {
    audioProcessor = audioContext.createScriptProcessor(2048, 1, 1); // Smaller buffer for lower latency

    let bufferQueue = [];
    let lastSendTime = 0;
    const SEND_INTERVAL = 100; // Send every 100ms

    audioProcessor.onaudioprocess = (e) => {
        if (!isRecording) return;

        const inputData = e.inputBuffer.getChannelData(0);
        const outputData = new Int16Array(inputData.length);

        // Optimized conversion
        for (let i = 0; i < inputData.length; i++) {
            const s = Math.max(-1, Math.min(1, inputData[i]));
            outputData[i] = (s < 0 ? s * 0x8000 : s * 0x7FFF) | 0;
        }

        bufferQueue.push(outputData);

        // Throttle sends
        const now = Date.now();
        if (now - lastSendTime >= SEND_INTERVAL && ws && ws.readyState === WebSocket.OPEN) {
            if (bufferQueue.length > 0) {
                // Combine buffers
                const totalLength = bufferQueue.reduce((sum, buf) => sum + buf.length, 0);
                const combined = new Int16Array(totalLength);
                let offset = 0;
                for (const buf of bufferQueue) {
                    combined.set(buf, offset);
                    offset += buf.length;
                }

                ws.send(combined.buffer);
                bufferQueue = [];
                lastSendTime = now;

                // Show processing indicator
                showProcessingIndicator();
            }
        }
    };

    source.connect(audioProcessor);
    audioProcessor.connect(audioContext.destination);
}

// Stop recording
function stopRecording() {
    isRecording = false;

    if (audioProcessor) {
        audioProcessor.disconnect();
        audioProcessor = null;
    }

    if (audioContext) {
        audioContext.close();
        audioContext = null;
    }

    updateStatus('connected', 'Connected');
    document.getElementById('start-btn').style.display = 'inline-block';
    document.getElementById('stop-btn').style.display = 'none';

    hideProcessingIndicator();
    showNotification('Recording stopped', 'info', 2000);
}

// Display conversation (highly optimized)
const messageTemplate = document.createElement('template');
function displayConversationTurnOptimized(data) {
    const conversationArea = document.getElementById('conversation-area');

    // Remove placeholder
    const placeholder = conversationArea.querySelector('p[style*="text-align: center"]');
    if (placeholder) {
        placeholder.remove();
    }

    const timestamp = new Date(data.timestamp).toLocaleTimeString();
    const speakerFlag = languageFlags[data.speaker_language] || '🗣️';

    let suggestionsHTML = '';
    if (data.suggestions && data.suggestions.length > 0) {
        suggestionsHTML = `
            <div class="suggestions">
                <div class="suggestions-title">💡 Suggested responses:</div>
                ${data.suggestions.map(s => `
                    <span class="suggestion-item" onclick="copySuggestion(\`${s.text}\`)">
                        ${s.text}
                    </span>
                `).join('')}
            </div>
        `;
    }

    messageTemplate.innerHTML = `
        <div class="message" style="animation: fadeIn 0.3s ease-out;">
            <div class="message-header">
                <div class="speaker-info">
                    ${speakerFlag} ${data.speaker_name || data.speaker_id}
                    <span class="lang-tag">${data.speaker_language.toUpperCase()}</span>
                </div>
                <div class="timestamp">${timestamp}</div>
            </div>
            <div class="message-content">
                <div class="original-text">
                    ${data.original_text}
                </div>
                <div class="translated-text">
                    <strong>→ ${data.target_language.toUpperCase()}:</strong> ${data.translated_text}
                </div>
                ${suggestionsHTML}
            </div>
        </div>
    `;

    const messageNode = messageTemplate.content.cloneNode(true);

    // Use requestAnimationFrame for smooth rendering
    requestAnimationFrame(() => {
        conversationArea.appendChild(messageNode);
        conversationArea.scrollTop = conversationArea.scrollHeight;
    });
}

// Utility: Throttle
const throttleTimers = new Map();
function throttle(func, limit) {
    return function(...args) {
        const key = func.toString();
        if (!throttleTimers.has(key)) {
            func.apply(this, args);
            throttleTimers.set(key, setTimeout(() => {
                throttleTimers.delete(key);
            }, limit));
        }
    };
}

// Copy suggestion
function copySuggestion(text) {
    navigator.clipboard.writeText(text).then(() => {
        showNotification('Copied to clipboard!', 'success', 1500);
    }).catch(() => {
        showNotification('Failed to copy', 'error', 1500);
    });
}

// Clear conversation
function clearConversation() {
    if (confirm('Clear conversation history?')) {
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: 'clear_history' }));
        }
    }
}

// Add fadeIn animation
const fadeInStyle = document.createElement('style');
fadeInStyle.textContent = `
    @keyframes fadeIn {
        from {
            opacity: 0;
            transform: translateY(10px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    .lang-tag {
        display: inline-block;
        margin-left: 8px;
        padding: 2px 8px;
        background: rgba(102, 126, 234, 0.2);
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: normal;
    }
`;
document.head.appendChild(fadeInStyle);
