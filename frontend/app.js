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
    await loadAudioDevices();
    connectWebSocket();
});

// Load audio input devices
async function loadAudioDevices() {
    try {
        await navigator.mediaDevices.getUserMedia({ audio: true }); // Request permission first
        const devices = await navigator.mediaDevices.enumerateDevices();
        const audioInputs = devices.filter(device => device.kind === 'audioinput');
        const select = document.getElementById('audio_input_device');

        // Keep default option
        select.innerHTML = '<option value="default">Default</option>';

        audioInputs.forEach(device => {
            const option = document.createElement('option');
            option.value = device.deviceId;
            option.text = device.label || `Microphone ${select.length + 1}`;
            select.appendChild(option);
        });

        // Listen for changes
        navigator.mediaDevices.ondevicechange = loadAudioDevices;

    } catch (error) {
        console.error('Error loading audio devices:', error);
    }
}

// Load configuration from server
async function loadConfig() {
    try {
        const response = await fetch('/api/config');
        const config = await response.json();

        // Populate form - General
        document.getElementById('target_language').value = config.target_language || 'en';
        document.getElementById('source_language').value = config.source_language || '';
        document.getElementById('enable_speaker_id').checked = config.enable_speaker_id !== false;
        document.getElementById('enable_suggestions').checked = config.enable_suggestions !== false;
        document.getElementById('enable_sentiment').checked = config.enable_sentiment !== false;
        document.getElementById('show_latency_monitor').checked = config.show_latency_monitor !== false;

        // AI & Models
        document.getElementById('processing_mode').value = config.processing_mode || 'local';
        document.getElementById('whisper_model').value = config.whisper_model || 'large-v3';
        document.getElementById('latency_priority').value = config.latency_priority || 'realtime';
        document.getElementById('use_intel_gpu').checked = config.use_intel_gpu === true;

        // API Keys (optional)
        if (config.openai_api_key) document.getElementById('openai_api_key').value = config.openai_api_key;
        if (config.deepgram_api_key) document.getElementById('deepgram_api_key').value = config.deepgram_api_key;
        if (config.deepl_api_key) document.getElementById('deepl_api_key').value = config.deepl_api_key;

        // Show/hide latency monitor based on setting
        const latencyMonitor = document.getElementById('latency-monitor');
        if (latencyMonitor) {
            latencyMonitor.style.display = config.show_latency_monitor !== false ? 'block' : 'none';
        }
    } catch (error) {
        console.error('Error loading config:', error);
    }
}

