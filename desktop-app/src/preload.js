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

    // Controls
    toggleOverlay: () => ipcRenderer.invoke('toggle-overlay'),
    toggleInvisible: () => ipcRenderer.invoke('toggle-invisible'),

    // Events
    onOpenSettings: (callback) => ipcRenderer.on('open-settings', callback),

    // Platform info
    platform: process.platform,
    versions: process.versions
});
