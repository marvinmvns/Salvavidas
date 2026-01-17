/**
 * Salvavidas Analytics Dashboard
 * Real-time analytics visualization
 */

const API_BASE = window.location.origin;
let charts = {};
let currentTimeRange = 'last_week';

// Initialize dashboard
document.addEventListener('DOMContentLoaded', () => {
    console.log('[Analytics] Initializing dashboard...');

    // Setup event listeners
    document.getElementById('time-range').addEventListener('change', onTimeRangeChange);
    document.getElementById('refresh-btn').addEventListener('click', refreshData);
    document.getElementById('export-btn').addEventListener('click', exportData);

    // Load initial data
    loadAnalytics();
});

/**
 * Load analytics data from API
 */
async function loadAnalytics() {
    showLoading(true);
    hideError();

    try {
        // Fetch summary data
        const summaryResponse = await fetch(
            `${API_BASE}/api/analytics/summary?time_range=${currentTimeRange}`
        );

        if (!summaryResponse.ok) {
            throw new Error(`HTTP ${summaryResponse.status}: ${summaryResponse.statusText}`);
        }

        const summary = await summaryResponse.json();

        // Fetch sentiment timeline
        const timelineResponse = await fetch(
            `${API_BASE}/api/analytics/sentiment/timeline?time_range=${currentTimeRange}&granularity=hour`
        );
        const timelineData = await timelineResponse.json();

        // Fetch speaker rankings
        const speakersResponse = await fetch(
            `${API_BASE}/api/analytics/speakers/rankings?time_range=${currentTimeRange}&limit=10`
        );
        const speakersData = await speakersResponse.json();

        // Update dashboard
        updateStatistics(summary);
        updateCharts(summary, timelineData.timeline || []);
        updateSpeakersTable(speakersData.rankings || []);

        showLoading(false);
        document.getElementById('dashboard').style.display = 'block';

    } catch (error) {
        console.error('[Analytics] Failed to load data:', error);
        showError(`Failed to load analytics: ${error.message}`);
        showLoading(false);
    }
}

/**
 * Update statistics cards
 */
function updateStatistics(summary) {
    // Total meetings
    document.getElementById('stat-meetings').textContent = summary.total_meetings;

    // Total duration (convert to hours:minutes)
    const hours = Math.floor(summary.total_duration_seconds / 3600);
    const minutes = Math.floor((summary.total_duration_seconds % 3600) / 60);
    document.getElementById('stat-duration').textContent = `${hours}h ${minutes}m`;

    // Unique speakers
    document.getElementById('stat-speakers').textContent = summary.unique_speakers;

    // Sentiment
    const sentimentEmoji = getSentimentEmoji(summary.overall_sentiment_score);
    document.getElementById('stat-sentiment').innerHTML =
        `<span class="sentiment-emoji">${sentimentEmoji}</span><span id="stat-sentiment-value">${summary.overall_sentiment_score.toFixed(2)}</span>`;

    // Sentiment trend
    const trendElement = document.getElementById('stat-sentiment-trend');
    trendElement.textContent = summary.sentiment_trend.charAt(0).toUpperCase() + summary.sentiment_trend.slice(1);
    trendElement.className = `stat-change ${getTrendClass(summary.sentiment_trend)}`;
}

/**
 * Update all charts
 */
function updateCharts(summary, timeline) {
    // Activity chart (meetings per day)
    updateActivityChart(summary.daily_breakdown);

    // Sentiment timeline chart
    updateSentimentChart(timeline);

    // Platform usage chart
    updatePlatformChart(summary);

    // Sentiment distribution chart
    updateSentimentDistributionChart(summary.sentiment_distribution);
}

/**
 * Update activity chart
 */
function updateActivityChart(dailyBreakdown) {
    const ctx = document.getElementById('activity-chart');

    // Destroy existing chart
    if (charts.activity) {
        charts.activity.destroy();
    }

    const labels = dailyBreakdown.map(day => {
        const date = new Date(day.date);
        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    });

    const data = dailyBreakdown.map(day => day.total_meetings);

    charts.activity = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Meetings',
                data: data,
                backgroundColor: 'rgba(102, 126, 234, 0.8)',
                borderColor: 'rgba(102, 126, 234, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        precision: 0
                    }
                }
            }
        }
    });
}

/**
 * Update sentiment timeline chart
 */
function updateSentimentChart(timeline) {
    const ctx = document.getElementById('sentiment-chart');

    // Destroy existing chart
    if (charts.sentiment) {
        charts.sentiment.destroy();
    }

    const labels = timeline.map(point => {
        const date = new Date(point.timestamp);
        return date.toLocaleString('en-US', {
            month: 'short',
            day: 'numeric',
            hour: '2-digit'
        });
    });

    const data = timeline.map(point => point.average_score);

    charts.sentiment = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Sentiment',
                data: data,
                borderColor: 'rgba(118, 75, 162, 1)',
                backgroundColor: 'rgba(118, 75, 162, 0.1)',
                borderWidth: 2,
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    min: -1,
                    max: 1,
                    ticks: {
                        callback: function(value) {
                            if (value === 1) return 'Very Positive';
                            if (value === 0.5) return 'Positive';
                            if (value === 0) return 'Neutral';
                            if (value === -0.5) return 'Negative';
                            if (value === -1) return 'Very Negative';
                            return value.toFixed(1);
                        }
                    }
                }
            }
        }
    });
}

