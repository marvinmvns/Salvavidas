/**
 * Salvavidas - Content Script
 * Injects overlay into Google Meet, Zoom, and Microsoft Teams
 */

// Configuration
const BACKEND_WS_URL = 'ws://localhost:8000/ws';
const OVERLAY_ID = 'salvavidas-overlay';

// State
let ws = null;
let isRecording = false;
let mediaRecorder = null;
let audioContext = null;
let audioStream = null;

/**
 * Initialize the extension when page loads
 */
async function initialize() {
  console.log('[Salvavidas] Initializing...');

  // Inject overlay UI
  injectOverlay();

  // Setup WebSocket connection
  await connectWebSocket();

  // Setup audio capture
  setupAudioCapture();

  // Listen for messages from popup/background
  chrome.runtime.onMessage.addListener(handleMessage);

  console.log('[Salvavidas] Initialized successfully');
}

/**
 * Inject the overlay UI into the page
 */
function injectOverlay() {
  // Check if already injected
  if (document.getElementById(OVERLAY_ID)) {
    console.log('[Salvavidas] Overlay already exists');
    return;
  }

  const overlay = document.createElement('div');
  overlay.id = OVERLAY_ID;
  overlay.innerHTML = `
    <div class="salvavidas-container">
      <div class="salvavidas-header">
        <img src="${chrome.runtime.getURL('icons/icon48.png')}" alt="Salvavidas" />
        <h3>Salvavidas AI Assistant</h3>
        <div class="salvavidas-controls">
          <button id="salvavidas-toggle" class="salvavidas-btn" title="Toggle Recording">
            <span class="status-indicator"></span>
          </button>
          <button id="salvavidas-minimize" class="salvavidas-btn" title="Minimize">−</button>
        </div>
      </div>

      <div class="salvavidas-content">
        <!-- Transcription Display -->
        <div class="salvavidas-section">
          <h4>Live Transcription</h4>
          <div id="salvavidas-transcription" class="transcription-box">
            Waiting for audio...
          </div>
        </div>

        <!-- Sentiment Display -->
        <div class="salvavidas-section">
          <h4>Sentiment Analysis</h4>
          <div id="salvavidas-sentiment" class="sentiment-display">
            <span class="sentiment-emoji">😐</span>
            <span class="sentiment-text">Neutral</span>
            <span class="sentiment-confidence">—</span>
          </div>
        </div>

        <!-- Suggestions Display -->
        <div class="salvavidas-section">
          <h4>Suggested Responses</h4>
          <div id="salvavidas-suggestions" class="suggestions-container">
            <div class="suggestion-placeholder">
              Start the meeting to see suggestions...
            </div>
          </div>
        </div>

        <!-- Meeting Stats -->
        <div class="salvavidas-section">
          <h4>Meeting Stats</h4>
          <div id="salvavidas-stats" class="stats-display">
            <div class="stat-item">
              <span class="stat-label">Duration:</span>
              <span id="stat-duration">00:00</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">Speakers:</span>
              <span id="stat-speakers">0</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">Sentiment:</span>
              <span id="stat-overall-sentiment">—</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  `;

  document.body.appendChild(overlay);

  // Make overlay draggable
  makeDraggable();

  // Setup event listeners
  document.getElementById('salvavidas-toggle').addEventListener('click', toggleRecording);
  document.getElementById('salvavidas-minimize').addEventListener('click', toggleMinimize);

  console.log('[Salvavidas] Overlay injected');
}

/**
 * Make overlay draggable
 */
function makeDraggable() {
  const overlay = document.getElementById(OVERLAY_ID);
  const header = overlay.querySelector('.salvavidas-header');

  let isDragging = false;
  let currentX;
  let currentY;
  let initialX;
  let initialY;
  let xOffset = 0;
  let yOffset = 0;

  header.addEventListener('mousedown', dragStart);
  document.addEventListener('mousemove', drag);
  document.addEventListener('mouseup', dragEnd);

  function dragStart(e) {
    if (e.target.closest('.salvavidas-controls')) return;

    initialX = e.clientX - xOffset;
    initialY = e.clientY - yOffset;
    isDragging = true;
  }

  function drag(e) {
    if (isDragging) {
      e.preventDefault();
      currentX = e.clientX - initialX;
      currentY = e.clientY - initialY;
      xOffset = currentX;
      yOffset = currentY;

      setTranslate(currentX, currentY, overlay);
    }
  }

  function dragEnd(e) {
    initialX = currentX;
    initialY = currentY;
    isDragging = false;
  }

  function setTranslate(xPos, yPos, el) {
    el.style.transform = `translate(${xPos}px, ${yPos}px)`;
  }
}