// Save configuration
async function saveConfig() {
    const configs = {
        // General
        target_language: document.getElementById('target_language').value,
        source_language: document.getElementById('source_language').value,
        enable_speaker_id: document.getElementById('enable_speaker_id').checked,
        enable_suggestions: document.getElementById('enable_suggestions').checked,
        enable_sentiment: document.getElementById('enable_sentiment').checked,
        show_latency_monitor: document.getElementById('show_latency_monitor').checked,

        // AI & Models
        processing_mode: document.getElementById('processing_mode').value,
        whisper_model: document.getElementById('whisper_model').value,
        latency_priority: document.getElementById('latency_priority').value,
        use_intel_gpu: document.getElementById('use_intel_gpu').checked,

        // API Keys (only save if not empty)
        openai_api_key: document.getElementById('openai_api_key').value || '',
        deepgram_api_key: document.getElementById('deepgram_api_key').value || '',
        deepl_api_key: document.getElementById('deepl_api_key').value || '',
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

    // Show/hide latency monitor immediately
    const latencyMonitor = document.getElementById('latency-monitor');
    if (latencyMonitor) {
        latencyMonitor.style.display = configs.show_latency_monitor ? 'block' : 'none';
    }

    alert('✅ Configuration saved! Reconnecting...');
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

// Clear all speakers
async function clearAllSpeakers() {
    const confirmed = confirm(
        'Are you sure you want to remove ALL speakers?\n\n' +
        'This will delete all voice profiles and associated names.\n\n' +
        'This action cannot be undone.'
    );

    if (!confirmed) {
        return;
    }

    try {
        const response = await fetch('/api/speakers/clear', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });

        if (response.ok) {
            alert('✅ All speakers have been removed successfully!');
            await loadSpeakers(); // Reload the speakers list
        } else {
            alert('❌ Error clearing speakers. Please try again.');
        }
    } catch (error) {
        console.error('Error clearing speakers:', error);
        alert('❌ Error clearing speakers: ' + error.message);
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

        // Update performance metrics
        if (data.performance) {
            updateLatencyMonitor(data.performance);
        }
    } else if (data.type === 'new_speaker_detected') {
        // Show modal to name the new speaker
        showNameSpeakerModal(data);
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

// Update latency monitor with performance metrics
function updateLatencyMonitor(performance) {
    const updateLatency = (id, value) => {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = `${value}ms`;

            // Color code based on latency thresholds
            element.className = 'latency-value';
            if (value > 2000) {
                element.classList.add('critical');
            } else if (value > 1000) {
                element.classList.add('warning');
            }
        }
    };

    // Use new detailed metrics (with fallback to legacy names)
    updateLatency('latency-speaker', performance.speaker_id_ms || performance.speaker_latency_ms || 0);
    updateLatency('latency-stt', performance.stt_ms || performance.stt_latency_ms || 0);
    updateLatency('latency-translation', performance.translation_ms || performance.translation_latency_ms || 0);
    updateLatency('latency-llm', performance.llm_ms || 0);
    updateLatency('latency-total', performance.total_ms || performance.total_latency_ms || 0);
}

// Show modal to name a new speaker
function showNameSpeakerModal(speakerData) {
    // Check if modal already exists
    let modal = document.getElementById('name-speaker-modal');

    if (!modal) {
        // Create modal
        modal = document.createElement('div');
        modal.id = 'name-speaker-modal';
        modal.className = 'modal';
        modal.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h3>🎤 Novo Falante Detectado</h3>
                    <span class="close-modal" onclick="closeNameSpeakerModal()">&times;</span>
                </div>
                <div class="modal-body">
                    <p>Um novo falante foi detectado. Por favor, identifique:</p>
                    <div class="form-group">
                        <label for="speaker-name-input">Nome:</label>
                        <input type="text" id="speaker-name-input" class="form-control"
                               placeholder="Digite o nome do falante" autofocus>
                    </div>
                    <div class="form-group">
                        <label for="speaker-email-input">Email (opcional):</label>
                        <input type="email" id="speaker-email-input" class="form-control"
                               placeholder="email@example.com">
                    </div>
                    <div class="modal-info">
                        <small>ID sugerido: <strong id="speaker-id-display"></strong></small>
                    </div>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-secondary" onclick="closeNameSpeakerModal()">
                        Cancelar
                    </button>
                    <button class="btn btn-primary" onclick="submitSpeakerName()">
                        Salvar
                    </button>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
    }

    // Update modal with speaker data
    document.getElementById('speaker-id-display').textContent =
        speakerData.suggested_name || speakerData.speaker_id;
    document.getElementById('speaker-name-input').value = speakerData.suggested_name || '';
    document.getElementById('speaker-email-input').value = '';

    // Set language if known
    const langSelect = document.getElementById('speaker-language-input');
    if (langSelect) {
        langSelect.value = speakerData.language || '';
    }

    // Store speaker ID for later use
    modal.dataset.speakerId = speakerData.speaker_id;

    // Show modal
    modal.style.display = 'flex';

    // Focus on name input
    setTimeout(() => {
        document.getElementById('speaker-name-input').focus();
    }, 100);
}

// Close name speaker modal
function closeNameSpeakerModal() {
    const modal = document.getElementById('name-speaker-modal');
    if (modal) {
        modal.style.display = 'none';
    }
}

// Submit speaker name
async function submitSpeakerName() {
    const modal = document.getElementById('name-speaker-modal');
    const speakerId = modal.dataset.speakerId;
    const name = document.getElementById('speaker-name-input').value.trim();
    const email = document.getElementById('speaker-email-input').value.trim();
    const language = document.getElementById('speaker-language-input') ? document.getElementById('speaker-language-input').value : null;

    if (!name) {
        alert('Por favor, digite um nome para o falante.');
        return;
    }

    try {
        const response = await fetch('/api/speakers/name', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                speaker_id: speakerId,
                name: name,
                email: email || null,
                language: language || null
            })
        });

        const result = await response.json();

        if (result.success) {
            // Show success message
            alert(`✅ Falante "${name}" nomeado com sucesso!`);

            // Refresh speakers list
            await loadSpeakers();

            // Close modal
            closeNameSpeakerModal();
        } else {
            // Show error message (handling 'detail' from FastAPI or 'message' from logic)
            const errorMsg = result.message || result.detail || 'Erro desconhecido';
            alert(`❌ Erro ao nomear falante: ${errorMsg}`);
        }
    } catch (error) {
        console.error('Error naming speaker:', error);
        alert(`❌ Erro ao nomear falante: ${error.message}`);
    }
}

