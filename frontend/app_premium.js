// Salvavidas Premium - Meeting Assistant + Translator
let currentMode = 'translator';
let ws = null;
let audioContext = null;
let isRecording = false;
let meetingStartTime = null;
let messagesCount = 0;

// Set mode
function setMode(mode) {
    currentMode = mode;
    document.body.setAttribute('data-mode', mode);

    // Update active button
    document.querySelectorAll('.mode-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.classList.add('active');

    showNotification(`Switched to ${mode === 'translator' ? 'Translator' : 'Meeting Assistant'} mode`, 'success');
}

// Toggle discrete mode
function toggleDiscrete() {
    const overlay = document.getElementById('discrete-overlay');
    overlay.classList.toggle('active');
}

// Use suggestion
let currentSuggestion = null;
function useSuggestion(suggestion) {
    if (!suggestion && !currentSuggestion) return;

    const text = suggestion || currentSuggestion;

    // Copy to clipboard
    navigator.clipboard.writeText(text).then(() => {
        showNotification('Response copied! Ready to paste.', 'success');
    });
}

// Keyboard shortcuts
document.addEventListener('keydown', (e) => {
    // Ctrl+H: Toggle discrete overlay
    if (e.ctrlKey && e.key === 'h') {
        e.preventDefault();
        toggleDiscrete();
    }

    // Ctrl+U: Use current suggestion
    if (e.ctrlKey && e.key === 'u') {
        e.preventDefault();
        useSuggestion();
    }

    // Ctrl+M: Toggle mode
    if (e.ctrlKey && e.key === 'm') {
        e.preventDefault();
        const newMode = currentMode === 'translator' ? 'assistant' : 'translator';
        setMode(newMode);
    }
});

// Enhanced WebSocket message handling
function handleWebSocketMessagePremium(data) {
    if (data.type === 'transcription') {
        messagesCount++;
        updateMeetingStats();

        // Update current speech
        document.getElementById('current-speech').textContent =
            data.original_text.substring(0, 50) + '...';

        // Display in conversation area
        displayConversationTurn(data);

        // Meeting Assistant Mode: Advanced suggestions
        if (currentMode === 'assistant') {
            displayAdvancedSuggestions(data);
            analyzeSentiment(data.original_text);
        }

        // Update discrete overlay
        if (data.suggestions && data.suggestions.length > 0) {
            currentSuggestion = data.suggestions[0].text;
            document.getElementById('discrete-text').textContent = currentSuggestion;
        }
    }
}

// Display advanced suggestions (Meeting Assistant Mode)
function displayAdvancedSuggestions(data) {
    const container = document.getElementById('suggestions-container');

    if (!data.suggestions || data.suggestions.length === 0) {
        container.innerHTML = '<p style="color: #718096; font-size: 0.9rem;">No suggestions yet...</p>';
        return;
    }

    // Categorize suggestions
    const categorized = categorizeSuggestions(data.suggestions);

    container.innerHTML = '';

    Object.entries(categorized).forEach(([type, suggestions]) => {
        suggestions.forEach((sug, index) => {
            const card = document.createElement('div');
            card.className = `suggestion-card priority-${index === 0 ? 'high' : 'normal'}`;

            card.innerHTML = `
                <div class="suggestion-card-header">
                    <span class="suggestion-type ${type}">${type}</span>
                    <span style="font-size: 0.75rem; color: #718096;">
                        ${(sug.confidence * 100).toFixed(0)}% confidence
                    </span>
                </div>
                <div class="suggestion-text">${sug.text}</div>
                <div class="suggestion-actions">
                    <button class="btn-small btn-use" onclick='useSuggestion(\`${sug.text}\`)'>
                        Use Response
                    </button>
                    <button class="btn-small btn-copy" onclick='copySuggestion(\`${sug.text}\`)'>
                        Copy
                    </button>
                </div>
            `;

            container.appendChild(card);
        });
    });
}

// Categorize suggestions based on content
function categorizeSuggestions(suggestions) {
    const categories = {
        sales: [],
        objection: [],
        negotiation: [],
        general: []
    };

    suggestions.forEach(sug => {
        const text = sug.text.toLowerCase();

        // Simple categorization (in production, use NLP/LLM)
        if (text.includes('value') || text.includes('roi') || text.includes('benefit')) {
            categories.sales.push(sug);
        } else if (text.includes('understand') || text.includes('concern')) {
            categories.objection.push(sug);
        } else if (text.includes('what if') || text.includes('alternative')) {
            categories.negotiation.push(sug);
        } else {
            categories.general.push(sug);
        }
    });

    // Remove empty categories
    return Object.fromEntries(
        Object.entries(categories).filter(([_, arr]) => arr.length > 0)
    );
}

// Sentiment analysis (simulated - in production, use API)
function analyzeSentiment(text) {
    // Simple sentiment analysis (replace with real API call)
    const positive = ['good', 'great', 'excellent', 'happy', 'love', 'yes'];
    const negative = ['bad', 'poor', 'terrible', 'unhappy', 'hate', 'no'];

    let score = 0.5; // Neutral
    const lowerText = text.toLowerCase();

    positive.forEach(word => {
        if (lowerText.includes(word)) score += 0.1;
    });

    negative.forEach(word => {
        if (lowerText.includes(word)) score -= 0.1;
    });

    score = Math.max(0, Math.min(1, score));

    // Update UI
    let emoji, sentiment, color;
    if (score > 0.6) {
        emoji = '😊';
        sentiment = 'Positive';
        color = '#48bb78';
    } else if (score < 0.4) {
        emoji = '😟';
        sentiment = 'Concerned';
        color = '#f56565';
    } else {
        emoji = '😐';
        sentiment = 'Neutral';
        color = '#718096';
    }

    document.getElementById('sentiment-emoji').textContent = emoji;
    document.getElementById('sentiment-text').textContent = sentiment;
    document.getElementById('sentiment-text').style.color = color;
    document.getElementById('sentiment-confidence').textContent =
        `Confidence: ${(score * 100).toFixed(0)}%`;
}

// Update meeting stats
function updateMeetingStats() {
    // Duration
    if (meetingStartTime) {
        const duration = Math.floor((Date.now() - meetingStartTime) / 1000);
        const minutes = Math.floor(duration / 60);
        const seconds = duration % 60;
        document.getElementById('meeting-duration').textContent =
            `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
    }

    // Messages
    document.getElementById('messages-count').textContent = messagesCount;

    // Speakers
    const speakers = new Set(
        Array.from(document.querySelectorAll('.speaker-info'))
            .map(el => el.textContent.trim())
    );
    document.getElementById('speakers-count').textContent = speakers.size;
}

// Start recording (enhanced)
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
        const processor = audioContext.createScriptProcessor(2048, 1, 1);

        source.connect(processor);
        processor.connect(audioContext.destination);

        processor.onaudioprocess = (e) => {
            if (!isRecording) return;

            const inputData = e.inputBuffer.getChannelData(0);
            const outputData = new Int16Array(inputData.length);

            for (let i = 0; i < inputData.length; i++) {
                const s = Math.max(-1, Math.min(1, inputData[i]));
                outputData[i] = (s < 0 ? s * 0x8000 : s * 0x7FFF) | 0;
            }

            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(outputData.buffer);
            }
        };

        isRecording = true;
        meetingStartTime = Date.now();

        // Update UI
        document.getElementById('start-btn').style.display = 'none';
        document.getElementById('stop-btn').style.display = 'inline-block';
        document.getElementById('status-indicator').className = 'status-indicator recording';
        document.getElementById('status-text').textContent = 'Recording...';

        showNotification('Recording started', 'success');

        // Start stats update interval
        setInterval(updateMeetingStats, 1000);

    } catch (error) {
        console.error('Error starting recording:', error);
        showNotification('Error accessing microphone', 'error');
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

    document.body.appendChild(notification);

    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease-in';
        setTimeout(() => notification.remove(), 300);
    }, duration);
}

// Copy suggestion
function copySuggestion(text) {
    navigator.clipboard.writeText(text).then(() => {
        showNotification('Copied to clipboard!', 'success', 1500);
    });
}

// Initialize on load
document.addEventListener('DOMContentLoaded', () => {
    // Load app_optimized.js functions (config, WebSocket, etc.)
    // They will be available here

    // Override message handler to include premium features
    const originalHandler = window.handleWebSocketMessage || function() {};
    window.handleWebSocketMessage = function(data) {
        originalHandler(data);
        handleWebSocketMessagePremium(data);
    };

    console.log('Salvavidas Premium initialized');
    showNotification('Welcome to Salvavidas Premium!', 'success');
});