/**
 * Toggle minimize state
 */
function toggleMinimize() {
  const overlay = document.getElementById(OVERLAY_ID);
  overlay.classList.toggle('minimized');
}

/**
 * Connect to backend WebSocket
 */
async function connectWebSocket() {
  try {
    // Get backend URL from storage
    const settings = await chrome.storage.sync.get(['backendUrl']);
    const wsUrl = settings.backendUrl || BACKEND_WS_URL;

    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log('[Salvavidas] WebSocket connected');
      updateConnectionStatus(true);
    };

    ws.onmessage = (event) => {
      handleWebSocketMessage(JSON.parse(event.data));
    };

    ws.onerror = (error) => {
      console.error('[Salvavidas] WebSocket error:', error);
      updateConnectionStatus(false);
    };

    ws.onclose = () => {
      console.log('[Salvavidas] WebSocket disconnected');
      updateConnectionStatus(false);
      // Attempt reconnection after 5 seconds
      setTimeout(connectWebSocket, 5000);
    };

  } catch (error) {
    console.error('[Salvavidas] Failed to connect WebSocket:', error);
  }
}

/**
 * Handle WebSocket messages from backend
 */
function handleWebSocketMessage(data) {
  console.log('[Salvavidas] Received:', data);

  switch (data.type) {
    case 'transcription':
      updateTranscription(data.data);
      break;
    case 'translation':
      updateTranslation(data.data);
      break;
    case 'sentiment':
      updateSentiment(data.data);
      break;
    case 'suggestions':
      updateSuggestions(data.data);
      break;
    case 'speaker':
      updateSpeaker(data.data);
      break;
    case 'stats':
      updateStats(data.data);
      break;
    default:
      console.warn('[Salvavidas] Unknown message type:', data.type);
  }
}

/**
 * Update transcription display
 */
function updateTranscription(data) {
  const transcriptionBox = document.getElementById('salvavidas-transcription');
  const entry = document.createElement('div');
  entry.className = 'transcription-entry';
  entry.innerHTML = `
    <div class="transcription-meta">
      <span class="speaker">${data.speaker || 'Unknown'}</span>
      <span class="timestamp">${new Date().toLocaleTimeString()}</span>
    </div>
    <div class="transcription-text">${data.text}</div>
    ${data.translation ? `<div class="translation-text">→ ${data.translation}</div>` : ''}
  `;

  transcriptionBox.appendChild(entry);
  transcriptionBox.scrollTop = transcriptionBox.scrollHeight;
}

/**
 * Update sentiment display
 */
function updateSentiment(data) {
  const sentimentEmojis = {
    'very_positive': '😄',
    'positive': '🙂',
    'neutral': '😐',
    'negative': '😕',
    'very_negative': '😢',
    'confused': '😕',
    'concerned': '😰',
    'excited': '🤩'
  };

  const emoji = document.querySelector('.sentiment-emoji');
  const text = document.querySelector('.sentiment-text');
  const confidence = document.querySelector('.sentiment-confidence');

  emoji.textContent = sentimentEmojis[data.sentiment] || '😐';
  text.textContent = data.sentiment.replace('_', ' ').toUpperCase();
  confidence.textContent = `${Math.round(data.confidence * 100)}%`;

  // Update overall sentiment in stats
  document.getElementById('stat-overall-sentiment').textContent =
    sentimentEmojis[data.sentiment] || '😐';
}

/**
 * Update suggestions display
 */
function updateSuggestions(suggestions) {
  const container = document.getElementById('salvavidas-suggestions');
  container.innerHTML = '';

  if (!suggestions || suggestions.length === 0) {
    container.innerHTML = '<div class="suggestion-placeholder">No suggestions available</div>';
    return;
  }

  suggestions.forEach((suggestion, index) => {
    const card = document.createElement('div');
    card.className = `suggestion-card priority-${suggestion.priority}`;
    card.innerHTML = `
      <div class="suggestion-header">
        <span class="suggestion-type">${suggestion.type.replace('_', ' ')}</span>
        <span class="suggestion-confidence">${Math.round(suggestion.confidence * 100)}%</span>
      </div>
      <div class="suggestion-text">${suggestion.text}</div>
      <div class="suggestion-footer">
        <button class="copy-btn" data-text="${suggestion.text}">Copy</button>
        <span class="suggestion-outcome">${suggestion.expected_outcome}</span>
      </div>
    `;

    container.appendChild(card);

    // Add copy functionality
    card.querySelector('.copy-btn').addEventListener('click', (e) => {
      navigator.clipboard.writeText(e.target.dataset.text);
      e.target.textContent = '✓ Copied';
      setTimeout(() => e.target.textContent = 'Copy', 2000);
    });
  });
}

