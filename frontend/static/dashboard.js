/**
 * فلوسك — Business Dashboard Frontend
 * RTL Arabic Dark Mode Dashboard with WebSocket real-time updates
 */

// ---------------------------------------------------------------------------
// Configuration
// ---------------------------------------------------------------------------
const WS_URL = `ws://${window.location.host}/ws`;
const API_URL = `${window.location.protocol}//${window.location.host}`;

// ---------------------------------------------------------------------------
// Auth Guard & User Info
// ---------------------------------------------------------------------------
const token = localStorage.getItem('access_token');
if (!token) {
    window.location.href = '/login';
    throw new Error('Authentication required');
}

async function initUser() {
    try {
        const res = await fetch(`${API_URL}/auth/me`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (res.ok) {
            const userData = await res.json();
            const emailEl = document.getElementById('user-email');
            if (emailEl) emailEl.textContent = userData.email;
        }
    } catch (e) {}
}
initUser();

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

        // Check onboarding
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

        // Load appliances for health counts
        await loadAppliances();
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
let totalKwh = 0;
let monthlyCost = 0;
let alertActive = false;
let alertDismissed = false;
let appliances = [];

// Egyptian electricity tiers (EGP/kWh)
const TIERS = [
    { limit: 50,  price: 0.58,  name: Lang.t('tier-1') },
    { limit: 100, price: 0.88,  name: Lang.t('tier-2') },
    { limit: 200, price: 1.18, name: Lang.t('tier-3') },
    { limit: 350, price: 1.48, name: Lang.t('tier-4') },
    { limit: 650, price: 1.88, name: Lang.t('tier-5') },
    { limit: 1000, price: 2.38, name: Lang.t('tier-6') },
    { limit: Infinity, price: 2.88, name: Lang.t('tier-7') },
];

// ---------------------------------------------------------------------------
// Appliance Loading
// ---------------------------------------------------------------------------
async function loadAppliances() {
    try {
        const res = await fetch(`${API_URL}/api/appliances`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (res.ok) {
            appliances = await res.json();
            updateHealthCounts();
        }
    } catch (e) {
        console.warn('[Dashboard] Failed to load appliances:', e);
    }
}

function updateHealthCounts() {
    const healthy = appliances.length;
    document.getElementById('healthy-count').textContent = healthy;
    document.getElementById('warning-count').textContent = '0';
    document.getElementById('critical-count').textContent = '0';
}

// ---------------------------------------------------------------------------
// WebSocket Connection
// ---------------------------------------------------------------------------
function connectWebSocket() {
    if (ws && (ws.readyState === WebSocket.CONNECTING || ws.readyState === WebSocket.OPEN)) {
        return;
    }

    updateConnectionStatus('connecting');

    ws = new WebSocket(WS_URL);

    ws.onopen = () => {
        console.log('[WS] Connected');
        updateConnectionStatus('connected');
        if (reconnectTimer) {
            clearTimeout(reconnectTimer);
            reconnectTimer = null;
        }
    };

    ws.onmessage = (event) => {
        try {
            const msg = JSON.parse(event.data);

            if (msg.type === 'history') {
                // Process history (last 20 readings)
                const filtered = msg.data.filter(r => r.device_id === window.userDeviceId);
                filtered.forEach(record => processReading(record));
                return;
            }

            if (msg.type === 'pong') return;

            // Filter by user's device
            if (msg.device_id && msg.device_id !== window.userDeviceId) return;

            processReading(msg);

        } catch (err) {
            console.error('[WS] Parse error:', err);
        }
    };

    ws.onerror = () => {
        updateConnectionStatus('error');
    };

    ws.onclose = () => {
        updateConnectionStatus('disconnected');
        reconnectTimer = setTimeout(connectWebSocket, 3000);
    };
}

function updateConnectionStatus(state) {
    const dot = document.getElementById('ws-status-dot');
    const text = document.getElementById('ws-status-text');
    if (!dot || !text) return;

    const states = {
        connected:    { color: 'bg-emerald-500', text: Lang.t('ws-status-connected') },
        connecting:   { color: 'bg-amber-500',   text: Lang.t('ws-status-connecting') },
        disconnected: { color: 'bg-red-500',     text: Lang.t('ws-status-disconnected') },
        error:        { color: 'bg-red-500',     text: Lang.t('ws-status-error') },
    };

    const s = states[state] || states.disconnected;
    dot.className = `w-2 h-2 rounded-full ${s.color} live-dot`;
    text.textContent = s.text;
}

// ---------------------------------------------------------------------------
// Process Incoming Reading
// ---------------------------------------------------------------------------
function processReading(record) {
    readingCount++;

    // Update live metrics
    updateLiveMetrics(record);

    // Accumulate energy (approximate: P watts * 1 second / 3600 = Wh)
    if (record.P && !isNaN(record.P)) {
        totalKwh += record.P / 1000 / 3600;
    }

    // Update cost & tier
    updateCostAndTier();

    // Check for anomaly
    if (record.is_anomaly && !alertDismissed) {
        showAIAlert(record);
    }

    // Add to activity log
    addActivityLog(record);
}

function updateLiveMetrics(record) {
    const v = document.getElementById('live-voltage');
    const i = document.getElementById('live-current');
    const p = document.getElementById('live-power');
    const pf = document.getElementById('live-pf');

    if (v) v.textContent = formatNumber(record.V, 1);
    if (i) i.textContent = formatNumber(record.I, 3);
    if (p) p.textContent = formatNumber(record.P, 1);
    if (pf) pf.textContent = formatNumber(record.PF, 3);
}

// ---------------------------------------------------------------------------
// Cost & Tier Calculation
// ---------------------------------------------------------------------------
function updateCostAndTier() {
    // Calculate cost based on Egyptian tier system
    let remainingKwh = totalKwh;
    let cost = 0;
    let currentTier = TIERS[0];
    let tierConsumed = 0;
    let tierLimit = TIERS[0].limit;

    for (const tier of TIERS) {
        if (remainingKwh <= 0) break;
        const consumed = Math.min(remainingKwh, tier.limit - (TIERS.indexOf(tier) > 0 ? TIERS[TIERS.indexOf(tier) - 1].limit : 0));
        cost += consumed * tier.price;
        remainingKwh -= consumed;
        if (remainingKwh > 0) {
            currentTier = TIERS[TIERS.indexOf(tier) + 1] || tier;
        } else {
            currentTier = tier;
            tierConsumed = consumed;
            tierLimit = tier.limit - (TIERS.indexOf(tier) > 0 ? TIERS[TIERS.indexOf(tier) - 1].limit : 0);
        }
    }

    monthlyCost = Math.round(cost);

    // Update DOM
    const costEl = document.getElementById('cost-value');
    const costBar = document.getElementById('cost-bar');
    const costPercent = document.getElementById('cost-percent');
    const tierName = document.getElementById('tier-name');
    const tierProgress = document.getElementById('tier-progress');
    const tierCurrent = document.getElementById('tier-current');
    const tierRemaining = document.getElementById('tier-remaining');
    const tierRange = document.getElementById('tier-range');
    const tierPrice = document.getElementById('tier-price');
    const tierMin = document.getElementById('tier-min');
    const tierMax = document.getElementById('tier-max');

    if (costEl) costEl.textContent = monthlyCost.toLocaleString();
    if (tierName) tierName.textContent = currentTier.name;

    // Calculate tier progress
    const tierStart = TIERS.indexOf(currentTier) > 0 ? TIERS[TIERS.indexOf(currentTier) - 1].limit : 0;
    const tierMax = currentTier.limit === Infinity ? tierStart + 200 : currentTier.limit;
    const inTier = totalKwh - tierStart;
    const tierPct = Math.min((inTier / (tierMax - tierStart)) * 100, 100);

    if (tierProgress) tierProgress.style.width = `${tierPct}%`;
    if (tierCurrent) tierCurrent.textContent = `${Math.round(totalKwh)} ${Lang.t('unit-kwh')}`;
    if (tierRemaining) tierRemaining.textContent = `${Math.round(Math.max(0, tierMax - totalKwh))} ${Lang.t('unit-kwh')}`;

    const kwhUnit = Lang.t('unit-kwh');
    const currency = Lang.t('cost-currency');

    if (tierRange) {
        tierRange.innerHTML = currentTier.limit === Infinity ? `${tierStart}+ ${kwhUnit}` : `${tierStart} &rarr; ${currentTier.limit} ${kwhUnit}`;
    }
    if (tierPrice) {
        tierPrice.textContent = `${currentTier.price} ${currency}/${kwhUnit}`;
    }
    if (tierMin) tierMin.textContent = tierStart;
    if (tierMax) {
        tierMax.textContent = currentTier.limit === Infinity ? '+' : `${currentTier.limit} ${kwhUnit}`;
    }

    // Cost bar (arbitrary max of 500 EGP for visualization)
    const costPct = Math.min((monthlyCost / 500) * 100, 100);
    if (costBar) costBar.style.width = `${costPct}%`;
    if (costPercent) costPercent.textContent = `${Math.round(costPct)}%`;
}

// ---------------------------------------------------------------------------
// AI Alert
// ---------------------------------------------------------------------------
function showAIAlert(record) {
    if (alertActive) return;

    const card = document.getElementById('ai-alert-card');
    const msg = document.getElementById('ai-alert-message');
    const time = document.getElementById('ai-alert-time');

    if (!card) return;

    // Determine alert message based on reading
    let alertText = 'التكييف بيسحب طاقة أكتر من المعتاد - يُنصح بالصيانة';
    if (record.V > 250) {
        alertText = Lang.t('alert-voltage-high').replace('{v}', record.V.toFixed(1));
    } else if (record.V < 210) {
        alertText = Lang.t('alert-voltage-low').replace('{v}', record.V.toFixed(1));
    } else if (record.I > 5) {
        alertText = Lang.t('alert-current-high').replace('{i}', record.I.toFixed(2));
    } else if (record.PF < 0.7) {
        alertText = Lang.t('alert-pf-low').replace('{pf}', record.PF.toFixed(2));
    }

    if (msg) msg.textContent = alertText;
    if (time) time.textContent = new Date().toLocaleTimeString(Lang.get() === 'ar' ? 'ar-SA' : 'en-US');

    card.classList.remove('hidden');
    alertActive = true;

    // Auto-dismiss after 30 seconds
    setTimeout(() => {
        if (alertActive) dismissAlert();
    }, 30000);
}

function dismissAlert() {
    const card = document.getElementById('ai-alert-card');
    if (card) {
        card.classList.add('hidden');
    }
    alertActive = false;
    alertDismissed = true;

    // Re-enable after 2 minutes
    setTimeout(() => {
        alertDismissed = false;
    }, 120000);
}

// ---------------------------------------------------------------------------
// Activity Log
// ---------------------------------------------------------------------------
function addActivityLog(record) {
    const log = document.getElementById('activity-log');
    if (!log) return;

    // Remove empty state
    const empty = log.querySelector('.text-center');
    if (empty) empty.remove();

    const time = new Date().toLocaleTimeString(Lang.get() === 'ar' ? 'ar-SA' : 'en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    const isAnomaly = record.is_anomaly;

    const item = document.createElement('div');
    item.className = `flex items-center justify-between p-3 rounded-xl ${isAnomaly ? 'bg-red-500/5 border border-red-500/10' : 'bg-slate-800/40 border border-slate-700/20'}`;
    item.innerHTML = `
        <div class="flex items-center gap-3">
            <div class="w-2 h-2 rounded-full ${isAnomaly ? 'bg-red-500' : 'bg-emerald-500'}"></div>
            <div>
                <div class="text-sm ${isAnomaly ? 'text-red-400 font-semibold' : 'text-slate-300'}">
                    ${isAnomaly ? Lang.t('log-alert') : Lang.t('log-normal')}
                </div>
                <div class="text-xs text-slate-500">${time}</div>
            </div>
        </div>
        <div class="text-start">
            <div class="text-sm font-semibold text-slate-200">${formatNumber(record.P, 1)} ${Lang.t('unit-watt')}</div>
            <div class="text-xs text-slate-500">${formatNumber(record.V, 1)}V · ${formatNumber(record.I, 2)}A</div>
        </div>
    `;

    log.insertBefore(item, log.firstChild);

    // Keep only last 10
    while (log.children.length > 10) {
        log.removeChild(log.lastChild);
    }
}

// ---------------------------------------------------------------------------
// Utilities
// ---------------------------------------------------------------------------
function formatNumber(value, decimals) {
    if (value === undefined || value === null || isNaN(value)) return '--';
    return Number(value).toFixed(decimals);
}

function logout() {
    localStorage.removeItem('access_token');
    window.location.href = '/login';
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
    connectWebSocket();
    updateCostAndTier(); // تحديث أرقام ونصوص الشرائح فور تحميل الصفحة
});
