/**
 * Salvavidas Speaker Management
 * Frontend for speaker enrollment and management
 */

const API_BASE = window.location.origin;

// State
let currentTab = 'enroll';
let enrollmentSession = null;
let isRecording = false;
let mediaRecorder = null;
let audioChunks = [];
let samplesRecorded = 0;
let samplesRequired = 3;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    console.log('[Speakers] Initializing...');
    loadSpeakers();
});

/**
 * Switch between tabs
 */
function switchTab(tab) {
    currentTab = tab;

    // Update tab buttons
    document.querySelectorAll('.tab').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.classList.add('active');

    // Update content sections
    document.querySelectorAll('.content-section').forEach(section => {
        section.classList.remove('active');
    });

    if (tab === 'enroll') {
        document.getElementById('enroll-section').classList.add('active');
    } else if (tab === 'list') {
        document.getElementById('list-section').classList.add('active');
        loadSpeakers();
    }
}

/**
 * Start enrollment process
 */
async function startEnrollment() {
    const name = document.getElementById('speaker-name').value.trim();
    const email = document.getElementById('speaker-email').value.trim();
    const language = document.getElementById('speaker-language').value;

    if (!name) {
        showNotification('Please enter speaker name', 'error');
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/api/speakers/enroll/start`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                name: name,
                email: email || null,
                language: language
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();
        enrollmentSession = data;
        samplesRequired = data.samples_required;

        // Switch to recording step
        document.getElementById('step-info').style.display = 'none';
        document.getElementById('step-recording').style.display = 'block';

        showNotification(`Enrollment started for ${name}`, 'success');

    } catch (error) {
        console.error('[Speakers] Failed to start enrollment:', error);
        showNotification('Failed to start enrollment', 'error');
    }
}

/**
 * Toggle recording
 */
async function toggleRecording() {
    if (isRecording) {
        stopRecording();
    } else {
        await startRecording();
    }
}

/**
 * Start recording audio sample
 */
async function startRecording() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({
            audio: {
                echoCancellation: true,
                noiseSuppression: true,
                autoGainControl: true,
                sampleRate: 16000
            }
        });

        mediaRecorder = new MediaRecorder(stream, {
            mimeType: 'audio/webm;codecs=opus'
        });

        audioChunks = [];

        mediaRecorder.ondataavailable = (event) => {
            if (event.data.size > 0) {
                audioChunks.push(event.data);
            }
        };

        mediaRecorder.onstop = async () => {
            const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
            await uploadSample(audioBlob);

            // Stop all tracks
            stream.getTracks().forEach(track => track.stop());
        };

        mediaRecorder.start();
        isRecording = true;

        // Update UI
        document.getElementById('record-btn').classList.add('recording');
        document.getElementById('recording-status').textContent = 'Recording... (click to stop)';

    } catch (error) {
        console.error('[Speakers] Failed to start recording:', error);
        showNotification('Microphone access denied', 'error');
    }
}

/**
 * Stop recording
 */
function stopRecording() {
    if (mediaRecorder && isRecording) {
        mediaRecorder.stop();
        isRecording = false;

        // Update UI
        document.getElementById('record-btn').classList.remove('recording');
        document.getElementById('recording-status').textContent = 'Processing...';
    }
}

/**
 * Upload audio sample
 */
async function uploadSample(audioBlob) {
    if (!enrollmentSession) {
        showNotification('No active enrollment session', 'error');
        return;
    }

    try {
        const formData = new FormData();
        formData.append('audio', audioBlob, 'sample.webm');

        const response = await fetch(
            `${API_BASE}/api/speakers/enroll/${enrollmentSession.session_id}/sample`,
            {
                method: 'POST',
                body: formData
            }
        );

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();
        samplesRecorded = data.samples_collected;

        // Update UI
        updateProgress();
        addSampleToList(samplesRecorded);

        document.getElementById('recording-status').textContent = 'Click to record';

        // Check if complete
        if (data.complete) {
            document.getElementById('complete-btn').disabled = false;
            showNotification('All samples collected! Click "Complete Enrollment"', 'success');
        } else {
            showNotification(`Sample ${samplesRecorded} recorded`, 'success');
        }

    } catch (error) {
        console.error('[Speakers] Failed to upload sample:', error);
        showNotification('Failed to upload sample', 'error');
        document.getElementById('recording-status').textContent = 'Click to record';
    }
}

/**
 * Complete enrollment
 */
async function completeEnrollment() {
    if (!enrollmentSession) return;

    try {
        const response = await fetch(
            `${API_BASE}/api/speakers/enroll/${enrollmentSession.session_id}/complete`,
            { method: 'POST' }
        );

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();

        showNotification(`${data.name} enrolled successfully!`, 'success');

        // Reset enrollment
        resetEnrollment();

        // Switch to speakers list
        setTimeout(() => {
            document.querySelector('.tab:nth-child(2)').click();
        }, 1500);

    } catch (error) {
        console.error('[Speakers] Failed to complete enrollment:', error);
        showNotification('Failed to complete enrollment', 'error');
    }
}

/**
 * Cancel enrollment
 */
async function cancelEnrollment() {
    if (!enrollmentSession) return;

    if (!confirm('Are you sure you want to cancel this enrollment?')) {
        return;
    }

    try {
        await fetch(
            `${API_BASE}/api/speakers/enroll/${enrollmentSession.session_id}`,
            { method: 'DELETE' }
        );

        showNotification('Enrollment cancelled', 'success');
        resetEnrollment();

    } catch (error) {
        console.error('[Speakers] Failed to cancel enrollment:', error);
    }
}

/**
 * Reset enrollment state
 */
function resetEnrollment() {
    enrollmentSession = null;
    samplesRecorded = 0;
    audioChunks = [];

    // Reset UI
    document.getElementById('step-info').style.display = 'block';
    document.getElementById('step-recording').style.display = 'none';
    document.getElementById('speaker-name').value = '';
    document.getElementById('speaker-email').value = '';
    document.getElementById('samples-list').innerHTML = '';
    document.getElementById('complete-btn').disabled = true;
    updateProgress();
}

/**
 * Update progress bar
 */
function updateProgress() {
    const percent = (samplesRecorded / samplesRequired) * 100;
    document.getElementById('progress').style.width = `${percent}%`;
    document.getElementById('sample-count').textContent = `Samples: ${samplesRecorded}/${samplesRequired}`;
}

/**
 * Add sample to list
 */
function addSampleToList(index) {
    const samplesList = document.getElementById('samples-list');
    const item = document.createElement('div');
    item.className = 'sample-item';
    item.innerHTML = `
        <span>✓ Sample ${index} recorded</span>
        <span style="color: #10b981; font-weight: 600;">Ready</span>
    `;
    samplesList.appendChild(item);
}

/**
 * Load all speakers
 */
async function loadSpeakers() {
    try {
        const response = await fetch(`${API_BASE}/api/speakers`);

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();
        displaySpeakers(data.speakers);

    } catch (error) {
        console.error('[Speakers] Failed to load speakers:', error);
        showNotification('Failed to load speakers', 'error');
    }
}

/**
 * Display speakers grid
 */
function displaySpeakers(speakers) {
    const container = document.getElementById('speakers-container');

    if (!speakers || speakers.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <p>No speakers enrolled yet</p>
                <p style="font-size: 14px; margin-top: 8px;">Click "Enroll Speaker" to add your first speaker</p>
            </div>
        `;
        return;
    }

    container.innerHTML = speakers.map(speaker => `
        <div class="speaker-card">
            <h3>${speaker.name}</h3>
            <div class="speaker-meta">
                ${speaker.email || 'No email'} • ${speaker.language.toUpperCase()}
            </div>

            <div class="speaker-stats">
                <div class="stat-item">
                    <div class="stat-value">${speaker.sample_count}</div>
                    <div>Samples</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">${speaker.total_meetings}</div>
                    <div>Meetings</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">${Math.floor(speaker.total_talk_time_seconds / 60)}m</div>
                    <div>Talk Time</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">${Math.round(speaker.recognition_accuracy * 100)}%</div>
                    <div>Accuracy</div>
                </div>
            </div>

            <div style="margin-top: 16px; display: flex; gap: 8px;">
                <button class="btn-primary" style="flex: 1; font-size: 12px;"
                        onclick="viewSpeaker('${speaker.speaker_id}')">
                    View Details
                </button>
                <button class="btn-danger" style="font-size: 12px; padding: 8px 12px;"
                        onclick="deleteSpeaker('${speaker.speaker_id}', '${speaker.name}')">
                    🗑️
                </button>
            </div>
        </div>
    `).join('');
}

