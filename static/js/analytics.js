// Analytics Dashboard JavaScript
document.addEventListener('DOMContentLoaded', function() {
    let charts = {};
    let currentDays = 90;
    
    // Initialize dashboard
    loadAnalytics();
    setupEventListeners();
    
    function setupEventListeners() {
        document.getElementById('days-filter').addEventListener('change', (e) => {
            currentDays = parseInt(e.target.value);
            loadAnalytics();
        });
        
        document.getElementById('word-trend-granularity').addEventListener('change', (e) => {
            loadWordCountTrend(e.target.value);
        });
        
        document.getElementById('mood-trend-granularity').addEventListener('change', (e) => {
            loadMoodTrend(e.target.value);
        });
        
        document.getElementById('export-btn').addEventListener('click', () => {
            window.location.href = `/api/analytics/export-csv/?type=full&days=${currentDays}`;
        });
    }
    
    async function loadAnalytics() {
        try {
            await Promise.all([
                loadStreaks(),
                loadWordCountStats(),
                loadMoodDistribution(),
                loadTopThemes(),
                loadWordCountTrend('weekly'),
                loadMoodTrend('weekly')
            ]);
        } catch (error) {
            console.error('Error loading analytics:', error);
        }
    }
    
    async function loadStreaks() {
        const response = await fetch(`/api/analytics/streaks/?days=${currentDays}`);
        const data = await response.json();
        
        document.getElementById('current-streak').textContent = data.current_streak;
        document.getElementById('longest-streak').textContent = data.longest_streak;
        document.getElementById('last-entry-date').textContent = 
            data.last_entry_date ? new Date(data.last_entry_date).toLocaleDateString() : '--';
    }
    
    async function loadWordCountStats() {
        const response = await fetch(`/api/analytics/word-count-stats/?days=${currentDays}`);
        const data = await response.json();
        
        document.getElementById('total-words').textContent = data.total_words.toLocaleString();
        document.getElementById('avg-words').textContent = data.avg_words_per_entry.toFixed(1);
        document.getElementById('max-words').textContent = data.max_words_in_entry;
        document.getElementById('min-words').textContent = data.min_words_in_entry;
    }
    
    async function loadMoodDistribution() {
        const response = await fetch(`/api/analytics/mood-distribution/?days=${currentDays}`);
        const data = await response.json();
        
        const ctx = document.getElementById('moodDistributionChart').getContext('2d');
        
        if (charts.moodDistribution) {
            charts.moodDistribution.destroy();
        }
        
        charts.moodDistribution = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: Object.keys(data).map(m => capitalizeFirst(m)),
                datasets: [{
                    data: Object.values(data),
                    backgroundColor: [
                        '#FFD93D',  // joyful
                        '#6C5B7B',  // sad
                        '#C44569',  // angry
                        '#A8DADC',  // anxious
                        '#457B9D',  // calm
                        '#95B8D1'   // neutral
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }
    
    async function loadTopThemes() {
        const response = await fetch(`/api/analytics/top-themes/?days=${currentDays}&limit=5`);
        const data = await response.json();
        
        const themesList = document.getElementById('themes-list');
        themesList.innerHTML = data.themes.map(theme => `
            <div class="theme-item">
                <span class="theme-name">${theme.theme}</span>
                <div class="theme-stats">
                    <span class="theme-count">${theme.count} entries</span>
                    <span class="theme-sentiment">Sentiment: ${theme.avg_sentiment.toFixed(2)}</span>
                </div>
            </div>
        `).join('');
    }
    
    async function loadWordCountTrend(granularity) {
        const response = await fetch(`/api/analytics/word-count-trend/?granularity=${granularity}&days=${currentDays}`);
        const data = await response.json();
        
        const ctx = document.getElementById('wordCountChart').getContext('2d');
        
        if (charts.wordCount) {
            charts.wordCount.destroy();
        }
        
        charts.wordCount = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.trend.map(item => new Date(item.date).toLocaleDateString()),
                datasets: [{
                    label: 'Words Written',
                    data: data.trend.map(item => item.words),
                    borderColor: '#667eea',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    tension: 0.3,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Words'
                        }
                    }
                }
            }
        });
    }
    
    async function loadMoodTrend(granularity) {
        const response = await fetch(`/api/analytics/mood-trend/?granularity=${granularity}&days=${currentDays}`);
        const data = await response.json();
        
        const ctx = document.getElementById('moodTrendChart').getContext('2d');
        
        if (charts.moodTrend) {
            charts.moodTrend.destroy();
        }
        
        const emotions = ['joyful', 'sad', 'angry', 'anxious', 'calm', 'neutral'];
        const colors = {
            'joyful': '#FFD93D',
            'sad': '#6C5B7B',
            'angry': '#C44569',
            'anxious': '#A8DADC',
            'calm': '#457B9D',
            'neutral': '#95B8D1'
        };
        
        charts.moodTrend = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.trend.map(item => new Date(item.date).toLocaleDateString()),
                datasets: emotions.map(emotion => ({
                    label: capitalizeFirst(emotion),
                    data: data.trend.map(item => item.moods[emotion] || 0),
                    backgroundColor: colors[emotion]
                }))
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                },
                scales: {
                    x: {
                        stacked: true
                    },
                    y: {
                        stacked: true,
                        beginAtZero: true
                    }
                }
            }
        });
    }
    
    function capitalizeFirst(str) {
        return str.charAt(0).toUpperCase() + str.slice(1);
    }
});
