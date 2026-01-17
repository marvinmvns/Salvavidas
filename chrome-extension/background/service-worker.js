/**
 * Salvavidas - Background Service Worker
 * Manages extension lifecycle and communication
 */

// Extension state
const extensionState = {
  isActive: false,
  backendUrl: 'ws://localhost:8000/ws',
  settings: {
    autoStart: false,
    language: 'en',
    mode: 'meeting_assistant', // 'translator' or 'meeting_assistant'
    processingMode: 'local' // 'local', 'fast', 'premium'
  }
};

// Initialize extension on install
chrome.runtime.onInstalled.addListener(async (details) => {
  console.log('[Salvavidas] Extension installed:', details.reason);

  if (details.reason === 'install') {
    // Set default settings
    await chrome.storage.sync.set({
      backendUrl: extensionState.backendUrl,
      settings: extensionState.settings
    });

    // Open welcome page
    chrome.tabs.create({
      url: 'https://github.com/marvinmvns/Salvavidas#readme'
    });
  }

  // Load settings
  await loadSettings();
});

// Load settings from storage
async function loadSettings() {
  try {
    const data = await chrome.storage.sync.get(['backendUrl', 'settings']);

    if (data.backendUrl) {
      extensionState.backendUrl = data.backendUrl;
    }

    if (data.settings) {
      extensionState.settings = { ...extensionState.settings, ...data.settings };
    }

    console.log('[Salvavidas] Settings loaded:', extensionState);
  } catch (error) {
    console.error('[Salvavidas] Failed to load settings:', error);
  }
}

// Save settings to storage
async function saveSettings() {
  try {
    await chrome.storage.sync.set({
      backendUrl: extensionState.backendUrl,
      settings: extensionState.settings
    });

    console.log('[Salvavidas] Settings saved');
  } catch (error) {
    console.error('[Salvavidas] Failed to save settings:', error);
  }
}

// Handle messages from content scripts and popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  console.log('[Salvavidas] Message received:', request);

  switch (request.action) {
    case 'getSettings':
      sendResponse({
        success: true,
        backendUrl: extensionState.backendUrl,
        settings: extensionState.settings,
        isActive: extensionState.isActive
      });
      break;

    case 'updateSettings':
      if (request.backendUrl) {
        extensionState.backendUrl = request.backendUrl;
      }
      if (request.settings) {
        extensionState.settings = { ...extensionState.settings, ...request.settings };
      }
      saveSettings();
      sendResponse({ success: true });
      break;

    case 'toggleActive':
      extensionState.isActive = !extensionState.isActive;
      updateIcon();
      sendResponse({ success: true, isActive: extensionState.isActive });
      break;

    case 'setActive':
      extensionState.isActive = request.isActive;
      updateIcon();
      sendResponse({ success: true, isActive: extensionState.isActive });
      break;

    case 'checkBackendStatus':
      checkBackendConnection().then(status => {
        sendResponse({ success: true, status });
      });
      return true; // Keep channel open for async response

    default:
      sendResponse({ success: false, error: 'Unknown action' });
  }

  return true;
});

// Update extension icon based on state
function updateIcon() {
  const iconPath = extensionState.isActive ? 'icons/icon48.png' : 'icons/icon48-gray.png';

  chrome.action.setIcon({
    path: {
      16: iconPath.replace('48', '16'),
      48: iconPath,
      128: iconPath.replace('48', '128')
    }
  });
}

// Check backend connection status
async function checkBackendConnection() {
  try {
    const httpUrl = extensionState.backendUrl.replace('ws://', 'http://').replace('wss://', 'https://');
    const baseUrl = httpUrl.split('/ws')[0];

    const response = await fetch(`${baseUrl}/health`, {
      method: 'GET',
      timeout: 5000
    });

    if (response.ok) {
      return { connected: true, message: 'Backend is reachable' };
    } else {
      return { connected: false, message: `Backend returned ${response.status}` };
    }
  } catch (error) {
    return {
      connected: false,
      message: `Connection failed: ${error.message}`
    };
  }
}

// Handle tab updates (detect meeting URLs)
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.status === 'complete' && tab.url) {
    // Check if this is a meeting URL
    const meetingUrls = [
      'meet.google.com',
      'zoom.us',
      'teams.microsoft.com'
    ];

    const isMeetingUrl = meetingUrls.some(domain => tab.url.includes(domain));

    if (isMeetingUrl && extensionState.settings.autoStart) {
      // Notify content script to auto-start
      chrome.tabs.sendMessage(tabId, {
        action: 'autoStart',
        settings: extensionState.settings
      }).catch(err => {
        console.log('[Salvavidas] Could not send autoStart message:', err);
      });
    }
  }
});

// Handle keyboard shortcuts
chrome.commands.onCommand.addListener((command) => {
  console.log('[Salvavidas] Command received:', command);

  switch (command) {
    case 'toggle-recording':
      chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
        if (tabs[0]) {
          chrome.tabs.sendMessage(tabs[0].id, { action: 'toggle' });
        }
      });
      break;

    case 'toggle-overlay':
      chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
        if (tabs[0]) {
          chrome.tabs.sendMessage(tabs[0].id, { action: 'toggleOverlay' });
        }
      });
      break;
  }
});

// Periodic backend health check
setInterval(async () => {
  if (extensionState.isActive) {
    const status = await checkBackendConnection();
    if (!status.connected) {
      console.warn('[Salvavidas] Backend unreachable:', status.message);
    }
  }
}, 30000); // Check every 30 seconds

// Context menu integration
chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: 'salvavidas-open-settings',
    title: 'Salvavidas Settings',
    contexts: ['action']
  });

  chrome.contextMenus.create({
    id: 'salvavidas-check-status',
    title: 'Check Backend Status',
    contexts: ['action']
  });
});

chrome.contextMenus.onClicked.addListener((info, tab) => {
  switch (info.menuItemId) {
    case 'salvavidas-open-settings':
      chrome.runtime.openOptionsPage();
      break;

    case 'salvavidas-check-status':
      checkBackendConnection().then(status => {
        const message = status.connected
          ? 'Backend is connected and ready!'
          : `Backend is not reachable: ${status.message}`;

        chrome.notifications.create({
          type: 'basic',
          iconUrl: 'icons/icon48.png',
          title: 'Salvavidas Backend Status',
          message: message
        });
      });
      break;
  }
});

// Handle alarm events (for scheduled tasks)
chrome.alarms.onAlarm.addListener((alarm) => {
  console.log('[Salvavidas] Alarm triggered:', alarm.name);

  switch (alarm.name) {
    case 'healthCheck':
      checkBackendConnection();
      break;
  }
});

// Create health check alarm
chrome.alarms.create('healthCheck', {
  periodInMinutes: 1
});

console.log('[Salvavidas] Background service worker initialized');
