/**
 * Salvavidas Desktop - Main Process
 * Cross-platform desktop app with invisible mode for screen sharing
 */

const { app, BrowserWindow, globalShortcut, ipcMain, Menu, Tray, screen, Notification } = require('electron');
const path = require('path');
const Store = require('electron-store');
const TeamsDetector = require('./teams-detector');

const store = new Store();

let mainWindow = null;
let overlayWindow = null;
let settingsWindow = null;
let tray = null;
let isInvisibleMode = false;
let teamsDetector = null;

// Auto-start overlay on Teams meetings (configurable)
let autoStartOverlay = store.get('autoStartOverlay', true);

// Disable hardware acceleration for better compatibility
app.disableHardwareAcceleration();

// Additional flags to prevent GPU crashes
app.commandLine.appendSwitch('disable-gpu');
app.commandLine.appendSwitch('disable-gpu-compositing');
app.commandLine.appendSwitch('disable-software-rasterizer');
app.commandLine.appendSwitch('ignore-gpu-blacklist');

/**
 * Create main window
 */
function createMainWindow() {
    const primaryDisplay = screen.getPrimaryDisplay();
    const { width, height } = primaryDisplay.workAreaSize;

    mainWindow = new BrowserWindow({
        width: 1200,
        height: 800,
        minWidth: 800,
        minHeight: 600,
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
            preload: path.join(__dirname, 'preload.js')
        },
        icon: path.join(__dirname, '../build/icon.png'),
        title: 'Salvavidas - Voice Translation Assistant',
        backgroundColor: '#667eea',
        show: false, // Don't show until ready
    });

    // Load the app (can be local HTML or web server)
    const serverUrl = store.get('serverUrl', 'http://localhost:8000');
    mainWindow.loadURL(serverUrl);

    // Show when ready
    mainWindow.once('ready-to-show', () => {
        mainWindow.show();
    });

    // Handle close button
    mainWindow.on('close', (event) => {
        if (!app.isQuitting) {
            event.preventDefault();
            mainWindow.hide();
        }
    });

    mainWindow.on('closed', () => {
        mainWindow = null;
    });

    return mainWindow;
}

/**
 * Create invisible overlay window for discrete mode
 * This window will NOT appear when screen sharing
 */
function createOverlayWindow() {
    const primaryDisplay = screen.getPrimaryDisplay();
    const { width, height } = primaryDisplay.workAreaSize;

    overlayWindow = new BrowserWindow({
        width: 400,
        height: 600,
        x: width - 420, // Right side
        y: 100, // Top
        frame: false,
        transparent: true,
        alwaysOnTop: true,
        skipTaskbar: true,
        resizable: false,
        hasShadow: false,
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
            preload: path.join(__dirname, 'preload.js')
        },
        // CRITICAL: These make it invisible to screen capture
        type: 'panel', // On macOS, panel windows aren't captured
        vibrancy: 'ultra-dark', // macOS
        backgroundColor: '#00000000', // Transparent
    });

    // On Windows, use different approach
    if (process.platform === 'win32') {
        overlayWindow.setSkipTaskbar(true);
        overlayWindow.setAlwaysOnTop(true, 'screen-saver');
    }

    // Load overlay HTML
    overlayWindow.loadFile(path.join(__dirname, '../public/overlay.html'));

    overlayWindow.on('closed', () => {
        overlayWindow = null;
    });

    // Make draggable
    overlayWindow.setIgnoreMouseEvents(false);

    return overlayWindow;
}

/**
 * Create settings window
 */
function createSettingsWindow() {
    // Don't create multiple settings windows
    if (settingsWindow) {
        settingsWindow.show();
        settingsWindow.focus();
        return settingsWindow;
    }

    settingsWindow = new BrowserWindow({
        width: 900,
        height: 700,
        minWidth: 800,
        minHeight: 600,
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
            preload: path.join(__dirname, 'preload.js')
        },
        icon: path.join(__dirname, '../build/icon.png'),
        title: 'Configurações - Salvavidas',
        backgroundColor: '#1a202c',
        parent: mainWindow,
        modal: false,
        show: false,
        autoHideMenuBar: true
    });

    // Load settings HTML
    settingsWindow.loadFile(path.join(__dirname, '../public/settings.html'));

    // Show when ready
    settingsWindow.once('ready-to-show', () => {
        settingsWindow.show();
    });

    settingsWindow.on('closed', () => {
        settingsWindow = null;
    });

    return settingsWindow;
}

/**
 * Create system tray
 */