// Update status indicator
function updateStatus(status, text) {
    const indicator = document.getElementById('status-indicator');
    const statusText = document.getElementById('status-text');

    indicator.className = `status-indicator ${status}`;
    statusText.textContent = text;
}

// Toggle System Active State
function toggleSystem(checkbox) {
    const statusLabel = document.getElementById('monitor-status');

    if (checkbox.checked) {
        statusLabel.textContent = "Listening...";
        statusLabel.style.color = "var(--success)";
        startRecording();
    } else {
        statusLabel.textContent = "Inactive";
        statusLabel.style.color = "var(--text-secondary)";
        stopRecording();
    }
}

// Start recording
async function startRecording() {
    try {
        const deviceId = document.getElementById('audio_input_device').value;
        const constraints = {
            audio: {
                channelCount: 1,
                sampleRate: 16000,
                deviceId: deviceId !== 'default' ? { exact: deviceId } : undefined
            }
        };

        const stream = await navigator.mediaDevices.getUserMedia(constraints);

        // Initialize AudioContext if needed
        if (!audioContext || audioContext.state === 'closed') {
            // Try to request 16kHz, but browser may ignore it
            audioContext = new AudioContext({ sampleRate: 16000 });
        } else if (audioContext.state === 'suspended') {
            await audioContext.resume();
        }

        console.log(`[Audio] AudioContext Sample Rate: ${audioContext.sampleRate}Hz`);

        // Add the AudioWorklet module
        try {
            await audioContext.audioWorklet.addModule('pcm-processor.js');
        } catch (e) {
            console.warn('Module maybe already added or error:', e);
        }

        const source = audioContext.createMediaStreamSource(stream);

        // Pass the ACTUAL sample rate to the processor so it can downsample if needed
        const workletNode = new AudioWorkletNode(audioContext, 'pcm-processor', {
            processorOptions: {
                sampleRate: audioContext.sampleRate
            }
        });

        workletNode.port.onmessage = (event) => {
            if (ws && ws.readyState === WebSocket.OPEN && isRecording) {
                ws.send(event.data);
            }
        };

        source.connect(workletNode);
        workletNode.connect(audioContext.destination);

        // Store references to clean up later
        mediaRecorder = { source, workletNode, stream };

        isRecording = true;
        updateStatus('recording', 'Recording...');

        // Ensure switch is synced if called programmatically
        const toggle = document.getElementById('system-toggle');
        if (toggle && !toggle.checked) toggle.checked = true;

    } catch (error) {
        console.error('Error starting recording:', error);
        alert('Error accessing microphone/audio: ' + error.message);
    }
}

// Stop recording
function stopRecording() {
    isRecording = false;

    if (mediaRecorder) {
        if (mediaRecorder.workletNode) {
            mediaRecorder.workletNode.disconnect();
            mediaRecorder.workletNode.port.onmessage = null;
        }
        if (mediaRecorder.source) {
            mediaRecorder.source.disconnect();
        }
        if (mediaRecorder.stream) {
            mediaRecorder.stream.getTracks().forEach(track => track.stop());
        }
        mediaRecorder = null;
    }

    if (audioContext) {
        audioContext.close();
        audioContext = null;
    }

    updateStatus('connected', 'Connected');

    // Ensure switch is synced
    const toggle = document.getElementById('system-toggle');
    if (toggle && toggle.checked) {
        toggle.checked = false;
        document.getElementById('monitor-status').textContent = "Inactive";
        document.getElementById('monitor-status').style.color = "var(--text-secondary)";
    }
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

    // Speaker identification badge
    let speakerBadgeHTML = '';
    if (data.is_enrolled_speaker) {
        const confidencePercent = Math.round((data.speaker_confidence || 0) * 100);
        speakerBadgeHTML = `<span class="speaker-badge enrolled" title="Enrolled speaker - ${confidencePercent}% confidence">✓ ${confidencePercent}%</span>`;
    } else if (data.is_new_speaker) {
        speakerBadgeHTML = `<span class="speaker-badge new" title="Unknown speaker detected">? New</span>`;
    }

    // Speaker email if available
    const emailHTML = data.speaker_email ? `<span style="color: #94a3b8; font-size: 11px; margin-left: 8px;">${data.speaker_email}</span>` : '';

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
                ${speakerFlag} <strong>${data.speaker_name || data.speaker_id}</strong>
                ${speakerBadgeHTML}
                ${emailHTML}
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

    // Auto-scroll to latest message with smooth animation
    requestAnimationFrame(() => {
        conversationArea.scrollTo({
            top: conversationArea.scrollHeight,
            behavior: 'smooth'
        });
    });
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