/**
 * Update speaker count
 */
function updateSpeaker(data) {
  const speakersEl = document.getElementById('stat-speakers');
  const currentCount = parseInt(speakersEl.textContent) || 0;
  speakersEl.textContent = Math.max(currentCount, data.speaker_count || currentCount + 1);
}

/**
 * Update meeting stats
 */
function updateStats(data) {
  if (data.duration) {
    document.getElementById('stat-duration').textContent = formatDuration(data.duration);
  }
  if (data.speaker_count) {
    document.getElementById('stat-speakers').textContent = data.speaker_count;
  }
}

/**
 * Format duration in seconds to MM:SS
 */
function formatDuration(seconds) {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
}

/**
 * Update connection status indicator
 */
function updateConnectionStatus(connected) {
  const indicator = document.querySelector('.status-indicator');
  if (indicator) {
    indicator.className = connected ? 'status-indicator connected' : 'status-indicator disconnected';
  }
}

/**
 * Setup audio capture from tab
 */
async function setupAudioCapture() {
  try {
    // Request tab audio capture permission
    audioStream = await navigator.mediaDevices.getUserMedia({
      audio: {
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true
      }
    });

    audioContext = new AudioContext({ sampleRate: 16000 });
    console.log('[Salvavidas] Audio capture ready');

  } catch (error) {
    console.error('[Salvavidas] Audio capture setup failed:', error);
  }
}

/**
 * Toggle recording on/off
 */
async function toggleRecording() {
  if (isRecording) {
    stopRecording();
  } else {
    await startRecording();
  }
}

/**
 * Start recording and streaming audio
 */
async function startRecording() {
  if (!audioStream) {
    console.error('[Salvavidas] No audio stream available');
    return;
  }

  if (!ws || ws.readyState !== WebSocket.OPEN) {
    console.error('[Salvavidas] WebSocket not connected');
    alert('Cannot start - not connected to backend');
    return;
  }

  try {
    // Create MediaRecorder with appropriate MIME type
    const mimeType = 'audio/webm;codecs=opus';
    mediaRecorder = new MediaRecorder(audioStream, {
      mimeType: mimeType,
      audioBitsPerSecond: 16000
    });

    mediaRecorder.ondataavailable = async (event) => {
      if (event.data.size > 0 && ws.readyState === WebSocket.OPEN) {
        // Convert blob to base64 and send
        const reader = new FileReader();
        reader.onloadend = () => {
          const base64Audio = reader.result.split(',')[1];
          ws.send(JSON.stringify({
            type: 'audio',
            data: base64Audio,
            format: 'webm'
          }));
        };
        reader.readAsDataURL(event.data);
      }
    };

    // Send audio chunks every 1 second
    mediaRecorder.start(1000);
    isRecording = true;

    // Update UI
    const toggleBtn = document.getElementById('salvavidas-toggle');
    toggleBtn.classList.add('recording');
    toggleBtn.title = 'Stop Recording';

    console.log('[Salvavidas] Recording started');

  } catch (error) {
    console.error('[Salvavidas] Failed to start recording:', error);
  }
}

/**
 * Stop recording
 */
function stopRecording() {
  if (mediaRecorder && mediaRecorder.state !== 'inactive') {
    mediaRecorder.stop();
  }

  isRecording = false;

  // Update UI
  const toggleBtn = document.getElementById('salvavidas-toggle');
  toggleBtn.classList.remove('recording');
  toggleBtn.title = 'Start Recording';

  console.log('[Salvavidas] Recording stopped');
}

/**
 * Handle messages from popup/background
 */
function handleMessage(request, sender, sendResponse) {
  console.log('[Salvavidas] Message received:', request);

  switch (request.action) {
    case 'start':
      startRecording();
      sendResponse({ success: true });
      break;
    case 'stop':
      stopRecording();
      sendResponse({ success: true });
      break;
    case 'toggle':
      toggleRecording();
      sendResponse({ success: true });
      break;
    case 'getStatus':
      sendResponse({
        recording: isRecording,
        connected: ws && ws.readyState === WebSocket.OPEN
      });
      break;
    default:
      sendResponse({ success: false, error: 'Unknown action' });
  }

  return true; // Keep message channel open for async response
}

/**
 * Cleanup on page unload
 */
window.addEventListener('beforeunload', () => {
  if (isRecording) {
    stopRecording();
  }
  if (ws) {
    ws.close();
  }
  if (audioStream) {
    audioStream.getTracks().forEach(track => track.stop());
  }
});

// Initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initialize);
} else {
  initialize();
}