function createTray() {
    const iconPath = path.join(__dirname, '../build/tray-icon.png');

    tray = new Tray(iconPath);

    updateTrayMenu();

    tray.setToolTip('Salvavidas - Voice Translation');

    // Click to show main window
    tray.on('click', () => {
        if (mainWindow) {
            mainWindow.isVisible() ? mainWindow.hide() : mainWindow.show();
        }
    });
}

/**
 * Update tray menu (called to refresh Teams status)
 */
function updateTrayMenu() {
    if (!tray) return;

    const teamsStatus = teamsDetector ? teamsDetector.getStatus() : { isInMeeting: false };

    const contextMenu = Menu.buildFromTemplate([
        {
            label: 'Show Salvavidas',
            click: () => {
                if (mainWindow) {
                    mainWindow.show();
                }
            }
        },
        {
            label: 'Toggle Overlay (Ctrl+Shift+O)',
            click: toggleOverlay
        },
        {
            label: 'Invisible Mode',
            type: 'checkbox',
            checked: isInvisibleMode,
            click: toggleInvisibleMode
        },
        { type: 'separator' },
        {
            label: `Teams: ${teamsStatus.isInMeeting ? '🟢 In Meeting' : '⚪ Not Detected'}`,
            enabled: false
        },
        {
            label: 'Auto-start Overlay for Teams',
            type: 'checkbox',
            checked: autoStartOverlay,
            click: () => {
                autoStartOverlay = !autoStartOverlay;
                store.set('autoStartOverlay', autoStartOverlay);
                updateTrayMenu();
            }
        },
        { type: 'separator' },
        {
            label: 'Settings',
            click: () => {
                createSettingsWindow();
            }
        },
        { type: 'separator' },
        {
            label: 'Quit',
            click: () => {
                app.isQuitting = true;
                app.quit();
            }
        }
    ]);

    tray.setContextMenu(contextMenu);
}

/**
 * Toggle overlay window
 */
function toggleOverlay() {
    if (!overlayWindow) {
        createOverlayWindow();
    } else {
        if (overlayWindow.isVisible()) {
            overlayWindow.hide();
        } else {
            overlayWindow.show();
        }
    }
}

/**
 * Toggle invisible mode
 * In this mode, the app becomes completely invisible to screen capture
 */
function toggleInvisibleMode() {
    isInvisibleMode = !isInvisibleMode;

    if (isInvisibleMode) {
        // Hide main window, show overlay
        if (mainWindow && mainWindow.isVisible()) {
            mainWindow.hide();
        }
        if (!overlayWindow) {
            createOverlayWindow();
        } else {
            overlayWindow.show();
        }
    } else {
        // Show main window, hide overlay
        if (overlayWindow && overlayWindow.isVisible()) {
            overlayWindow.hide();
        }
        if (mainWindow) {
            mainWindow.show();
        }
    }

    // Update tray
    updateTrayMenu();
}

/**
 * Register global shortcuts
 */
function registerShortcuts() {
    // Ctrl+Shift+O: Toggle overlay
    globalShortcut.register('CommandOrControl+Shift+O', toggleOverlay);

    // Ctrl+Shift+I: Toggle invisible mode
    globalShortcut.register('CommandOrControl+Shift+I', toggleInvisibleMode);

    // Ctrl+Shift+S: Show/hide main window
    globalShortcut.register('CommandOrControl+Shift+S', () => {
        if (mainWindow) {
            mainWindow.isVisible() ? mainWindow.hide() : mainWindow.show();
        }
    });

    // Ctrl+Shift+H: Hide all
    globalShortcut.register('CommandOrControl+Shift+H', () => {
        if (mainWindow) mainWindow.hide();
        if (overlayWindow) overlayWindow.hide();
    });

    // Ctrl+,: Open settings
    globalShortcut.register('CommandOrControl+,', () => {
        createSettingsWindow();
    });
}

/**
 * Initialize Teams meeting detector
 */
