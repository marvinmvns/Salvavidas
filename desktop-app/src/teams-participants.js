/**
 * Teams Participants Extractor
 * Captura nomes dos participantes de reuniões do Microsoft Teams
 */

const { exec } = require('child_process');
const { promisify } = require('util');

const execPromise = promisify(exec);

class TeamsParticipantsExtractor {
    constructor() {
        this.platform = process.platform;
        this.participants = new Map(); // speaker_id -> participant info
        this.lastUpdate = null;
    }

    /**
     * Extract participants from Teams meeting
     * @returns {Promise<Array>} Array of participant names
     */
    async extractParticipants() {
        try {
            switch (this.platform) {
                case 'win32':
                    return await this.extractWindows();
                case 'darwin':
                    return await this.extractMacOS();
                case 'linux':
                    return await this.extractLinux();
                default:
                    console.warn('[TeamsParticipants] Unsupported platform:', this.platform);
                    return [];
            }
        } catch (error) {
            console.error('[TeamsParticipants] Error extracting participants:', error);
            return [];
        }
    }

    /**
     * Extract participants on Windows using PowerShell
     * Attempts to read from Teams window title or accessibility APIs
     */
    async extractWindows() {
        try {
            // Method 1: Try to read from Teams window automation
            const psScript = `
                Add-Type -AssemblyName UIAutomationClient
                Add-Type -AssemblyName UIAutomationTypes

                $teamsWindows = Get-Process -Name Teams | Where-Object { $_.MainWindowTitle -ne "" }

                foreach ($window in $teamsWindows) {
                    if ($window.MainWindowTitle -match "\\|") {
                        # Meeting window format: "Meeting Title | Microsoft Teams"
                        $participants = @()

                        # Try to get automation element
                        try {
                            $automation = [System.Windows.Automation.AutomationElement]::FromHandle($window.MainWindowHandle)

                            # Look for participant list elements
                            $condition = [System.Windows.Automation.PropertyCondition]::new(
                                [System.Windows.Automation.AutomationElement]::ControlTypeProperty,
                                [System.Windows.Automation.ControlType]::List
                            )

                            $participantLists = $automation.FindAll(
                                [System.Windows.Automation.TreeScope]::Descendants,
                                $condition
                            )

                            foreach ($list in $participantLists) {
                                if ($list.Current.Name -match "participant" -or $list.Current.Name -match "roster") {
                                    $items = $list.FindAll(
                                        [System.Windows.Automation.TreeScope]::Children,
                                        [System.Windows.Automation.Condition]::TrueCondition
                                    )

                                    foreach ($item in $items) {
                                        $name = $item.Current.Name
                                        if ($name -and $name -notmatch "^(You|Você|button|list)" -and $name.Length -gt 2) {
                                            $participants += $name
                                        }
                                    }
                                }
                            }
                        } catch {
                            # Automation failed, try window title parsing
                        }

                        if ($participants.Count -gt 0) {
                            $participants | ConvertTo-Json -Compress
                            exit 0
                        }
                    }
                }

                # Fallback: Return empty array
                @() | ConvertTo-Json -Compress
            `.trim();

            const { stdout } = await execPromise(
                `powershell -NoProfile -Command "${psScript.replace(/"/g, '\\"')}"`,
                { timeout: 5000 }
            );

            const participants = JSON.parse(stdout.trim() || '[]');
            this.lastUpdate = Date.now();

            console.log('[TeamsParticipants] Windows - Found participants:', participants);
            return participants;

        } catch (error) {
            console.error('[TeamsParticipants] Windows extraction error:', error.message);
            return [];
        }
    }

