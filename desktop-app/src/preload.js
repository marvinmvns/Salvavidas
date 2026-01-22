/**
 * Preload script - Secure bridge between Electron and web content
 */

const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods that allow the renderer process to use
// ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld('electronAPI', {
    // Config
    getConfig: () => ipcRenderer.invoke('get-config'),
    setConfig: (key, value) => ipcRenderer.invoke('set-config', key, value),

    // Settings
    getSettings: () => ipcRenderer.invoke('get-settings'),
    saveSettings: (settings) => ipcRenderer.invoke('save-settings', settings),
    clearCache: () => ipcRenderer.invoke('clear-cache'),
    clearSpeakers: () => ipcRenderer.invoke('clear-speakers'),

    // Controls
    toggleOverlay: () => ipcRenderer.invoke('toggle-overlay'),
    toggleInvisible: () => ipcRenderer.invoke('toggle-invisible'),
    openSettings: () => ipcRenderer.invoke('open-settings-window'),

    // Window controls (for frameless window)
    minimizeWindow: () => ipcRenderer.invoke('window-minimize'),
    closeWindow: () => ipcRenderer.invoke('window-close'),

    // Events
    onOpenSettings: (callback) => ipcRenderer.on('open-settings', callback),
    on: (channel, callback) => {
        // Whitelist of allowed channels
        const validChannels = ['teams-meeting-started', 'teams-meeting-ended'];
        if (validChannels.includes(channel)) {
            ipcRenderer.on(channel, callback);
        }
    },

    // Platform info
    platform: process.platform,
    versions: process.versions
});
