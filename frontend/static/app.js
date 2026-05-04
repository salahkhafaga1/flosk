/**
 * Smart Home Energy Monitor - Dashboard Frontend
 * Features: WebSocket real-time updates, Auth Guard, Device Filtering, AI Diagnostics Panel
 */

// ---------------------------------------------------------------------------
// Configuration
// ---------------------------------------------------------------------------
const WS_URL = `ws://${window.location.host}/ws`;
const API_URL = `${window.location.protocol}//${window.location.host}`;
const STORAGE_KEY = 'smart_home_onboarding';
const APPLIANCE_STORAGE_KEY = 'smart_home_appliances';

// ---------------------------------------------------------------------------
// Auth Guard — redirect to login if not authenticated
// ---------------------------------------------------------------------------
const token = localStorage.getItem('access_token');
if (!token) {
    window.location.href = '/login';
    throw new Error('Authentication required');
}

// Verify token is still valid, check device status, and onboarding status
(async function authGuard() {
    try {
        const res = await fetch(`${API_URL}/device/status`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (!res.ok) {
            localStorage.removeItem('access_token');
            window.location.href = '/login';
            return;
        }
        const data = await res.json();
        if (!data.has_device) {
            window.location.href = '/claim';
            return;
        }
        window.userDeviceId = data.device_id;
        console.log('[Auth] Device claimed:', data.device_id, 'Online:', data.online);

        // Check onboarding status — redirect to wizard if not complete
        const onboardRes = await fetch(`${API_URL}/api/appliances/check`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (onboardRes.ok) {
            const onboardData = await onboardRes.json();
            if (!onboardData.onboarded) {
                window.location.href = '/onboarding';
                return;
            }
        }
    } catch (e) {
        console.error('[Auth] Guard failed:', e);
        window.location.href = '/login';
    }
})();

// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------
let ws = null;
let reconnectTimer = null;
let readingCount = 0;
let selectedAppliances = [];
let lastAlertHash = '';

// Chart instances
let powerChart = null;
let voltageChart = null;

// Keep last 50 data points for charts
const MAX_CHART_POINTS = 50;
const chartData = {
    labels: [],
    power: [],
    voltage: [],
    current: []
};

// ---------------------------------------------------------------------------
// DOM Elements
// ---------------------------------------------------------------------------
const els = {
    status: document.getElementById('connection-status'),
    readingCount: document.getElementById('reading-count'),
    voltage: document.getElementById('val-voltage'),
    current: document.getElementById('val-current'),
    power: document.getElementById('val-power'),
    pf: document.getElementById('val-pf'),
    reactive: document.getElementById('val-reactive'),
    anomaly: document.getElementById('val-anomaly'),
    anomalyStatus: document.getElementById('anomaly-status'),
    anomalyCard: document.getElementById('card-anomaly'),
    tableBody: document.getElementById('telemetry-body'),
    // Modal
    modal: document.getElementById('onboarding-modal'),
    btnSaveAppliances: document.getElementById('btn-save-appliances'),
    btnResetAppliances: document.getElementById('btn-reset-appliances'),
    // Diagnostics
    diagAppliances: document.getElementById('diag-appliances'),
    diagAlerts: document.getElementById('diag-alerts'),
    diagStatus: document.getElementById('diag-status'),
};

// ---------------------------------------------------------------------------
// Onboarding & Appliance Management (RTL Arabic Dynamic Form)
// ---------------------------------------------------------------------------
let onboardingAppliances = []; // Temporary list during onboarding

async function checkOnboardingStatus() {
    try {
        const res = await fetch(`${API_URL}/api/appliances/check`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (res.ok) {
            const data = await res.json();
            return data.onboarded;
        }
    } catch (e) {
        console.warn('[Onboarding] Backend check failed, falling back to localStorage:', e);
    }
    // Fallback to localStorage
    return localStorage.getItem(STORAGE_KEY) === 'complete' && selectedAppliances.length > 0;
}

async function loadAppliancesFromBackend() {
    try {
        const res = await fetch(`${API_URL}/api/appliances`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (res.ok) {
            const data = await res.json();
            selectedAppliances = data.map(item => ({
                name: item.name,
                wattage: item.wattage,
                quantity: item.quantity,
                priority: inferPriority(item.wattage)
            }));
            saveAppliancesToStorage();
            renderApplianceTags();
        }
    } catch (e) {
        console.warn('[Onboarding] Failed to load from backend:', e);
        loadAppliancesFromStorage();
    }
}

function inferPriority(wattage) {
    if (wattage >= 1500) return 'high';
    if (wattage >= 500) return 'medium';
    return 'low';
}

function loadAppliancesFromStorage() {
    try {
        const raw = localStorage.getItem(APPLIANCE_STORAGE_KEY);
        if (raw) {
            selectedAppliances = JSON.parse(raw);
        }
    } catch (e) {
        console.error('[Onboarding] Failed to parse appliances:', e);
        selectedAppliances = [];
    }
}

function saveAppliancesToStorage() {
    localStorage.setItem(APPLIANCE_STORAGE_KEY, JSON.stringify(selectedAppliances));
    localStorage.setItem(STORAGE_KEY, 'complete');
}

function showOnboardingModal() {
    if (els.modal) {
        els.modal.style.display = 'flex';
        onboardingAppliances = [];
        renderOnboardingList();
        resetOnboardingForm();
    }
}

function hideOnboardingModal() {
    if (els.modal) {
        els.modal.style.display = 'none';
    }
}

function resetOnboardingForm() {
    const select = document.getElementById('appliance-select');
    const wattage = document.getElementById('appliance-wattage');
    const quantity = document.getElementById('appliance-quantity');
    if (select) select.value = '';
    if (wattage) wattage.value = '';
    if (quantity) quantity.value = '1';
}

function addOnboardingAppliance() {
    const select = document.getElementById('appliance-select');
    const wattageInput = document.getElementById('appliance-wattage');
    const quantityInput = document.getElementById('appliance-quantity');

    const name = select ? select.value : '';
    const wattage = wattageInput ? parseFloat(wattageInput.value) : 0;
    const quantity = quantityInput ? parseInt(quantityInput.value) : 1;

    if (!name) {
        alert('الرجاء اختيار جهاز من القائمة');
        return;
    }
    if (!wattage || wattage <= 0) {
        alert('الرجاء إدخال استطاعة صحيحة');
        return;
    }
    if (!quantity || quantity < 1) {
        alert('الرجاء إدخال كمية صحيحة');
        return;
    }

    onboardingAppliances.push({ name, wattage, quantity });
    renderOnboardingList();
    resetOnboardingForm();
}

function removeOnboardingAppliance(index) {
    onboardingAppliances.splice(index, 1);
    renderOnboardingList();
}

function renderOnboardingList() {
    const listEl = document.getElementById('appliance-list');
    const totalAppliancesEl = document.getElementById('total-appliances');
    const totalWattageEl = document.getElementById('total-wattage');
    const saveBtn = document.getElementById('btn-save-appliances');

    if (!listEl) return;

    if (onboardingAppliances.length === 0) {
        listEl.innerHTML = '<div class="appliance-list-empty">لم تُضف أي أجهزة بعد. اختر جهازاً من القائمة وأضفه.</div>';
    } else {
        listEl.innerHTML = onboardingAppliances.map((app, idx) => `
            <div class="appliance-list-item">
                <div class="item-info">
                    <span class="item-name">${escapeHtml(app.name)}</span>
                    <span class="item-wattage">${app.wattage} وات</span>
                    <span class="item-meta">× ${app.quantity}</span>
                </div>
                <button class="btn-remove" onclick="removeOnboardingAppliance(${idx})">حذف</button>
            </div>
        `).join('');
    }

    const totalQty = onboardingAppliances.reduce((sum, a) => sum + a.quantity, 0);
    const totalW = onboardingAppliances.reduce((sum, a) => sum + (a.wattage * a.quantity), 0);

    if (totalAppliancesEl) totalAppliancesEl.textContent = `${totalQty} جهاز`;
    if (totalWattageEl) totalWattageEl.textContent = `إجمالي الاستطاعة: ${totalW.toLocaleString()} وات`;
    if (saveBtn) saveBtn.disabled = onboardingAppliances.length === 0;
}

async function saveOnboardingAppliances() {
    if (onboardingAppliances.length === 0) return;

    const payload = {
        appliances: onboardingAppliances.map(a => ({
            name: a.name,
            wattage: a.wattage,
            quantity: a.quantity
        }))
    };

    try {
        const res = await fetch(`${API_URL}/api/appliances`, {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(payload)
        });

        if (!res.ok) throw new Error(`HTTP ${res.status}`);

        const data = await res.json();
        selectedAppliances = data.map(item => ({
            name: item.name,
            wattage: item.wattage,
            quantity: item.quantity,
            priority: inferPriority(item.wattage)
        }));
        saveAppliancesToStorage();
        renderApplianceTags();
        hideOnboardingModal();
        console.log('[Onboarding] Saved', data.length, 'appliances');
    } catch (e) {
        console.error('[Onboarding] Failed to save:', e);
        alert('فشل حفظ الأجهزة. تأكد من تشغيل الخادم وحاول مرة أخرى.');
    }
}

function renderApplianceTags() {
    if (!els.diagAppliances) return;
    if (selectedAppliances.length === 0) {
        els.diagAppliances.innerHTML = '<span class="appliance-tag">لا توجد أجهزة مسجلة</span>';
        return;
    }
    els.diagAppliances.innerHTML = selectedAppliances.map(app => {
        const pClass = `priority-${app.priority}`;
        const wattText = app.wattage ? ` (${app.wattage}W${app.quantity > 1 ? ` ×${app.quantity}` : ''})` : '';
        return `<span class="appliance-tag ${pClass}">${app.name}${wattText}</span>`;
    }).join('');
}

async function initOnboarding() {
    // Onboarding now happens on the standalone /onboarding page.
    // In the dashboard, we just load appliances for diagnostics.
    await loadAppliancesFromBackend();
}

// ---------------------------------------------------------------------------
// AI Diagnostics Engine
// ---------------------------------------------------------------------------
function generateDiagnostics(record) {
    const alerts = [];
    const V = record.V;
    const I = record.I;
    const P = record.P;
    const PF = record.PF;
    const Q = record.Q || 0;
    const score = record.anomaly_score;
    const isAnomaly = record.is_anomaly;

    // --- Critical: Negative anomaly score ---
    if (score !== undefined && score !== null && score < 0) {
        alerts.push({
            severity: 'critical',
            title: '⚠️ Model Integrity Fault',
            message: 'The anomaly detection model is reporting negative scores, which indicates possible model corruption or sensor miscalibration. Please restart the ESP32 and retrain the Isolation Forest model.'
        });
    }

    // --- Critical: Overvoltage ---
    if (V > 250) {
        const affected = selectedAppliances.filter(a => ['Air Conditioner', 'Refrigerator', 'Computer / Server'].includes(a.name));
        const names = affected.length ? affected.map(a => a.name).join(', ') : 'connected appliances';
        alerts.push({
            severity: 'critical',
            title: '🔴 Overvoltage Alert',
            message: `Voltage spike detected (${V.toFixed(1)}V). ${names} are at risk of permanent damage. Disconnect sensitive electronics immediately and check your mains stabilizer.`
        });
    }

    // --- Warning: Undervoltage ---
    if (V < 210) {
        const affected = selectedAppliances.filter(a => ['Air Conditioner', 'Water Pump', 'Refrigerator'].includes(a.name));
        const names = affected.length ? affected.map(a => a.name).join(', ') : 'motor-driven loads';
        alerts.push({
            severity: 'warning',
            title: '🟡 Undervoltage Warning',
            message: `Mains voltage dropped to ${V.toFixed(1)}V. ${names} may stall or overheat due to insufficient torque. Avoid starting heavy loads until voltage stabilizes.`
        });
    }

    // --- Warning: High Current / Overload ---
    if (I > 5.0) {
        const affected = selectedAppliances.filter(a => ['Heater', 'EV Charger', 'Air Conditioner'].includes(a.name));
        const names = affected.length ? affected.map(a => a.name).join(', ') : 'high-wattage loads';
        alerts.push({
            severity: 'warning',
            title: '🟡 Overcurrent Warning',
            message: `Current draw is ${I.toFixed(2)}A — significantly above baseline. Check ${names} for compressor lock-rotor or heating-element short circuits.`
        });
    }

    // --- Info/Warning: Poor Power Factor ---
    if (PF < 0.7) {
        const affected = selectedAppliances.filter(a => ['Air Conditioner', 'Water Pump', 'Washing Machine'].includes(a.name));
        const names = affected.length ? affected.map(a => a.name).join(', ') : 'inductive motors';
        alerts.push({
            severity: 'warning',
            title: '🟡 Low Power Factor',
            message: `Power factor dropped to ${PF.toFixed(2)}. Reactive power is high. ${names} may have failing run capacitors — schedule capacitor-bank inspection.`
        });
    } else if (PF < 0.85) {
        alerts.push({
            severity: 'info',
            title: 'ℹ️ Suboptimal Power Factor',
            message: `Power factor is ${PF.toFixed(2)}. Not critical, but installing a PFC unit can reduce your electricity bill if you have many inductive loads.`
        });
    }

    // --- Info: High Reactive Power ---
    if (Q > 300) {
        alerts.push({
            severity: 'info',
            title: 'ℹ️ High Reactive Power',
            message: `Reactive power is ${Q.toFixed(1)} VAR. This increases apparent power without doing useful work. Consider capacitor compensation for your AC compressor or pump motors.`
        });
    }

    // --- Warning/Critical: Anomaly from ML Model ---
    if (isAnomaly && score > 0.5) {
        // Try to attribute to specific appliances based on signature patterns
        const applianceGuess = inferApplianceFromSignature(V, I, P, PF);
        alerts.push({
            severity: 'critical',
            title: '🤖 ML Anomaly Detected',
            message: `The AI model flagged an unusual electrical signature (score ${score.toFixed(4)}). ${applianceGuess} Possible causes: failing compressor startup capacitor, blocked condenser, or refrigerant leak causing repeated short-cycling.`
        });
    } else if (isAnomaly) {
        alerts.push({
            severity: 'warning',
            title: '🤖 Minor Anomaly',
            message: `Slight deviation from normal operating envelope detected (score ${score.toFixed(4)}). Monitor for trends — if this repeats, check for loose terminals or deteriorating insulation.`
        });
    }

    // --- Info: Appliance-specific idle detection ---
    if (P < 50 && I > 1.0) {
        alerts.push({
            severity: 'info',
            title: 'ℹ️ Phantom Load Detected',
            message: `Low active power (${P.toFixed(1)}W) but measurable current (${I.toFixed(2)}A). A standby device or failing appliance may be drawing reactive current. Check refrigerators in defrost mode or ACs with stuck contactors.`
        });
    }

    return alerts;
}

function inferApplianceFromSignature(V, I, P, PF) {
    const S = V * I;
    const highPower = selectedAppliances.filter(a => ['Air Conditioner', 'Heater', 'EV Charger'].includes(a.name));
    const mediumPower = selectedAppliances.filter(a => ['Washing Machine', 'Water Pump', 'Microwave'].includes(a.name));

    if (P > 1500 && highPower.length > 0) {
        return `Signature matches ${highPower[0].name} under heavy load.`;
    }
    if (P > 500 && mediumPower.length > 0) {
        return `Pattern is consistent with ${mediumPower[0].name} motor startup or heating cycle.`;
    }
    return 'Unable to pinpoint exact appliance without load-disaggregation data.';
}

function renderDiagnostics(alerts) {
    if (!els.diagAlerts) return;

    if (alerts.length === 0) {
        els.diagAlerts.innerHTML = '<div class="diag-placeholder">✅ All systems operating within normal parameters.</div>';
        if (els.diagStatus) {
            els.diagStatus.textContent = 'Healthy';
            els.diagStatus.className = 'diag-badge diag-ok';
        }
        return;
    }

    // Determine overall status
    const hasCritical = alerts.some(a => a.severity === 'critical');
    const hasWarning = alerts.some(a => a.severity === 'warning');

    if (els.diagStatus) {
        if (hasCritical) {
            els.diagStatus.textContent = 'Critical Issue';
            els.diagStatus.className = 'diag-badge diag-critical';
        } else if (hasWarning) {
            els.diagStatus.textContent = 'Attention Needed';
            els.diagStatus.className = 'diag-badge diag-warn';
        } else {
            els.diagStatus.textContent = 'Minor Notes';
            els.diagStatus.className = 'diag-badge diag-ok';
        }
    }

    els.diagAlerts.innerHTML = alerts.map(alert => `
        <div class="diag-alert ${alert.severity}">
            <div class="diag-alert-title">${escapeHtml(alert.title)}</div>
            <div class="diag-alert-body">${escapeHtml(alert.message)}</div>
        </div>
    `).join('');
}

function updateDiagnostics(record) {
    const alerts = generateDiagnostics(record);
    renderDiagnostics(alerts);
}

// ---------------------------------------------------------------------------
// Initialize Charts
// ---------------------------------------------------------------------------
function initCharts() {
    const commonOptions = {
        responsive: true,
        maintainAspectRatio: false,
        animation: { duration: 300 },
        plugins: {
            legend: { labels: { color: '#94a3b8' } }
        },
        scales: {
            x: {
                ticks: { color: '#94a3b8', maxTicksLimit: 8 },
                grid: { color: '#334155' }
            },
            y: {
                ticks: { color: '#94a3b8' },
                grid: { color: '#334155' }
            }
        }
    };

    powerChart = new Chart(document.getElementById('powerChart'), {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Active Power (W)',
                data: [],
                borderColor: '#3b82f6',
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                fill: true,
                tension: 0.4,
                pointRadius: 0
            }]
        },
        options: {
            ...commonOptions,
            interaction: { intersect: false, mode: 'index' }
        }
    });

    voltageChart = new Chart(document.getElementById('voltageChart'), {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'Voltage (V)',
                    data: [],
                    borderColor: '#22c55e',
                    backgroundColor: 'rgba(34, 197, 94, 0.1)',
                    fill: true,
                    tension: 0.4,
                    pointRadius: 0,
                    yAxisID: 'y'
                },
                {
                    label: 'Current (A)',
                    data: [],
                    borderColor: '#eab308',
                    backgroundColor: 'rgba(234, 179, 8, 0.1)',
                    fill: true,
                    tension: 0.4,
                    pointRadius: 0,
                    yAxisID: 'y1'
                }
            ]
        },
        options: {
            ...commonOptions,
            scales: {
                ...commonOptions.scales,
                y: {
                    ...commonOptions.scales.y,
                    position: 'left',
                    title: { display: true, text: 'Voltage (V)', color: '#22c55e' }
                },
                y1: {
                    position: 'right',
                    ticks: { color: '#eab308' },
                    grid: { drawOnChartArea: false },
                    title: { display: true, text: 'Current (A)', color: '#eab308' }
                }
            }
        }
    });
}