    /**
     * Extract participants on macOS using AppleScript
     */
    async extractMacOS() {
        try {
            const appleScript = `
                tell application "System Events"
                    tell process "Microsoft Teams"
                        if exists (window 1) then
                            set windowName to name of window 1

                            -- Check if it's a meeting window
                            if windowName contains "Meeting" or windowName contains "Reunião" then
                                try
                                    -- Try to get participant list
                                    tell window 1
                                        set participantGroups to every group whose description contains "participant" or description contains "roster"
                                        set participantList to {}

                                        repeat with grp in participantGroups
                                            set participantNames to name of every UI element of grp
                                            repeat with pname in participantNames
                                                if pname is not "" and length of pname > 2 then
                                                    if pname does not start with "You" and pname does not start with "Você" then
                                                        set end of participantList to pname
                                                    end if
                                                end if
                                            end repeat
                                        end repeat

                                        return participantList
                                    end tell
                                on error
                                    return {}
                                end try
                            end if
                        end if
                    end tell
                end tell
                return {}
            `.trim();

            const { stdout } = await execPromise(`osascript -e '${appleScript}'`, { timeout: 5000 });

            // Parse AppleScript list format: {item1, item2, item3}
            const participantStr = stdout.trim();
            let participants = [];

            if (participantStr && participantStr.startsWith('{') && participantStr.endsWith('}')) {
                const content = participantStr.slice(1, -1);
                participants = content.split(',').map(s => s.trim()).filter(s => s && s.length > 2);
            }

            this.lastUpdate = Date.now();
            console.log('[TeamsParticipants] macOS - Found participants:', participants);
            return participants;

        } catch (error) {
            console.error('[TeamsParticipants] macOS extraction error:', error.message);
            return [];
        }
    }

    /**
     * Extract participants on Linux using window inspection
     */
    async extractLinux() {
        try {
            // Method 1: Try xdotool to get window info
            const { stdout: windowId } = await execPromise(
                'xdotool search --name "Microsoft Teams" | head -1',
                { timeout: 3000 }
            );

            if (!windowId.trim()) {
                return [];
            }

            // Try to get window properties that might contain participant info
            // Note: This is limited on Linux, may require accessibility tools
            const { stdout: props } = await execPromise(
                `xdotool getwindowname ${windowId.trim()}`,
                { timeout: 2000 }
            );

            // Parse window title for participant count hints
            // Teams on Linux typically shows: "Meeting Title | Microsoft Teams"
            // Actual participant names require accessibility APIs

            this.lastUpdate = Date.now();
            console.log('[TeamsParticipants] Linux - Window title:', props.trim());

            // TODO: Implement more sophisticated Linux extraction
            // May require: at-spi, accessibility APIs, or screen reading tools

            return [];

        } catch (error) {
            console.error('[TeamsParticipants] Linux extraction error:', error.message);
            return [];
        }
    }

    /**
     * Associate a participant name with a speaker ID
     * @param {string} speakerId - Speaker ID from voice analysis
     * @param {string} participantName - Participant name from Teams
     */
    associateParticipant(speakerId, participantName) {
        this.participants.set(speakerId, {
            name: participantName,
            associatedAt: Date.now()
        });
        console.log(`[TeamsParticipants] Associated ${speakerId} with ${participantName}`);
    }

    /**
     * Get participant name for a speaker ID
     * @param {string} speakerId
     * @returns {string|null}
     */
    getParticipantName(speakerId) {
        const info = this.participants.get(speakerId);
        return info ? info.name : null;
    }

    /**
     * Auto-detect and assign participant names based on speaking order
     * Simple heuristic: first unknown speaker gets first participant name, etc.
     * @param {Array} unknownSpeakers - Array of unknown speaker IDs
     * @returns {Map} Map of speaker ID to suggested name
     */
    autoAssignNames(unknownSpeakers) {
        const suggestions = new Map();
        const participantsList = Array.from(this.participants.values());

        unknownSpeakers.forEach((speakerId, index) => {
            if (index < participantsList.length) {
                suggestions.set(speakerId, participantsList[index].name);
            }
        });

        return suggestions;
    }

    /**
     * Clear all associations
     */
    clear() {
        this.participants.clear();
        this.lastUpdate = null;
    }
}

module.exports = TeamsParticipantsExtractor;