/**
 * View speaker details
 */
async function viewSpeaker(speakerId) {
    try {
        const response = await fetch(`${API_BASE}/api/speakers/${speakerId}`);

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const speaker = await response.json();

        alert(`
Speaker: ${speaker.name}
Email: ${speaker.email || 'N/A'}
Language: ${speaker.language}
Organization: ${speaker.organization || 'N/A'}

Samples: ${speaker.sample_count}
Total Meetings: ${speaker.total_meetings}
Talk Time: ${Math.floor(speaker.total_talk_time_seconds / 60)} minutes
Recognition Accuracy: ${Math.round(speaker.recognition_accuracy * 100)}%

Enrolled: ${new Date(speaker.enrollment_date).toLocaleDateString()}
Last Seen: ${speaker.last_seen ? new Date(speaker.last_seen).toLocaleDateString() : 'Never'}
        `.trim());

    } catch (error) {
        console.error('[Speakers] Failed to load speaker:', error);
        showNotification('Failed to load speaker details', 'error');
    }
}

/**
 * Delete speaker
 */
async function deleteSpeaker(speakerId, name) {
    if (!confirm(`Delete speaker "${name}"?\n\nThis action cannot be undone.`)) {
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/api/speakers/${speakerId}`, {
            method: 'DELETE'
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        showNotification(`${name} deleted successfully`, 'success');
        loadSpeakers();

    } catch (error) {
        console.error('[Speakers] Failed to delete speaker:', error);
        showNotification('Failed to delete speaker', 'error');
    }
}

/**
 * Show notification
 */
function showNotification(message, type = 'success') {
    const notification = document.getElementById('notification');
    notification.textContent = message;
    notification.className = `notification ${type} show`;

    setTimeout(() => {
        notification.classList.remove('show');
    }, 3000);
}
