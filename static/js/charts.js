// charts.js - إدارة الرسوم البيانية

function initCharts(priorityStats, statusStats, weeklyStats) {
    // Priority Chart
    const priorityCtx = document.getElementById('priorityChart');
    if (priorityCtx) {
        new Chart(priorityCtx, {
            type: 'doughnut',
            data: {
                labels: priorityStats.labels,
                datasets: [{
                    data: priorityStats.data,
                    backgroundColor: priorityStats.colors,
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { position: 'bottom' }
                }
            }
        });
    }

    // Status Chart
    const statusCtx = document.getElementById('statusChart');
    if (statusCtx) {
        new Chart(statusCtx, {
            type: 'doughnut',
            data: {
                labels: statusStats.labels,
                datasets: [{
                    data: statusStats.data,
                    backgroundColor: statusStats.colors,
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { position: 'bottom' }
                }
            }
        });
    }

    // Weekly Chart
    const weeklyCtx = document.getElementById('weeklyChart');
    if (weeklyCtx) {
        new Chart(weeklyCtx, {
            type: 'bar',
            data: {
                labels: weeklyStats.labels,
                datasets: [{
                    label: 'عدد الأعطال',
                    data: weeklyStats.data,
                    backgroundColor: 'rgba(74, 108, 247, 0.7)',
                    borderColor: '#4a6cf7',
                    borderWidth: 2,
                    borderRadius: 8
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: { stepSize: 1 }
                    }
                }
            }
        });
    }
}