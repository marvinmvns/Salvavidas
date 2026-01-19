/**
 * Salvavidas Settings Manager
 * Manages all application settings with persistence
 */

// Default settings
const DEFAULT_SETTINGS = {
    // General
    target_language: 'en',
    source_language: '',
    enable_speaker_id: true,
    enable_suggestions: true,
    enable_sentiment: true,
    show_latency_monitor: true,

    // AI & Models
    processing_mode: 'local',
    whisper_model: 'large-v3',
    latency_priority: 'realtime',
    openai_api_key: '',
    deepgram_api_key: '',
    deepl_api_key: '',
    elevenlabs_api_key: '',
    huggingface_token: '',

    // Audio
    sample_rate: 16000,
    chunk_size: 1024,
    channels: 1,
    capture_microphone: true,
    capture_system_audio: true,
    mix_streams: true,

    // Teams
    teams_auto_detect: true,
    teams_auto_start: false,
    teams_extract_names: true,
    overlay_opacity: 95,
    overlay_always_on_top: true,
    overlay_invisible_to_capture: true,

    // Advanced
    use_intel_gpu: false,
    auto_launch: false,
    minimize_to_tray: true,
    backend_url: 'ws://localhost:8000'
};

// Current settings (loaded from storage)
let currentSettings = { ...DEFAULT_SETTINGS };

/**
 * Initialize settings page
 */
async function initializeSettings() {
    console.log('[Settings] Initializing...');

    // Load settings from storage
    await loadSettings();

    // Populate form with current settings
    populateForm();

    // Setup event listeners
    setupEventListeners();

    console.log('[Settings] Initialized');
}

/**
 * Load settings from electron store
 */
async function loadSettings() {
    try {
        if (window.electronAPI && window.electronAPI.getSettings) {
            const stored = await window.electronAPI.getSettings();
            currentSettings = { ...DEFAULT_SETTINGS, ...stored };
            console.log('[Settings] Loaded:', currentSettings);
        } else {
            console.warn('[Settings] No electronAPI available, using defaults');
        }
    } catch (error) {
        console.error('[Settings] Error loading:', error);
        currentSettings = { ...DEFAULT_SETTINGS };
    }
}

/**
 * Populate form with current settings
 */
function populateForm() {
    // Text inputs and selects
    for (const [key, value] of Object.entries(currentSettings)) {
        const element = document.getElementById(key);

        if (element) {
            if (element.type === 'checkbox') {
                element.checked = value;
            } else if (element.type === 'radio') {
                if (element.value === value) {
                    element.checked = true;
                }
            } else if (element.type === 'range') {
                element.value = value;
                // Update range value display
                const display = document.getElementById(`${key}_value`);
                if (display) {
                    display.textContent = value;
                }
            } else {
                element.value = value;
            }
        }
    }

    // Radio groups
    const modeRadios = document.getElementsByName('processing_mode');
    modeRadios.forEach(radio => {
        if (radio.value === currentSettings.processing_mode) {
            radio.checked = true;
        }
    });
}

/**
 * Setup event listeners
 */
function setupEventListeners() {
    // Range inputs - show value
    const rangeInputs = document.querySelectorAll('input[type="range"]');
    rangeInputs.forEach(input => {
        input.addEventListener('input', (e) => {
            const display = document.getElementById(`${e.target.id}_value`);
            if (display) {
                display.textContent = e.target.value;
            }
        });
    });

    // Processing mode change - enable/disable API keys
    const modeRadios = document.getElementsByName('processing_mode');
    modeRadios.forEach(radio => {
        radio.addEventListener('change', (e) => {
            updateAPIKeyFields(e.target.value);
        });
    });

    // Initial API key state
    updateAPIKeyFields(currentSettings.processing_mode);
}

/**
 * Update API key fields based on processing mode
 */
function updateAPIKeyFields(mode) {
    const apiKeys = [
        'openai_api_key',
        'deepgram_api_key',
        'deepl_api_key',
        'elevenlabs_api_key'
    ];

    const isLocal = mode === 'local';

    apiKeys.forEach(key => {
        const field = document.getElementById(key);
        if (field) {
            field.disabled = isLocal;
            field.style.opacity = isLocal ? '0.5' : '1';
        }
    });
}

/**
 * Switch between tabs
 */
