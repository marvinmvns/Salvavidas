/**
 * Salvavidas - Popup Script
 * Handles extension popup UI and settings
 */

// DOM Elements
let backendUrlInput;
let modeSelect;
let processingModeSelect;
let languageSelect;
let autoStartCheckbox;
let btnSave;
let btnTest;
let btnStart;
let btnStop;
let notification;
let backendStatusIndicator;
let backendStatusText;
let recordingStatus;

// State
let currentSettings = {
  backendUrl: 'ws://localhost:8000/ws',
  settings: {
    autoStart: false,
    language: 'en',
    mode: 'meeting_assistant',
    processingMode: 'local'
  }
};

/**
 * Initialize popup when DOM is ready
 */
document.addEventListener('DOMContentLoaded', async () => {
  console.log('[Salvavidas Popup] Initializing...');

  // Get DOM elements
  backendUrlInput = document.getElementById('backend-url');
  modeSelect = document.getElementById('mode');
  processingModeSelect = document.getElementById('processing-mode');
  languageSelect = document.getElementById('language');
  autoStartCheckbox = document.getElementById('auto-start');
  btnSave = document.getElementById('btn-save');
  btnTest = document.getElementById('btn-test');
  btnStart = document.getElementById('btn-start');
  btnStop = document.getElementById('btn-stop');
  notification = document.getElementById('notification');
  backendStatusIndicator = document.getElementById('backend-status-indicator');
  backendStatusText = document.getElementById('backend-status-text');
  recordingStatus = document.getElementById('recording-status');

  // Setup event listeners
  btnSave.addEventListener('click', saveSettings);
  btnTest.addEventListener('click', testConnection);
  btnStart.addEventListener('click', startAssistant);
  btnStop.addEventListener('click', stopAssistant);

  // Load current settings
  await loadSettings();

  // Check backend status
  await checkBackendStatus();

  // Check if currently active tab is a meeting
  await checkCurrentTab();

  console.log('[Salvavidas Popup] Initialized');
});

/**
 * Load settings from storage
 */
async function loadSettings() {
  try {
    const response = await chrome.runtime.sendMessage({ action: 'getSettings' });

    if (response.success) {
      currentSettings.backendUrl = response.backendUrl;
      currentSettings.settings = response.settings;

      // Update UI
      backendUrlInput.value = currentSettings.backendUrl;
      modeSelect.value = currentSettings.settings.mode;
      processingModeSelect.value = currentSettings.settings.processingMode;
      languageSelect.value = currentSettings.settings.language;
      autoStartCheckbox.checked = currentSettings.settings.autoStart;

      console.log('[Salvavidas Popup] Settings loaded:', currentSettings);
    }
  } catch (error) {
    console.error('[Salvavidas Popup] Failed to load settings:', error);
    showNotification('Failed to load settings', 'error');
  }
}

/**
 * Save settings to storage
 */
async function saveSettings() {
  try {
    // Get values from UI
    const backendUrl = backendUrlInput.value.trim();
    const settings = {
      mode: modeSelect.value,
      processingMode: processingModeSelect.value,
      language: languageSelect.value,
      autoStart: autoStartCheckbox.checked
    };

    // Validate backend URL
    if (!backendUrl.startsWith('ws://') && !backendUrl.startsWith('wss://')) {
      showNotification('Backend URL must start with ws:// or wss://', 'error');
      return;
    }

    // Save to background
    const response = await chrome.runtime.sendMessage({
      action: 'updateSettings',
      backendUrl: backendUrl,
      settings: settings
    });

    if (response.success) {
      currentSettings.backendUrl = backendUrl;
      currentSettings.settings = settings;
      showNotification('Settings saved successfully!', 'success');
    } else {
      showNotification('Failed to save settings', 'error');
    }
  } catch (error) {
    console.error('[Salvavidas Popup] Failed to save settings:', error);
    showNotification('Failed to save settings', 'error');
  }
}

/**
 * Test backend connection
 */
async function testConnection() {
  btnTest.disabled = true;
  btnTest.textContent = 'Testing...';

  try {
    const response = await chrome.runtime.sendMessage({ action: 'checkBackendStatus' });

    if (response.success && response.status.connected) {
      backendStatusIndicator.className = 'status-indicator connected';
      backendStatusText.textContent = 'Connected';
      showNotification('Backend is connected and ready!', 'success');
    } else {
      backendStatusIndicator.className = 'status-indicator disconnected';
      backendStatusText.textContent = 'Disconnected';
      showNotification(`Backend is unreachable: ${response.status.message}`, 'error');
    }
  } catch (error) {
    console.error('[Salvavidas Popup] Connection test failed:', error);
    backendStatusIndicator.className = 'status-indicator disconnected';
    backendStatusText.textContent = 'Disconnected';
    showNotification('Connection test failed', 'error');
  }

  btnTest.disabled = false;
  btnTest.textContent = 'Test Connection';
}