/**
 * Update platform usage chart
 */
function updatePlatformChart(summary) {
    const ctx = document.getElementById('platform-chart');

    // Destroy existing chart
    if (charts.platform) {
        charts.platform.destroy();
    }

    // Count platform usage from daily breakdown
    const platformCounts = {};
    summary.daily_breakdown.forEach(day => {
        Object.entries(day.platform_usage || {}).forEach(([platform, count]) => {
            platformCounts[platform] = (platformCounts[platform] || 0) + count;
        });
    });

    const labels = Object.keys(platformCounts);
    const data = Object.values(platformCounts);

    charts.platform = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels.map(l => l.charAt(0).toUpperCase() + l.slice(1)),
            datasets: [{
                data: data,
                backgroundColor: [
                    'rgba(102, 126, 234, 0.8)',
                    'rgba(118, 75, 162, 0.8)',
                    'rgba(16, 185, 129, 0.8)',
                    'rgba(245, 158, 11, 0.8)',
                    'rgba(239, 68, 68, 0.8)',
                ],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
}

/**
 * Update sentiment distribution chart
 */
function updateSentimentDistributionChart(distribution) {
    const ctx = document.getElementById('sentiment-dist-chart');

    // Destroy existing chart
    if (charts.sentimentDist) {
        charts.sentimentDist.destroy();
    }

    const sentimentLabels = {
        'very_positive': '😄 Very Positive',
        'positive': '🙂 Positive',
        'excited': '🤩 Excited',
        'neutral': '😐 Neutral',
        'confused': '😕 Confused',
        'concerned': '😰 Concerned',
        'negative': '😕 Negative',
        'very_negative': '😢 Very Negative'
    };

    const labels = Object.keys(distribution).map(k => sentimentLabels[k] || k);
    const data = Object.values(distribution);

    charts.sentimentDist = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Count',
                data: data,
                backgroundColor: 'rgba(118, 75, 162, 0.8)',
                borderColor: 'rgba(118, 75, 162, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            indexAxis: 'y',
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    ticks: {
                        precision: 0
                    }
                }
            }
        }
    });
}

/**
 * Update speakers table
 */
function updateSpeakersTable(rankings) {
    const tbody = document.getElementById('speakers-table');

    if (!rankings || rankings.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; color: #999;">No speakers found</td></tr>';
        return;
    }

    tbody.innerHTML = rankings.map((speaker, index) => {
        const talkTime = formatDuration(speaker.total_talk_time_seconds);
        const sentiment = speaker.average_sentiment_score.toFixed(2);
        const sentimentClass = speaker.average_sentiment_score > 0.3 ? 'positive' :
                              speaker.average_sentiment_score < -0.3 ? 'negative' : 'neutral';

        return `
            <tr>
                <td><strong>#${index + 1}</strong></td>
                <td>${speaker.speaker_name}</td>
                <td>${speaker.total_meetings}</td>
                <td>${talkTime}</td>
                <td><span class="stat-change ${sentimentClass}">${sentiment}</span></td>
                <td>${speaker.questions_asked}</td>
            </tr>
        `;
    }).join('');
}

/**
 * Event handlers
 */
function onTimeRangeChange(event) {
    currentTimeRange = event.target.value;
    loadAnalytics();
}

function refreshData() {
    loadAnalytics();
}

async function exportData() {
    const exportBtn = document.getElementById('export-btn');
    exportBtn.disabled = true;
    exportBtn.textContent = '📥 Exporting...';

    try {
        const response = await fetch(`${API_BASE}/api/analytics/export`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                format: 'csv',
                time_range: currentTimeRange,
                include_speaker_breakdown: true,
                include_sentiment_analysis: true
            })
        });

        if (!response.ok) {
            throw new Error('Export failed');
        }

        const result = await response.json();

        // In a real implementation, would download the file
        alert(`Export successful! File: ${result.file_path}\nSize: ${(result.file_size_bytes / 1024).toFixed(2)} KB`);

    } catch (error) {
        console.error('[Analytics] Export failed:', error);
        alert('Failed to export data: ' + error.message);
    } finally {
        exportBtn.disabled = false;
        exportBtn.textContent = '📥 Export CSV';
    }
}

/**
 * Helper functions
 */
function getSentimentEmoji(score) {
    if (score >= 0.7) return '😄';
    if (score >= 0.3) return '🙂';
    if (score >= -0.2) return '😐';
    if (score >= -0.6) return '😕';
    return '😢';
}

function getTrendClass(trend) {
    if (trend === 'improving') return 'positive';
    if (trend === 'declining') return 'negative';
    return 'neutral';
}

function formatDuration(seconds) {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);

    if (hours > 0) {
        return `${hours}h ${minutes}m`;
    }
    return `${minutes}m`;
}

function showLoading(show) {
    document.getElementById('loading').style.display = show ? 'block' : 'none';
}

function showError(message) {
    const errorEl = document.getElementById('error-message');
    errorEl.textContent = message;
    errorEl.style.display = 'block';
}

function hideError() {
    document.getElementById('error-message').style.display = 'none';
}