function switchTab(tabName) {
    // Hide all tabs
    const tabs = document.querySelectorAll('.tab-content');
    tabs.forEach(tab => {
        tab.classList.remove('active');
    });

    // Remove active class from all tab buttons
    const tabButtons = document.querySelectorAll('.tab');
    tabButtons.forEach(btn => {
        btn.classList.remove('active');
    });

    // Show selected tab
    const selectedTab = document.getElementById(`tab-${tabName}`);
    if (selectedTab) {
        selectedTab.classList.add('active');
    }

    // Activate tab button
    const activeButton = event.target;
    if (activeButton) {
        activeButton.classList.add('active');
    }
}

/**
 * Collect settings from form
 */
function collectFormData() {
    const settings = {};

    // Text inputs, selects, and checkboxes
    for (const key of Object.keys(DEFAULT_SETTINGS)) {
        const element = document.getElementById(key);

        if (element) {
            if (element.type === 'checkbox') {
                settings[key] = element.checked;
            } else if (element.type === 'number' || element.type === 'range') {
                settings[key] = parseInt(element.value);
            } else {
                settings[key] = element.value;
            }
        }
    }

    // Radio groups
    const modeRadio = document.querySelector('input[name="processing_mode"]:checked');
    if (modeRadio) {
        settings.processing_mode = modeRadio.value;
    }

    return settings;
}

/**
 * Save settings
 */
async function saveSettings() {
    try {
        // Collect form data
        const newSettings = collectFormData();

        console.log('[Settings] Saving:', newSettings);

        // Save via electronAPI
        if (window.electronAPI && window.electronAPI.saveSettings) {
            await window.electronAPI.saveSettings(newSettings);

            // Show success message
            showNotification('✅ Configurações salvas com sucesso!', 'success');

            // Update current settings
            currentSettings = { ...newSettings };

            // Close window after 1 second
            setTimeout(() => {
                window.close();
            }, 1000);
        } else {
            console.error('[Settings] electronAPI not available');
            showNotification('❌ Erro ao salvar configurações', 'error');
        }
    } catch (error) {
        console.error('[Settings] Error saving:', error);
        showNotification('❌ Erro ao salvar: ' + error.message, 'error');
    }
}

/**
 * Reset settings to defaults
 */
async function resetSettings() {
    const confirmed = confirm(
        'Tem certeza que deseja restaurar todas as configurações para os valores padrão?\n\n' +
        'Esta ação não pode ser desfeita.'
    );

    if (confirmed) {
        currentSettings = { ...DEFAULT_SETTINGS };
        populateForm();

        await saveSettings();

        showNotification('♻️ Configurações restauradas para padrão', 'info');
    }
}

/**
 * Clear cache
 */
async function clearCache() {
    const confirmed = confirm('Limpar cache de modelos e dados temporários?');

    if (confirmed) {
        if (window.electronAPI && window.electronAPI.clearCache) {
            await window.electronAPI.clearCache();
            showNotification('🗑️ Cache limpo com sucesso', 'success');
        }
    }
}

/**
 * Clear all speakers
 */
async function clearSpeakers() {
    const confirmed = confirm(
        'Tem certeza que deseja remover TODOS os falantes cadastrados?\n\n' +
        'Isso apagará todos os perfis de voz e nomes associados.\n\n' +
        'Esta ação não pode ser desfeita.'
    );

    if (confirmed) {
        if (window.electronAPI && window.electronAPI.clearSpeakers) {
            await window.electronAPI.clearSpeakers();
            showNotification('🗑️ Todos os falantes foram removidos', 'success');
        }
    }
}

/**
 * Show notification
 */
function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 20px;
        background: ${type === 'success' ? '#48bb78' : type === 'error' ? '#f56565' : '#667eea'};
        color: white;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        z-index: 10000;
        animation: slideInRight 0.3s ease-out;
        font-weight: 500;
    `;
    notification.textContent = message;

    // Add to DOM
    document.body.appendChild(notification);

    // Remove after 3 seconds
    setTimeout(() => {
        notification.style.animation = 'slideOutRight 0.3s ease-in';
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, 3000);
}

// Add animation styles
const style = document.createElement('style');
style.textContent = `
    @keyframes slideInRight {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }

    @keyframes slideOutRight {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeSettings);
} else {
    initializeSettings();
}
