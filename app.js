/**
 * Hybrid Edge-to-Cloud Visual Intelligence
 * Worker Operational Safety — Frontend Controller
 */

// ─── Socket.IO Connection ─────────────────────────────────
const socket = io();

// ─── DOM Elements ─────────────────────────────────────────
const els = {
    // Nav
    connStatus: document.getElementById('conn-status'),
    uptimeDisp: document.getElementById('uptime-display'),
    tickCount: document.getElementById('tick-count'),
    
    // Canvas Map
    canvas: document.getElementById('floor-canvas'),
    btnFov: document.getElementById('btn-toggle-fov'),
    btnZones: document.getElementById('btn-toggle-zones'),
    
    // Workers
    workerGrid: document.getElementById('worker-grid'),
    wsCompliant: document.getElementById('ws-compliant'),
    wsViolations: document.getElementById('ws-violations'),
    
    // Sensors
    sensorGrid: document.getElementById('sensor-grid'),
    envZoneSelect: document.getElementById('env-zone-select'),
    
    // Edge & Cloud
    edgeGrid: document.getElementById('edge-grid'),
    cloudMetrics: document.getElementById('cloud-metrics'),
    
    // Alerts
    alertList: document.getElementById('alert-list'),
    acCritical: document.getElementById('ac-critical'),
    acHigh: document.getElementById('ac-high'),
    acMedium: document.getElementById('ac-medium'),
    btnClearAlerts: document.getElementById('btn-clear-alerts'),
    
    // Analytics
    aTotalWorkers: document.getElementById('analytics-total-workers'),
    aPpeRate: document.getElementById('analytics-ppe-rate'),
    aAvgFatigue: document.getElementById('analytics-avg-fatigue'),
    aEdgeFps: document.getElementById('analytics-edge-fps'),
    aCloudLatency: document.getElementById('analytics-cloud-latency'),
    aDetections: document.getElementById('analytics-detections'),
    aDataPoints: document.getElementById('analytics-data-points'),
    aModelAcc: document.getElementById('analytics-model-acc'),
};

// ─── State ────────────────────────────────────────────────
let sysState = null;
let mapSettings = { showFov: true, showZones: true };
let ctx = els.canvas.getContext('2d');
let charts = {};

// ─── Initialization ───────────────────────────────────────
function init() {
    initCharts();
    setupEventListeners();
}

