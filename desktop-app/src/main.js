/**
 * Salvavidas Desktop - Main Process
 * Cross-platform desktop app with invisible mode for screen sharing
 */

const { app, BrowserWindow, globalShortcut, ipcMain, Menu, Tray, screen } = require('electron');
const path = require('path');
const Store = require('electron-store');

const store = new Store();

let mainWindow = null;
let overlayWindow = null;
let tray = null;
let isInvisibleMode = false;

// Disable hardware acceleration for better compatibility
app.disableHardwareAcceleration();

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
 * Create system tray
 */
function createTray() {
    const iconPath = path.join(__dirname, '../build/tray-icon.png');

    tray = new Tray(iconPath);

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
            label: 'Settings',
            click: () => {
                // Open settings
                if (mainWindow) {
                    mainWindow.webContents.send('open-settings');
                }
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

    tray.setToolTip('Salvavidas - Voice Translation');
    tray.setContextMenu(contextMenu);

    // Click to show main window
    tray.on('click', () => {
        if (mainWindow) {
            mainWindow.isVisible() ? mainWindow.hide() : mainWindow.show();
        }
    });
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
    if (tray) {
        const contextMenu = tray.getContextMenu();
        contextMenu.items[2].checked = isInvisibleMode;
    }
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
}

/**
 * App ready
 */
app.whenReady().then(() => {
    createMainWindow();
    createTray();
    registerShortcuts();

    // Create app menu
    const menu = Menu.buildFromTemplate([
        {
            label: 'Salvavidas',
            submenu: [
                { label: 'About', role: 'about' },
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
});

/**
 * IPC Handlers
 */
ipcMain.handle('get-config', () => {
    return store.store;
});

ipcMain.handle('set-config', (event, key, value) => {
    store.set(key, value);
    return true;
});

ipcMain.handle('toggle-overlay', toggleOverlay);
ipcMain.handle('toggle-invisible', toggleInvisibleMode);
