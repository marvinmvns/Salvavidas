/**
 * Participants Extractor for Google Meet and Zoom
 * Extracts participant names from DOM elements
 */

class ParticipantsExtractor {
    constructor() {
        this.platform = this.detectPlatform();
        this.participants = [];
        this.observer = null;
        this.extractionInterval = null;
    }

    /**
     * Detect which meeting platform we're on
     * @returns {string} 'meet' | 'zoom' | 'teams' | 'unknown'
     */
    detectPlatform() {
        const hostname = window.location.hostname;

        if (hostname.includes('meet.google.com')) {
            return 'meet';
        } else if (hostname.includes('zoom.us')) {
            return 'zoom';
        } else if (hostname.includes('teams.microsoft.com')) {
            return 'teams';
        }

        return 'unknown';
    }

    /**
     * Start monitoring for participants
     */
    startMonitoring() {
        console.log('[ParticipantsExtractor] Starting monitoring on:', this.platform);

        // Initial extraction
        this.extractParticipants();

        // Set up periodic extraction
        this.extractionInterval = setInterval(() => {
            this.extractParticipants();
        }, 5000); // Every 5 seconds

        // Set up DOM observer for dynamic changes
        this.setupDOMObserver();
    }

    /**
     * Stop monitoring
     */
    stopMonitoring() {
        if (this.extractionInterval) {
            clearInterval(this.extractionInterval);
            this.extractionInterval = null;
        }

        if (this.observer) {
            this.observer.disconnect();
            this.observer = null;
        }

        console.log('[ParticipantsExtractor] Monitoring stopped');
    }

    /**
     * Set up DOM observer to detect when participant list changes
     */
    setupDOMObserver() {
        const config = { childList: true, subtree: true };

        this.observer = new MutationObserver((mutations) => {
            // Check if any mutation affects participant list
            const affectsParticipants = mutations.some(mutation => {
                const target = mutation.target;
                if (target.nodeType === Node.ELEMENT_NODE) {
                    const el = target;
                    return this.isParticipantListElement(el);
                }
                return false;
            });

            if (affectsParticipants) {
                this.extractParticipants();
            }
        });

        this.observer.observe(document.body, config);
    }

    /**
     * Check if element is related to participant list
     * @param {Element} element
     * @returns {boolean}
     */
    isParticipantListElement(element) {
        const classStr = element.className || '';
        const idStr = element.id || '';

        return (
            classStr.includes('participant') ||
            classStr.includes('roster') ||
            classStr.includes('attendee') ||
            idStr.includes('participant') ||
            idStr.includes('roster')
        );
    }

    /**
     * Extract participants based on platform
     * @returns {Array<string>} Array of participant names
     */
    extractParticipants() {
        let newParticipants = [];

        switch (this.platform) {
            case 'meet':
                newParticipants = this.extractGoogleMeetParticipants();
                break;
            case 'zoom':
                newParticipants = this.extractZoomParticipants();
                break;
            case 'teams':
                newParticipants = this.extractTeamsWebParticipants();
                break;
            default:
                console.warn('[ParticipantsExtractor] Unknown platform');
                return [];
        }

        // Check if participants changed
        if (JSON.stringify(newParticipants) !== JSON.stringify(this.participants)) {
            this.participants = newParticipants;
            console.log('[ParticipantsExtractor] Participants updated:', this.participants);

            // Notify background script
            chrome.runtime.sendMessage({
                type: 'participants_updated',
                participants: this.participants,
                platform: this.platform
            });
        }

        return this.participants;
    }

