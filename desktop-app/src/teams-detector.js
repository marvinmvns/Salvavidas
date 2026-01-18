/**
 * Microsoft Teams Meeting Auto-Detector
 *
 * Detects when a Teams meeting is active and provides meeting metadata.
 * Works across Windows, macOS, and Linux.
 */

const { exec } = require('child_process');
const util = require('util');
const execPromise = util.promisify(exec);

class TeamsDetector {
    constructor() {
        this.isInMeeting = false;
        this.meetingInfo = null;
        this.checkInterval = null;
        this.pollIntervalMs = 5000; // Check every 5 seconds
        this.listeners = [];

        this.platform = process.platform; // 'win32', 'darwin', 'linux'
    }

    /**
     * Start monitoring for Teams meetings
     */
    start() {
        console.log('[TeamsDetector] Starting Teams meeting detection...');

        // Initial check
        this.checkTeamsMeeting();

        // Poll every N seconds
        this.checkInterval = setInterval(() => {
            this.checkTeamsMeeting();
        }, this.pollIntervalMs);
    }

    /**
     * Stop monitoring
     */
    stop() {
        if (this.checkInterval) {
            clearInterval(this.checkInterval);
            this.checkInterval = null;
        }
        console.log('[TeamsDetector] Stopped Teams meeting detection');
    }

    /**
     * Add event listener for meeting state changes
     */
    on(event, callback) {
        this.listeners.push({ event, callback });
    }

    /**
     * Emit event to all listeners
     */
    emit(event, data) {
        this.listeners
            .filter(l => l.event === event)
            .forEach(l => l.callback(data));
    }

    /**
     * Main check function - detects if Teams meeting is active
     */
    async checkTeamsMeeting() {
        try {
            const wasInMeeting = this.isInMeeting;

            // Check based on platform
            if (this.platform === 'win32') {
                await this.checkTeamsWindows();
            } else if (this.platform === 'darwin') {
                await this.checkTeamsMacOS();
            } else if (this.platform === 'linux') {
                await this.checkTeamsLinux();
            }

            // Emit events on state change
            if (!wasInMeeting && this.isInMeeting) {
                console.log('[TeamsDetector] Meeting started:', this.meetingInfo);
                this.emit('meeting-started', this.meetingInfo);
            } else if (wasInMeeting && !this.isInMeeting) {
                console.log('[TeamsDetector] Meeting ended');
                this.emit('meeting-ended', this.meetingInfo);
                this.meetingInfo = null;
            }

        } catch (error) {
            console.error('[TeamsDetector] Error checking Teams meeting:', error);
        }
    }

    /**
     * Check Teams meeting on Windows
     */
    async checkTeamsWindows() {
        try {
            // Use PowerShell to get Teams windows
            const psCommand = `
                Get-Process -Name Teams -ErrorAction SilentlyContinue |
                ForEach-Object {
                    $_.MainWindowTitle
                } |
                Where-Object { $_ -match "Meeting|Call|Video" }
            `;

            const { stdout } = await execPromise(`powershell -Command "${psCommand}"`);
            const windowTitle = stdout.trim();

            if (windowTitle && windowTitle.length > 0) {
                this.isInMeeting = true;
                this.meetingInfo = {
                    platform: 'Teams',
                    title: windowTitle,
                    timestamp: new Date().toISOString()
                };
            } else {
                // Also check if Teams process exists
                const { stdout: teamsCheck } = await execPromise('tasklist /FI "IMAGENAME eq Teams.exe" /NH');

                // Check for meeting-related window titles
                if (teamsCheck.includes('Teams.exe')) {
                    const { stdout: windowList } = await execPromise('powershell "Get-Process Teams | Select-Object MainWindowTitle | Format-Table -HideTableHeaders"');

                    const hasMeetingWindow = windowList.toLowerCase().includes('meeting') ||
                                           windowList.toLowerCase().includes('call') ||
                                           windowList.toLowerCase().includes('video');

                    this.isInMeeting = hasMeetingWindow;

                    if (hasMeetingWindow) {
                        this.meetingInfo = {
                            platform: 'Teams',
                            title: 'Teams Meeting',
                            timestamp: new Date().toISOString()
                        };
                    }
                } else {
                    this.isInMeeting = false;
                }
            }

        } catch (error) {
            // Teams not running or error occurred
            this.isInMeeting = false;
        }
    }

    /**
     * Check Teams meeting on macOS
     */
    async checkTeamsMacOS() {
        try {
            // Use AppleScript to get Teams window title
            const appleScript = `
                tell application "System Events"
                    if exists (process "Microsoft Teams") then
                        tell process "Microsoft Teams"
                            set windowTitles to name of every window
                            return windowTitles as string
                        end tell
                    else
                        return ""
                    end if
                end tell
            `;

            const { stdout } = await execPromise(`osascript -e '${appleScript}'`);
            const windowTitles = stdout.trim();

            const hasMeeting = windowTitles.toLowerCase().includes('meeting') ||
                             windowTitles.toLowerCase().includes('call') ||
                             windowTitles.toLowerCase().includes('video');

            this.isInMeeting = hasMeeting;

            if (hasMeeting) {
                this.meetingInfo = {
                    platform: 'Teams',
                    title: windowTitles,
                    timestamp: new Date().toISOString()
                };
            }

        } catch (error) {
            this.isInMeeting = false;
        }
    }

    /**
     * Check Teams meeting on Linux
     */
    async checkTeamsLinux() {
        try {
            // Check if Teams process is running
            const { stdout: processCheck } = await execPromise('ps aux | grep -i teams | grep -v grep || true');

            if (!processCheck.trim()) {
                this.isInMeeting = false;
                return;
            }

            // Get window titles using wmctrl (if available)
            try {
                const { stdout: windows } = await execPromise('wmctrl -l || xdotool search --name "Teams" getwindowname %@ || true');

                const hasMeeting = windows.toLowerCase().includes('meeting') ||
                                 windows.toLowerCase().includes('call') ||
                                 windows.toLowerCase().includes('video');

                this.isInMeeting = hasMeeting;

                if (hasMeeting) {
                    this.meetingInfo = {
                        platform: 'Teams',
                        title: windows.trim(),
                        timestamp: new Date().toISOString()
                    };
                }

            } catch (wmError) {
                // wmctrl not available, just check if Teams is running
                this.isInMeeting = processCheck.includes('teams');

                if (this.isInMeeting) {
                    this.meetingInfo = {
                        platform: 'Teams',
                        title: 'Teams (detected)',
                        timestamp: new Date().toISOString()
                    };
                }
            }

        } catch (error) {
            this.isInMeeting = false;
        }
    }

    /**
     * Get current meeting status
     */
    getStatus() {
        return {
            isInMeeting: this.isInMeeting,
            meetingInfo: this.meetingInfo
        };
    }

    /**
     * Manually trigger a check (useful for testing)
     */
    async forceCheck() {
        await this.checkTeamsMeeting();
        return this.getStatus();
    }
}

module.exports = TeamsDetector;