// ---------------------------------------------------------------------------
// Update Dashboard UI
// ---------------------------------------------------------------------------
function updateMetrics(record) {
    els.voltage.textContent = formatNumber(record.V, 1);
    els.current.textContent = formatNumber(record.I, 3);
    els.power.textContent = formatNumber(record.P, 1);
    els.pf.textContent = formatNumber(record.PF, 3);
    els.reactive.textContent = formatNumber(record.Q, 1);

    const score = record.anomaly_score;
    const isAnomaly = record.is_anomaly;

    if (score !== undefined && score !== null) {
        els.anomaly.textContent = score.toFixed(4);
    } else {
        els.anomaly.textContent = '--';
    }

    if (isAnomaly) {
        els.anomalyStatus.textContent = '⚠️ ANOMALY DETECTED';
        els.anomalyStatus.style.color = '#ef4444';
        els.anomalyCard.classList.add('alert');
    } else {
        els.anomalyStatus.textContent = 'Normal';
        els.anomalyStatus.style.color = '#22c55e';
        els.anomalyCard.classList.remove('alert');
    }
}

function updateCharts(record) {
    const time = new Date().toLocaleTimeString('en-US', {
        hour12: false,
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });

    chartData.labels.push(time);
    chartData.power.push(record.P);
    chartData.voltage.push(record.V);
    chartData.current.push(record.I);

    if (chartData.labels.length > MAX_CHART_POINTS) {
        chartData.labels.shift();
        chartData.power.shift();
        chartData.voltage.shift();
        chartData.current.shift();
    }

    powerChart.data.labels = chartData.labels;
    powerChart.data.datasets[0].data = chartData.power;
    powerChart.update('none');

    voltageChart.data.labels = chartData.labels;
    voltageChart.data.datasets[0].data = chartData.voltage;
    voltageChart.data.datasets[1].data = chartData.current;
    voltageChart.update('none');
}