    /**
     * Extract participants from Google Meet
     * @returns {Array<string>}
     */
    extractGoogleMeetParticipants() {
        const participants = [];

        // Method 1: Participant panel (when open)
        const participantElements = document.querySelectorAll(
            '[data-participant-id], [data-self-name], .participant-name, [jsname="tJHJj"]'
        );

        participantElements.forEach(el => {
            let name = '';

            // Try different selectors
            const nameEl = el.querySelector('.zWGUib') || // Name span
                          el.querySelector('[data-self-name]') ||
                          el;

            name = nameEl.textContent?.trim() || nameEl.getAttribute('data-self-name') || '';

            // Filter out invalid names
            if (name && name.length > 1 && !name.match(/^\d+$/)) {
                // Remove trailing (You) or (Você)
                name = name.replace(/\s*\((You|Você|Me|Moi)\)\s*$/i, '').trim();

                if (name && !participants.includes(name)) {
                    participants.push(name);
                }
            }
        });

        // Method 2: Video tiles with names
        const videoTiles = document.querySelectorAll('[data-participant-id]');
        videoTiles.forEach(tile => {
            const nameElement = tile.querySelector('[class*="name"], .YTbUzc');
            if (nameElement) {
                const name = nameElement.textContent?.trim();
                if (name && name.length > 1 && !participants.includes(name)) {
                    participants.push(name.replace(/\s*\((You|Você)\)\s*$/i, '').trim());
                }
            }
        });

        return participants.filter(n => n && n.length > 0);
    }

    /**
     * Extract participants from Zoom
     * @returns {Array<string>}
     */
    extractZoomParticipants() {
        const participants = [];

        // Method 1: Participants panel
        const participantItems = document.querySelectorAll(
            '.participants-item__display-name, ' +
            '[class*="participant-name"], ' +
            '[data-participant-name], ' +
            '.participants-selector__participant-name'
        );

        participantItems.forEach(el => {
            const name = el.textContent?.trim() || el.getAttribute('data-participant-name');
            if (name && name.length > 1 && !participants.includes(name)) {
                // Remove "(Host)", "(Co-Host)", "(Me)"
                const cleanName = name.replace(/\s*\((Host|Co-Host|Me|Eu|Anfitrião)\)\s*$/i, '').trim();
                if (cleanName) {
                    participants.push(cleanName);
                }
            }
        });

        // Method 2: Video gallery
        const videoNames = document.querySelectorAll(
            '.video-avatar__name, ' +
            '[class*="username"], ' +
            '.video-container__name'
        );

        videoNames.forEach(el => {
            const name = el.textContent?.trim();
            if (name && name.length > 1 && !participants.includes(name)) {
                const cleanName = name.replace(/\s*\((Host|Co-Host|Me|Eu)\)\s*$/i, '').trim();
                if (cleanName) {
                    participants.push(cleanName);
                }
            }
        });

        return participants.filter(n => n && n.length > 0);
    }

    /**
     * Extract participants from Teams Web
     * @returns {Array<string>}
     */
    extractTeamsWebParticipants() {
        const participants = [];

        // Teams web participant selectors
        const selectors = [
            '[data-tid="roster-participant-name"]',
            '[class*="participant-name"]',
            '[class*="roster-name"]',
            '.ts-calling-screen-participant-name'
        ];

        selectors.forEach(selector => {
            const elements = document.querySelectorAll(selector);
            elements.forEach(el => {
                const name = el.textContent?.trim();
                if (name && name.length > 1 && !participants.includes(name)) {
                    // Remove "(You)" or "(Você)"
                    const cleanName = name.replace(/\s*\((You|Você)\)\s*$/i, '').trim();
                    if (cleanName) {
                        participants.push(cleanName);
                    }
                }
            });
        });

        return participants.filter(n => n && n.length > 0);
    }

    /**
     * Get current participants
     * @returns {Array<string>}
     */
    getParticipants() {
        return [...this.participants];
    }

    /**
     * Suggest a participant name for an unknown speaker
     * Simple heuristic: cycle through available names
     * @param {number} speakerIndex - Index of unknown speaker
     * @returns {string|null}
     */
    suggestNameForSpeaker(speakerIndex) {
        if (speakerIndex < this.participants.length) {
            return this.participants[speakerIndex];
        }
        return null;
    }
}

// Initialize if on supported platform
if (window.location.hostname.match(/(meet\.google\.com|zoom\.us|teams\.microsoft\.com)/)) {
    window.participantsExtractor = new ParticipantsExtractor();
    window.participantsExtractor.startMonitoring();

    console.log('[ParticipantsExtractor] Initialized on:', window.participantsExtractor.platform);
}
