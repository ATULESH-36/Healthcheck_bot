/* static/js/app.js */
// Global Chart settings
Chart.defaults.color = '#94a3b8';
Chart.defaults.font.family = "'Inter', sans-serif";

// State
const maxDataPoints = 30; // 30 ticks of data points
let timeLabels = [];
let cpuData = [];
let responseData = [];

// Initialize time array
for (let i = 0; i < maxDataPoints; i++) {
    timeLabels.push('');
    cpuData.push(null);
    responseData.push(null);
}

// Helper: Setup Line Chart
function createLineChart(ctx, label, color, dataArr) {
    return new Chart(ctx, {
        type: 'line',
        data: {
            labels: timeLabels,
            datasets: [{
                label: label,
                data: dataArr,
                borderColor: color,
                backgroundColor: color + '22',
                borderWidth: 2,
                pointRadius: 0,
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: { duration: 0 },
            plugins: {
                legend: { display: false },
                tooltip: { enabled: false }
            },
            scales: {
                x: { display: false },
                y: {
                    display: true,
                    min: 0,
                    max: 100,
                    grid: { color: 'rgba(255,255,255,0.05)' },
                    border: { display: false }
                }
            }
        }
    });
}

// Helper: Setup Doughnut Gauge
function createGauge(ctx, color) {
    return new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Used', 'Free'],
            datasets: [{
                data: [0, 100],
                backgroundColor: [color, 'rgba(255,255,255,0.05)'],
                borderWidth: 0,
                cutout: '80%',
                circumference: 270,
                rotation: 225
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: { enabled: false }
            }
        }
    });
}

// Initialize Charts
const cpuChart = createLineChart(
    document.getElementById('cpuChart').getContext('2d'),
    'CPU',
    '#10b981',
    cpuData
);

const respCtx = document.getElementById('responseChart').getContext('2d');
const responseChartCtx = new Chart(respCtx, {
    type: 'line',
    data: {
        labels: timeLabels,
        datasets: [{
            label: 'Response Time',
            data: responseData,
            borderColor: '#f59e0b',
            backgroundColor: 'rgba(245, 158, 11, 0.1)',
            borderWidth: 2,
            pointRadius: 0,
            fill: true,
            tension: 0.4
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: { duration: 0 },
        plugins: { legend: { display: false } },
        scales: {
            x: { display: false },
            y: { min: 0, grid: { color: 'rgba(255,255,255,0.05)' } }
        }
    }
});

const memCtx = document.getElementById('memoryChart').getContext('2d');
const memChart = createGauge(memCtx, '#00f2fe');

const diskCtx = document.getElementById('diskChart').getContext('2d');
const diskChart = createGauge(diskCtx, '#f59e0b');

// Function to update the UI with new JSON data
function updateDashboard(data) {
    if (!data || data.error) return;

    // 1. Update line charts
    cpuData.push(data.cpu);
    cpuData.shift();
    cpuChart.update();

    document.getElementById('cpu-footer').innerHTML = `<span class="val" style="color:#10b981">${data.cpu.toFixed(1)}%</span> CPU Usage`;

    // 2. Update Gauges
    const memPercent = data.mem_percent;
    const memColor = memPercent > 85 ? '#ef4444' : (memPercent > 70 ? '#f59e0b' : '#00f2fe');
    memChart.data.datasets[0].data = [memPercent, 100 - memPercent];
    memChart.data.datasets[0].backgroundColor[0] = memColor;
    memChart.update();
    document.getElementById('memory-center').innerHTML = `<span style="color:${memColor}">${memPercent.toFixed(1)}<span style="font-size:14px">%</span></span>`;
    document.getElementById('memory-footer').innerHTML = `${data.mem_used_gb.toFixed(1)} GB / ${data.mem_total_gb.toFixed(1)} GB`;

    const diskPercent = data.disk_percent;
    const diskColor = diskPercent > 90 ? '#ef4444' : (diskPercent > 75 ? '#f59e0b' : '#10b981');
    diskChart.data.datasets[0].data = [diskPercent, 100 - diskPercent];
    diskChart.data.datasets[0].backgroundColor[0] = diskColor;
    diskChart.update();
    document.getElementById('disk-center').innerHTML = `<span style="color:${diskColor}">${diskPercent.toFixed(1)}<span style="font-size:14px">%</span></span>`;
    document.getElementById('disk-footer').innerHTML = `${data.disk_used_gb.toFixed(1)} GB / ${data.disk_total_gb.toFixed(1)} GB`;

    // 3. Network Status
    const pingEl = document.getElementById('ping-status');
    if (data.ping_ok) {
        pingEl.innerHTML = `<span style="color:#10b981">Reachable (${data.ping_host})</span>`;
    } else {
        pingEl.innerHTML = `<span style="color:#ef4444">Unreachable</span>`;
    }

    const epEl = document.getElementById('endpoint-status');
    if (data.endpoint_ok) {
        epEl.innerHTML = `<span style="color:#10b981">200 OK</span>`;
    } else {
        epEl.innerHTML = `<span style="color:#ef4444">Error ${data.endpoint_status}</span>`;
    }

    // 4. Update Checks Table
    const checksBody = document.getElementById('checks-table-body');
    checksBody.innerHTML = `
        <tr>
            <td>CPU</td>
            <td>80%</td>
            <td>${data.cpu <= 80 ? '<span class="badge success">OK</span>' : '<span class="badge critical">CRITICAL</span>'}</td>
        </tr>
        <tr>
            <td>Memory</td>
            <td>85%</td>
            <td>${data.mem_percent <= 85 ? '<span class="badge success">OK</span>' : '<span class="badge warning">WARNING</span>'}</td>
        </tr>
        <tr>
            <td>Disk</td>
            <td>90%</td>
            <td>${data.disk_percent <= 90 ? '<span class="badge success">OK</span>' : '<span class="badge warning">WARNING</span>'}</td>
        </tr>
        <tr>
            <td>Ping</td>
            <td>Reachable</td>
            <td>${data.ping_ok ? '<span class="badge success">OK</span>' : '<span class="badge critical">FAIL</span>'}</td>
        </tr>
        <tr>
            <td>HTTP</td>
            <td>200 OK</td>
            <td>${data.endpoint_ok ? '<span class="badge success">OK</span>' : '<span class="badge critical">FAIL</span>'}</td>
        </tr>
    `;

    // 5. Update Processes Table
    if (data.top_processes) {
        const procBody = document.getElementById('processes-table-body');
        let html = '';
        data.top_processes.forEach(p => {
            html += `
                <tr>
                    <td>${p.name}</td>
                    <td>${p.cpu}</td>
                    <td><span style="color:#00f2fe">${p.memory}</span></td>
                </tr>
            `;
        });
        procBody.innerHTML = html;
    }

    // Generate random response time mock around 120ms
    const rTime = Math.floor(100 + Math.random() * 40);
    responseData.push(rTime);
    responseData.shift();
    responseChartCtx.update();
}

// Fetch loop
async function fetchMetrics() {
    try {
        const res = await fetch('/api/metrics');
        const data = await res.json();
        updateDashboard(data);
    } catch (err) {
        console.error("Error fetching metrics:", err);
    }
}

// Initial fetch and set interval
fetchMetrics();
setInterval(fetchMetrics, 2000); // 2 second polling