function addTableRow(record) {
    const emptyRow = els.tableBody.querySelector('.empty-row');
    if (emptyRow) {
        emptyRow.remove();
    }

    const row = document.createElement('tr');
    const isAnomaly = record.is_anomaly;
    if (isAnomaly) {
        row.classList.add('anomaly-row');
    }

    const timeStr = record.timestamp
        ? new Date(record.timestamp).toLocaleTimeString()
        : new Date().toLocaleTimeString();

    row.innerHTML = `
        <td>${timeStr}</td>
        <td>${escapeHtml(record.device_id || 'unknown')}</td>
        <td>${formatNumber(record.V, 1)}</td>
        <td>${formatNumber(record.I, 3)}</td>
        <td>${formatNumber(record.P, 1)}</td>
        <td>${formatNumber(record.PF, 3)}</td>
        <td>${record.anomaly_score !== undefined ? record.anomaly_score.toFixed(4) : '--'}</td>
        <td>${isAnomaly ? '🔴 Anomaly' : '🟢 Normal'}</td>
    `;

    els.tableBody.insertBefore(row, els.tableBody.firstChild);

    while (els.tableBody.children.length > 50) {
        els.tableBody.removeChild(els.tableBody.lastChild);
    }
}

// ---------------------------------------------------------------------------
// WebSocket Connection (with device filtering)
// ---------------------------------------------------------------------------
function connectWebSocket() {
    if (ws && (ws.readyState === WebSocket.CONNECTING || ws.readyState === WebSocket.OPEN)) {
        return;
    }

    updateStatus('connecting');

    ws = new WebSocket(WS_URL);

    ws.onopen = () => {
        console.log('[WS] Connected');
        updateStatus('connected');
        if (reconnectTimer) {
            clearTimeout(reconnectTimer);
            reconnectTimer = null;
        }
    };

    ws.onmessage = (event) => {
        try {
            const msg = JSON.parse(event.data);

            if (msg.type === 'history') {
                // Filter history by user's device
                const filtered = msg.data.filter(r => r.device_id === window.userDeviceId);
                filtered.forEach(record => {
                    updateMetrics(record);
                    updateCharts(record);
                    updateDiagnostics(record);
                });
                return;
            }

            if (msg.type === 'pong') {
                return;
            }

            // Filter real-time data by user's claimed device
            if (msg.device_id && msg.device_id !== window.userDeviceId) {
                return; // Ignore data from other devices
            }

            readingCount++;
            els.readingCount.textContent = `Readings: ${readingCount}`;

            updateMetrics(msg);
            updateCharts(msg);
            addTableRow(msg);
            updateDiagnostics(msg);

        } catch (err) {
            console.error('[WS] Failed to parse message:', err);
        }
    };

    ws.onerror = (err) => {
        console.error('[WS] Error:', err);
        updateStatus('error');
    };

    ws.onclose = () => {
        console.log('[WS] Disconnected');
        updateStatus('disconnected');
        reconnectTimer = setTimeout(connectWebSocket, 3000);
    };
}

function updateStatus(state) {
    const statusMap = {
        connected: { text: 'Connected', class: 'connected' },
        connecting: { text: 'Connecting...', class: 'disconnected' },
        disconnected: { text: 'Disconnected', class: 'disconnected' },
        error: { text: 'Error', class: 'disconnected' }
    };

    const info = statusMap[state] || statusMap.disconnected;
    els.status.textContent = info.text;
    els.status.className = 'badge ' + info.class;
}

// ---------------------------------------------------------------------------
// Utility Functions
// ---------------------------------------------------------------------------
function formatNumber(value, decimals) {
    if (value === undefined || value === null || isNaN(value)) {
        return '--';
    }
    return Number(value).toFixed(decimals);
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ---------------------------------------------------------------------------
// Heartbeat
// ---------------------------------------------------------------------------
setInterval(() => {
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send('ping');
    }
}, 30000);

// ---------------------------------------------------------------------------
// Boot
// ---------------------------------------------------------------------------
document.addEventListener('DOMContentLoaded', () => {
    initOnboarding();
    initCharts();
    connectWebSocket();
});