function initializeTeamsDetector() {
    teamsDetector = new TeamsDetector();

    // Handle meeting started
    teamsDetector.on('meeting-started', (meetingInfo) => {
        console.log('[App] Teams meeting detected:', meetingInfo);

        // Update tray menu to show meeting status
        updateTrayMenu();

        // Send notification
        if (Notification.isSupported()) {
            new Notification({
                title: 'Teams Meeting Detected',
                body: 'Salvavidas is ready to assist!',
                silent: false
            }).show();
        }

        // Auto-start overlay if enabled
        if (autoStartOverlay && !overlayWindow) {
            console.log('[App] Auto-starting overlay for Teams meeting');
            createOverlayWindow();
        } else if (autoStartOverlay && overlayWindow && !overlayWindow.isVisible()) {
            overlayWindow.show();
        }

        // Send event to renderer processes
        if (mainWindow) {
            mainWindow.webContents.send('teams-meeting-started', meetingInfo);
        }
        if (overlayWindow) {
            overlayWindow.webContents.send('teams-meeting-started', meetingInfo);
        }
    });

    // Handle meeting ended
    teamsDetector.on('meeting-ended', (meetingInfo) => {
        console.log('[App] Teams meeting ended');

        // Update tray menu
        updateTrayMenu();

        // Send notification
        if (Notification.isSupported()) {
            new Notification({
                title: 'Teams Meeting Ended',
                body: 'Thanks for using Salvavidas!',
                silent: true
            }).show();
        }

        // Send event to renderer processes
        if (mainWindow) {
            mainWindow.webContents.send('teams-meeting-ended', meetingInfo);
        }
        if (overlayWindow) {
            overlayWindow.webContents.send('teams-meeting-ended', meetingInfo);
        }
    });

    // Start detecting
    teamsDetector.start();
}

/**
 * App ready
 */
app.whenReady().then(() => {
    createMainWindow();
    createTray();
    registerShortcuts();
    initializeTeamsDetector(); // Initialize Teams auto-detection

    // Create app menu
    const menu = Menu.buildFromTemplate([
        {
            label: 'Salvavidas',
            submenu: [
                { label: 'About', role: 'about' },
                { type: 'separator' },
                { label: 'Settings...', accelerator: 'CmdOrCtrl+,', click: () => createSettingsWindow() },
                { type: 'separator' },
                { label: 'Quit', accelerator: 'CmdOrCtrl+Q', click: () => app.quit() }
            ]
        },
        {
            label: 'View',
            submenu: [
                { label: 'Reload', accelerator: 'CmdOrCtrl+R', click: (item, focusedWindow) => focusedWindow?.reload() },
                { label: 'Toggle DevTools', accelerator: 'Alt+CmdOrCtrl+I', click: (item, focusedWindow) => focusedWindow?.toggleDevTools() },
                { type: 'separator' },
                { label: 'Toggle Overlay', accelerator: 'CmdOrCtrl+Shift+O', click: toggleOverlay },
                { label: 'Invisible Mode', accelerator: 'CmdOrCtrl+Shift+I', click: toggleInvisibleMode }
            ]
        }
    ]);
    Menu.setApplicationMenu(menu);

    app.on('activate', () => {
        if (BrowserWindow.getAllWindows().length === 0) {
            createMainWindow();
        }
    });
});

/**
 * Quit when all windows are closed (except macOS)
 */
app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

/**
 * Cleanup on quit
 */
app.on('will-quit', () => {
    globalShortcut.unregisterAll();

    // Stop Teams detector
    if (teamsDetector) {
        teamsDetector.stop();
    }
});

/**
 * IPC Handlers
 */
ipcMain.handle('get-config', () => {
    return store.store;
});

ipcMain.handle('set-config', (event, key, value) => {
    store.set(key, value);

    // Handle auto-start overlay setting
    if (key === 'autoStartOverlay') {
        autoStartOverlay = value;
    }

    return true;
});

ipcMain.handle('toggle-overlay', toggleOverlay);
ipcMain.handle('toggle-invisible', toggleInvisibleMode);

// Teams detection IPC handlers
ipcMain.handle('get-teams-status', async () => {
    if (teamsDetector) {
        return teamsDetector.getStatus();
    }
    return { isInMeeting: false, meetingInfo: null };
});

ipcMain.handle('force-teams-check', async () => {
    if (teamsDetector) {
        return await teamsDetector.forceCheck();
    }
    return { isInMeeting: false, meetingInfo: null };
});

ipcMain.handle('set-auto-start-overlay', (event, value) => {
    autoStartOverlay = value;
    store.set('autoStartOverlay', value);
    return true;
});

/**
 * Settings IPC handlers
 */
ipcMain.handle('get-settings', () => {
    // Return all settings from store
    return store.store;
});

ipcMain.handle('save-settings', (event, settings) => {
    // Save all settings to store
    for (const [key, value] of Object.entries(settings)) {
        store.set(key, value);
    }

    // Update runtime values that affect app behavior
    if (settings.autoStartOverlay !== undefined) {
        autoStartOverlay = settings.autoStartOverlay;
    }

    return true;
});

ipcMain.handle('clear-cache', async () => {
    // Clear cache-related settings
    // Note: Actual model cache clearing should be done by the backend
    console.log('[App] Cache clear requested');
    return true;
});

ipcMain.handle('clear-speakers', async () => {
    // Clear speaker-related settings
    store.delete('speakers');
    store.delete('speaker_embeddings');
    console.log('[App] Speakers cleared');
    return true;
});