function initCharts() {
    // Cloud Latency Chart
    const ctxLatency = document.getElementById('latency-chart').getContext('2d');
    charts.latency = new Chart(ctxLatency, {
        type: 'line',
        data: {
            labels: Array(20).fill(''),
            datasets: [{
                label: 'Cloud Latency (ms)',
                data: Array(20).fill(0),
                borderColor: '#448aff',
                backgroundColor: 'rgba(68, 138, 255, 0.1)',
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
                y: { 
                    display: true, 
                    grid: { color: 'rgba(255,255,255,0.05)' },
                    ticks: { color: '#9fa8da', font: { size: 10 } }
                }
            }
        }
    });

    // Analytics Chart
    const ctxPpe = document.getElementById('ppe-chart').getContext('2d');
    charts.ppe = new Chart(ctxPpe, {
        type: 'bar',
        data: {
            labels: ['Helmet', 'Vest', 'Goggles', 'Gloves', 'Boots'],
            datasets: [{
                label: 'Compliance %',
                data: [100, 100, 100, 100, 100],
                backgroundColor: 'rgba(105, 240, 174, 0.6)',
                borderColor: '#69f0ae',
                borderWidth: 1,
                borderRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                x: { grid: { display: false }, ticks: { color: '#9fa8da', font: { size: 10 } } },
                y: { min: 0, max: 100, grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#9fa8da', font: { size: 10 } } }
            }
        }
    });
}

function setupEventListeners() {
    els.btnFov.addEventListener('click', () => {
        mapSettings.showFov = !mapSettings.showFov;
        els.btnFov.classList.toggle('active', mapSettings.showFov);
        renderMap();
    });
    
    els.btnZones.addEventListener('click', () => {
        mapSettings.showZones = !mapSettings.showZones;
        els.btnZones.classList.toggle('active', mapSettings.showZones);
        renderMap();
    });

    els.envZoneSelect.addEventListener('change', () => {
        if(sysState) renderSensors(sysState.env_sensors[els.envZoneSelect.value]);
    });

    els.btnClearAlerts.addEventListener('click', () => {
        socket.emit('clear_alerts');
    });

    document.querySelectorAll('.btn-incident').forEach(btn => {
        btn.addEventListener('click', () => {
            const type = btn.getAttribute('data-type');
            socket.emit('trigger_incident', { type: type });
        });
    });
}

// ─── Socket Events ────────────────────────────────────────
socket.on('connect', () => {
    els.connStatus.classList.remove('disconnected');
    els.connStatus.classList.add('online');
    els.connStatus.querySelector('.status-label').textContent = 'Live';
});

socket.on('disconnect', () => {
    els.connStatus.classList.remove('online');
    els.connStatus.classList.add('disconnected');
    els.connStatus.querySelector('.status-label').textContent = 'Offline';
});

socket.on('init_state', (state) => {
    sysState = state;
    
    // Setup environment dropdown
    els.envZoneSelect.innerHTML = '';
    state.zones.forEach(z => {
        const opt = document.createElement('option');
        opt.value = z.id;
        opt.textContent = z.name;
        els.envZoneSelect.appendChild(opt);
    });

    updateUI(state);
});

socket.on('realtime_update', (update) => {
    if (!sysState) return;
    
    // Merge update into full state
    sysState.workers = update.workers;
    sysState.cameras = update.cameras;
    sysState.env_sensors = update.env_sensors;
    sysState.cloud = update.cloud;
    sysState.alerts = update.alerts;
    sysState.alert_stats = update.alert_stats;
    sysState.uptime = update.uptime;
    sysState.tick = update.tick;

    updateUI(sysState);
});

socket.on('alert_acknowledged', (data) => {
    const el = document.getElementById(`alert-${data.id}`);
    if (el) {
        el.classList.add('acknowledged');
        const btn = el.querySelector('.alert-ack-btn');
        if(btn) btn.remove();
    }
});

socket.on('alerts_cleared', () => {
    sysState.alerts = [];
    sysState.alert_stats = {total: 0, by_level: {}};
    renderAlerts();
});

// ─── UI Updaters ──────────────────────────────────────────
function formatTime(seconds) {
    const h = Math.floor(seconds / 3600).toString().padStart(2, '0');
    const m = Math.floor((seconds % 3600) / 60).toString().padStart(2, '0');
    const s = (seconds % 60).toString().padStart(2, '0');
    return `${h}:${m}:${s}`;
}

function updateUI(state) {
    els.uptimeDisp.textContent = formatTime(state.uptime);
    els.tickCount.textContent = state.tick;

    renderMap();
    renderWorkers(state.workers);
    renderSensors(state.env_sensors[els.envZoneSelect.value]);
    renderEdgeNodes(state.cameras);
    renderCloudMetrics(state.cloud);
    renderAlerts(state);
    updateCharts(state);
    updateAnalytics(state);
}

// ─── Map Rendering ────────────────────────────────────────
function renderMap() {
    if (!sysState || !sysState.zones) return;
    
    const w = els.canvas.width;
    const h = els.canvas.height;
    
    ctx.clearRect(0, 0, w, h);
    
    // Draw Grid
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.05)';
    ctx.lineWidth = 1;
    for(let i=0; i<w; i+=40) { ctx.beginPath(); ctx.moveTo(i, 0); ctx.lineTo(i, h); ctx.stroke(); }
    for(let i=0; i<h; i+=40) { ctx.beginPath(); ctx.moveTo(0, i); ctx.lineTo(w, i); ctx.stroke(); }

    // Draw Zones
    if (mapSettings.showZones) {
        sysState.zones.forEach(z => {
            // Fill
            ctx.fillStyle = z.color + '15'; // 15 = ~8% opacity hex
            ctx.fillRect(z.x, z.y, z.w, z.h);
            
            // Border
            ctx.strokeStyle = z.color + '60';
            ctx.lineWidth = 1;
            ctx.setLineDash([5, 5]);
            ctx.strokeRect(z.x, z.y, z.w, z.h);
            ctx.setLineDash([]);
            
            // Label
            ctx.fillStyle = z.color;
            ctx.font = '10px JetBrains Mono';
            ctx.fillText(z.name, z.x + 5, z.y + 15);
        });
    }

    // Draw Camera FOV
    if (mapSettings.showFov) {
        sysState.cameras.forEach(cam => {
            if (!cam.is_online) return;
            ctx.beginPath();
            ctx.arc(cam.x, cam.y, cam.fov_radius, 0, Math.PI * 2);
            const gradient = ctx.createRadialGradient(cam.x, cam.y, 0, cam.x, cam.y, cam.fov_radius);
            gradient.addColorStop(0, 'rgba(124, 77, 255, 0.15)');
            gradient.addColorStop(1, 'rgba(124, 77, 255, 0)');
            ctx.fillStyle = gradient;
            ctx.fill();
            
            // FOV border
            ctx.beginPath();
            ctx.arc(cam.x, cam.y, cam.fov_radius, 0, Math.PI * 2);
            ctx.strokeStyle = 'rgba(124, 77, 255, 0.2)';
            ctx.lineWidth = 1;
            ctx.stroke();
        });
    }

    // Draw Cameras
    sysState.cameras.forEach(cam => {
        ctx.fillStyle = cam.is_online ? '#7c4dff' : '#ff5252';
        ctx.beginPath();
        ctx.moveTo(cam.x, cam.y - 8);
        ctx.lineTo(cam.x + 8, cam.y + 8);
        ctx.lineTo(cam.x - 8, cam.y + 8);
        ctx.fill();
        
        ctx.fillStyle = '#fff';
        ctx.font = '10px sans-serif';
        ctx.fillText(cam.name, cam.x + 12, cam.y + 4);
    });

    // Draw Workers
    sysState.workers.forEach(w => {
        // Draw Worker Dot
        ctx.fillStyle = w.ppe_compliance ? '#00e5ff' : '#ffab40';
        if (!w.posture_ok || w.fatigue_score > 0.8) ctx.fillStyle = '#ff5252';
        
        ctx.beginPath();
        ctx.arc(w.x, w.y, 6, 0, Math.PI * 2);
        ctx.fill();
        
        // Draw bounding box if detected by a camera
        const isDetected = sysState.cameras.some(c => 
            c.is_online && c.detections.some(d => d.worker_id === w.id)
        );
        
        if (isDetected) {
            ctx.strokeStyle = w.ppe_compliance ? 'rgba(0, 229, 255, 0.5)' : 'rgba(255, 82, 82, 0.8)';
            ctx.lineWidth = 1.5;
            ctx.strokeRect(w.x - 12, w.y - 18, 24, 34);
            
            // Confidence little bar
            ctx.fillStyle = 'rgba(0, 229, 255, 0.8)';
            ctx.fillRect(w.x - 12, w.y - 22, 24 * 0.95, 3);
        }

        // Label
        ctx.fillStyle = '#e8eaf6';
        ctx.font = '9px sans-serif';
        ctx.fillText(w.id, w.x - 10, w.y + 16);
    });
}

// ─── Worker Cards ─────────────────────────────────────────
function renderWorkers(workers) {
    if (!workers) return;
    
    let comp = 0;
    let viol = 0;
    
    els.workerGrid.innerHTML = workers.map(w => {
        if (w.ppe_compliance) comp++; else viol++;
        
        const ppeHtml = Object.entries(w.ppe).map(([item, worn]) => 
            `<span class="ppe-badge ${worn ? 'ok' : 'missing'}">${item}</span>`
        ).join('');
        
        const cardClass = w.ppe_compliance && w.posture_ok ? '' : 'violation';
        
        return `
            <div class="worker-card ${cardClass}">
                <div class="wc-header">
                    <span class="wc-name">${w.name}</span>
                    <span class="wc-id">${w.id}</span>
                </div>
                <div class="wc-role">${w.role}</div>
                <div class="wc-vitals">
                    <div class="wc-vital">
                        <div class="wc-vital-value" style="color: ${w.heart_rate > 100 ? '#ff5252' : '#00e5ff'}">${w.heart_rate}</div>
                        <div class="wc-vital-label">BPM</div>
                    </div>
                    <div class="wc-vital">
                        <div class="wc-vital-value">${w.body_temp}°</div>
                        <div class="wc-vital-label">Temp</div>
                    </div>
                    <div class="wc-vital">
                        <div class="wc-vital-value" style="color: ${w.fatigue_score > 0.7 ? '#ffab40' : '#00e5ff'}">${Math.round(w.fatigue_score * 100)}%</div>
                        <div class="wc-vital-label">Fatigue</div>
                    </div>
                </div>
                <div class="wc-ppe">${ppeHtml}</div>
                <div class="wc-zone">📍 ${sysState.zones.find(z => z.id === w.current_zone)?.name || 'Transit'}</div>
            </div>
        `;
    }).join('');

    els.wsCompliant.textContent = comp;
    els.wsViolations.textContent = viol;
}

// ─── Sensor Gauges ────────────────────────────────────────
function renderSensors(sensorData) {
    if (!sensorData || !sensorData.sensors) {
        els.sensorGrid.innerHTML = '<p class="text-muted" style="grid-column: 1/-1;">No sensor data for select zone.</p>';
        return;
    }
    
    const icons = {
        temperature: '🌡️', humidity: '💧', gas_co: '☠️', gas_h2s: '🧪',
        noise: '🔊', vibration: '📳', dust_pm25: '🌫️'
    };

    els.sensorGrid.innerHTML = Object.entries(sensorData.sensors).map(([key, data]) => {
        const pct = Math.min(100, Math.max(0, (data.value / (data.threshold_critical * 1.2)) * 100));
        
        return `
            <div class="sensor-card ${data.status}">
                <div class="sensor-icon">${icons[key] || '📊'}</div>
                <div class="sensor-value">${data.value}</div>
                <div class="sensor-unit">${data.unit}</div>
                <div class="sensor-name">${key.replace('_', ' ')}</div>
                <div class="sensor-bar">
                    <div class="sensor-bar-fill" style="width: ${pct}%"></div>
                </div>
            </div>
        `;
    }).join('');
}

// ─── Edge Nodes ───────────────────────────────────────────
function renderEdgeNodes(cameras) {
    if (!cameras) return;
    
    els.edgeGrid.innerHTML = cameras.map(cam => {
        return `
            <div class="edge-card ${!cam.is_online ? 'offline' : ''}">
                <div class="ec-header">
                    <span class="ec-name">${cam.name}</span>
                    <span class="ec-status"></span>
                </div>
                <div class="ec-metrics">
                    <div class="ec-metric">
                        <div class="ec-metric-value">${cam.fps}</div>
                        <div class="ec-metric-label">FPS</div>
                    </div>
                    <div class="ec-metric">
                        <div class="ec-metric-value">${cam.inference_ms}ms</div>
                        <div class="ec-metric-label">Infer</div>
                    </div>
                    <div class="ec-metric">
                        <div class="ec-metric-value">${cam.gpu_util}%</div>
                        <div class="ec-metric-label">GPU</div>
                    </div>
                    <div class="ec-metric">
                        <div class="ec-metric-value">${cam.power_w}W</div>
                        <div class="ec-metric-label">Power</div>
                    </div>
                </div>
                <div class="ec-detections">🎯 Detected: ${cam.detection_count} persons</div>
                <button class="btn-sm" style="width:100%; margin-top:8px;" onclick="toggleCamera('${cam.id}')">
                    ${cam.is_online ? 'Disable Node' : 'Enable Node'}
                </button>
            </div>
        `;
    }).join('');
}

window.toggleCamera = function(id) {
    socket.emit('toggle_camera', { camera_id: id });
}

// ─── Cloud Metrics ────────────────────────────────────────
function renderCloudMetrics(cloud) {
    if (!cloud) return;
    
    els.cloudMetrics.innerHTML = `
        <div class="cm-card">
            <div class="cm-value">${cloud.latency_ms}ms</div>
            <div class="cm-label">Latency</div>
        </div>
        <div class="cm-card">
            <div class="cm-value">${cloud.bandwidth_mbps}</div>
            <div class="cm-label">Mbps</div>
        </div>
        <div class="cm-card">
            <div class="cm-value">${cloud.packet_loss_pct}%</div>
            <div class="cm-label">Pkt Loss</div>
        </div>
        <div class="cm-card">
            <div class="cm-value">${cloud.cloud_cpu}%</div>
            <div class="cm-label">Cloud CPU</div>
        </div>
    `;
}

// ─── Alerts ───────────────────────────────────────────────
function renderAlerts() {
    if (!sysState || !sysState.alerts) return;

    const stats = sysState.alert_stats?.by_level || {};
    els.acCritical.textContent = stats.critical || 0;
    els.acHigh.textContent = stats.high || 0;
    els.acMedium.textContent = stats.medium || 0;

    if (sysState.alerts.length === 0) {
        els.alertList.innerHTML = '<p class="text-muted" style="text-align:center; padding: 20px;">No active alerts. System nominal.</p>';
        return;
    }

    els.alertList.innerHTML = sysState.alerts.map(a => `
        <div class="alert-item level-${a.level} ${a.acknowledged ? 'acknowledged' : ''}" id="alert-${a.id}">
            <div class="alert-level ${a.level}">${a.level}</div>
            <div class="alert-body">
                <div class="alert-category">${a.category}</div>
                <div class="alert-message">${a.message}</div>
                <div style="display:flex; justify-content:space-between; align-items:center; margin-top:6px;">
                    <span class="alert-time">${a.timestamp} | Src: ${a.source}</span>
                    ${!a.acknowledged ? `<button class="alert-ack-btn" onclick="ackAlert(${a.id})">Acknowledge</button>` : ''}
                </div>
            </div>
        </div>
    `).join('');
}

window.ackAlert = function(id) {
    socket.emit('acknowledge_alert', { id: id });
}

// ─── Charts & Analytics ───────────────────────────────────
function updateCharts(state) {
    // Latency Line Chart
    const d = charts.latency.data.datasets[0].data;
    d.shift();
    d.push(state.cloud.latency_ms);
    charts.latency.update();

    // PPE Compliance Bar Chart
    const ppeStats = { helmet:0, vest:0, goggles:0, gloves:0, boots:0 };
    let total = state.workers.length;
    
    state.workers.forEach(w => {
        if(w.ppe.helmet) ppeStats.helmet++;
        if(w.ppe.vest) ppeStats.vest++;
        if(w.ppe.goggles) ppeStats.goggles++;
        if(w.ppe.gloves) ppeStats.gloves++;
        if(w.ppe.boots) ppeStats.boots++;
    });

    charts.ppe.data.datasets[0].data = [
        (ppeStats.helmet/total)*100,
        (ppeStats.vest/total)*100,
        (ppeStats.goggles/total)*100,
        (ppeStats.gloves/total)*100,
        (ppeStats.boots/total)*100
    ];
    charts.ppe.update();
}

function updateAnalytics(state) {
    els.aTotalWorkers.textContent = state.workers.length;
    
    const compliant = state.workers.filter(w => w.ppe_compliance).length;
    els.aPpeRate.textContent = Math.round((compliant / state.workers.length) * 100) + '%';
    
    const avgFatigue = state.workers.reduce((acc, w) => acc + w.fatigue_score, 0) / state.workers.length;
    els.aAvgFatigue.textContent = Math.round(avgFatigue * 100) + '%';
    
    const onlineCams = state.cameras.filter(c => c.is_online);
    const avgFps = onlineCams.reduce((acc, c) => acc + c.fps, 0) / (onlineCams.length || 1);
    els.aEdgeFps.textContent = avgFps.toFixed(1);
    
    els.aCloudLatency.textContent = state.cloud.latency_ms + 'ms';
    
    const dcount = state.cameras.reduce((acc, c) => acc + c.detection_count, 0);
    els.aDetections.textContent = dcount;
    
    els.aDataPoints.textContent = state.cloud.data_points.toLocaleString();
    els.aModelAcc.textContent = Math.round(state.cloud.model_accuracy * 100 * 10) / 10 + '%';
}

// ─── Boot ─────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', init);