/**
 * Check backend status
 */
async function checkBackendStatus() {
  try {
    const response = await chrome.runtime.sendMessage({ action: 'checkBackendStatus' });

    if (response.success && response.status.connected) {
      backendStatusIndicator.className = 'status-indicator connected';
      backendStatusText.textContent = 'Connected';
    } else {
      backendStatusIndicator.className = 'status-indicator disconnected';
      backendStatusText.textContent = 'Disconnected';
    }
  } catch (error) {
    console.error('[Salvavidas Popup] Status check failed:', error);
    backendStatusIndicator.className = 'status-indicator disconnected';
    backendStatusText.textContent = 'Error';
  }
}

/**
 * Check current tab for meeting URL
 */
async function checkCurrentTab() {
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

    if (tab && tab.url) {
      const meetingUrls = ['meet.google.com', 'zoom.us', 'teams.microsoft.com'];
      const isMeetingUrl = meetingUrls.some(domain => tab.url.includes(domain));

      if (isMeetingUrl) {
        // Check if assistant is already active
        try {
          const response = await chrome.tabs.sendMessage(tab.id, { action: 'getStatus' });

          if (response && response.recording) {
            recordingStatus.textContent = 'Recording';
            recordingStatus.style.color = '#10b981';
            btnStart.disabled = true;
            btnStop.disabled = false;
          }
        } catch (error) {
          // Content script not loaded yet
          console.log('[Salvavidas Popup] Content script not ready yet');
        }
      } else {
        showNotification('Open a Google Meet, Zoom, or Teams meeting to use this extension', 'error');
        btnStart.disabled = true;
      }
    }
  } catch (error) {
    console.error('[Salvavidas Popup] Failed to check current tab:', error);
  }
}

/**
 * Start the assistant
 */
async function startAssistant() {
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

    if (!tab) {
      showNotification('No active tab found', 'error');
      return;
    }

    // Send start message to content script
    const response = await chrome.tabs.sendMessage(tab.id, { action: 'start' });

    if (response && response.success) {
      recordingStatus.textContent = 'Recording';
      recordingStatus.style.color = '#10b981';
      btnStart.disabled = true;
      btnStop.disabled = false;
      showNotification('Assistant started!', 'success');

      // Update background state
      await chrome.runtime.sendMessage({ action: 'setActive', isActive: true });
    } else {
      showNotification('Failed to start assistant', 'error');
    }
  } catch (error) {
    console.error('[Salvavidas Popup] Failed to start assistant:', error);
    showNotification('Failed to start assistant. Make sure you\'re on a meeting page.', 'error');
  }
}

/**
 * Stop the assistant
 */
async function stopAssistant() {
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

    if (!tab) {
      showNotification('No active tab found', 'error');
      return;
    }

    // Send stop message to content script
    const response = await chrome.tabs.sendMessage(tab.id, { action: 'stop' });

    if (response && response.success) {
      recordingStatus.textContent = 'Stopped';
      recordingStatus.style.color = '#6b7280';
      btnStart.disabled = false;
      btnStop.disabled = true;
      showNotification('Assistant stopped', 'success');

      // Update background state
      await chrome.runtime.sendMessage({ action: 'setActive', isActive: false });
    } else {
      showNotification('Failed to stop assistant', 'error');
    }
  } catch (error) {
    console.error('[Salvavidas Popup] Failed to stop assistant:', error);
    showNotification('Failed to stop assistant', 'error');
  }
}

/**
 * Show notification message
 */
function showNotification(message, type = 'success') {
  notification.textContent = message;
  notification.className = `notification ${type} show`;

  // Auto-hide after 3 seconds
  setTimeout(() => {
    notification.classList.remove('show');
  }, 3000);
}

// Listen for messages from background/content scripts
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  console.log('[Salvavidas Popup] Message received:', request);

  switch (request.action) {
    case 'recordingStarted':
      recordingStatus.textContent = 'Recording';
      recordingStatus.style.color = '#10b981';
      btnStart.disabled = true;
      btnStop.disabled = false;
      break;

    case 'recordingStopped':
      recordingStatus.textContent = 'Stopped';
      recordingStatus.style.color = '#6b7280';
      btnStart.disabled = false;
      btnStop.disabled = true;
      break;

    case 'backendStatusChanged':
      if (request.connected) {
        backendStatusIndicator.className = 'status-indicator connected';
        backendStatusText.textContent = 'Connected';
      } else {
        backendStatusIndicator.className = 'status-indicator disconnected';
        backendStatusText.textContent = 'Disconnected';
      }
      break;
  }

  return true;
});
