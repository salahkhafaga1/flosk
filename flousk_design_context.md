# Flousk — Design Context (Frontend)

## 1) Frontend tech stack used
- **Vanilla HTML + Vanilla JS** (no React/Vue/Angular).
- Real-time updates via **WebSocket** (`ws://${window.location.host}/ws`).
- Charting: the current dashboard markup is designed for Tailwind/DOM updates; no framework is used for chart UI in the inspected dashboard file.
- i18n support appears to be handled by `static/lang.js` (loaded from `/static/lang.js`) and used via `Lang.t(...)` and `Lang.get()`.
- RTL support: HTML uses `dir="rtl"` and `lang="ar"` with `class="dark"`.

## 2) CSS framework or styling method
- **Tailwind CSS CDN** is used: `https://cdn.tailwindcss.com`.
- **Dark mode** driven by Tailwind `darkMode: 'class'` in `tailwind.config`.
- Styling approach:
  - Tailwind utility classes for most layout/typography/color.
  - Small amount of **custom CSS inside the main dashboard HTML** (e.g., glass panel backdrop filters, animations, scrollbars, ring backgrounds).
  - In addition, there is a separate older/alternate stylesheet at `frontend/static/style.css` that defines **CSS variables** (see section 4).

## 3) Exact code: main Dashboard page / primary layout with energy metrics

### Primary Dashboard file
- `frontend/static/index.html`
- The energy metrics are displayed in this file via DOM elements populated by `frontend/static/dashboard.js`.

#### Full contents (as currently present in `frontend/static/index.html`)
```html
<!DOCTYPE html>
<html lang="ar" dir="rtl" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title data-lang-key="hero-card-title">فلوسك — لوحة الطاقة الذكية</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
    <script>
        tailwind.config = {
            darkMode: 'class',
            theme: {
                extend: {
                    fontFamily: { cairo: ['Cairo', 'sans-serif'] },
                    colors: {
                        slate: {
                            950: '#020617', 900: '#0f172a', 850: '#0b1221',
                            800: '#1e293b', 750: '#182233', 700: '#334155', 600: '#475569',
                        }
                    }
                }
            }
        }
    </script>
    <script src="/static/lang.js"></script>
    <style>
        body { font-family: 'Cairo', sans-serif; }
        .glass-panel { backdrop-filter: blur(20px); transition: all 0.3s ease; }
        :is(.dark .glass-panel) { background: rgba(30,41,59,0.6); border: 1px solid rgba(99,102,241,0.12); }
        :is(html:not(.dark) .glass-panel) { background: rgba(255,255,255,0.8); border: 1px solid rgba(226,232,240,1); }
        .card-glow { box-shadow: 0 0 0 1px rgba(99,102,241,0.08), 0 4px 24px rgba(0,0,0,0.4); }
        .card-glow-green { box-shadow: 0 0 0 1px rgba(34,197,94,0.15), 0 4px 24px rgba(0,0,0,0.4); }
        .card-glow-red { box-shadow: 0 0 0 1px rgba(239,68,68,0.2), 0 4px 24px rgba(239,68,68,0.1), 0 0 40px rgba(239,68,68,0.05); }
        .gradient-text { background: linear-gradient(135deg,#818cf8 0%,#c084fc 50%,#f472b6 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
        .siren-pulse { animation: sirenPulse 1.5s ease-in-out infinite; }
        @keyframes sirenPulse { 0%,100%{opacity:1;transform:scale(1);filter:drop-shadow(0 0 4px rgba(239,68,68,0.6))} 50%{opacity:0.7;transform:scale(1.1);filter:drop-shadow(0 0 12px rgba(239,68,68,0.9))} }
        .slide-up { animation: slideUp 0.5s ease forwards; }
        @keyframes slideUp { from{opacity:0;transform:translateY(16px)} to{opacity:1;transform:translateY(0)} }
        .health-ring { background: conic-gradient(#22c55e var(--health-percent), rgba(30,41,59,0.8) 0); }
        .live-dot { animation: liveBlink 2s infinite; }
        @keyframes liveBlink { 0%,100%{opacity:1} 50%{opacity:0.3} }
        .cost-arrow { animation: floatArrow 2s ease-in-out infinite; }
        @keyframes floatArrow { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-3px)} }
        .tier-bar { background: linear-gradient(90deg,#22c55e 0%,#eab308 50%,#ef4444 100%); }
        ::-webkit-scrollbar { width:6px; }
        ::-webkit-scrollbar-track { background:#0f172a; }
        ::-webkit-scrollbar-thumb { background:#334155; border-radius:3px; }
        ::-webkit-scrollbar-thumb:hover { background:#475569; }
    </style>
</head>
<body class="bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-white min-h-screen overflow-x-hidden transition-colors duration-300">

    <!-- Background glow -->
    <div class="fixed inset-0 pointer-events-none overflow-hidden">
        <div class="absolute top-0 end-0 w-[600px] h-[600px] bg-indigo-600/5 rounded-full blur-[120px]"></div>
        <div class="absolute bottom-0 start-0 w-[500px] h-[500px] bg-purple-600/5 rounded-full blur-[100px]"></div>
    </div>

    <!-- Header -->
    <nav class="relative border-b border-slate-200 dark:border-slate-800 backdrop-blur-lg bg-white/90 dark:bg-gradient-to-b dark:from-slate-900/95 dark:to-slate-950/80 sticky top-0 z-50 transition-colors duration-300">
        <div class="w-full px-8 py-5 flex items-center justify-between">
            <div class="flex items-center gap-4">
                <div class="w-12 h-12 bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 rounded-2xl flex items-center justify-center text-2xl shadow-2xl shadow-purple-500/40 hover:scale-110 transition-transform">⚡</div>
                <div>
                    <span class="text-2xl font-bold bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400 bg-clip-text text-transparent" data-lang-key="hero-h1-brand">فلوسك</span>
                    <span class="text-xs text-slate-500 dark:text-slate-400 block -mt-1 font-medium">Smart Energy Monitor</span>
                </div>
            </div>
            <div class="hidden lg:flex items-center gap-8 mx-8">
                <a href="/dashboard" class="text-sm font-bold text-slate-900 dark:text-white border-b-2 border-indigo-500 pb-1" data-lang-key="nav-dashboard">لوحة الطاقة</a>
                <a href="/claim" class="text-sm font-medium text-slate-600 dark:text-slate-400 hover:text-indigo-600 dark:hover:text-white transition" data-lang-key="nav-connect">ربط الجهاز</a>
                <a href="/onboarding" class="text-sm font-medium text-slate-600 dark:text-slate-400 hover:text-indigo-600 dark:hover:text-white transition" data-lang-key="nav-appliances">الأجهزة</a>
            </div>
            <div class="flex items-center gap-4">
                <div class="flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-100 dark:bg-slate-800/30 border border-slate-200 dark:border-slate-700/30 backdrop-blur-sm">
                    <span id="ws-status-dot" class="w-2.5 h-2.5 rounded-full bg-emerald-400 live-dot"></span>
                    <span id="ws-status-text" class="text-[10px] text-slate-600 dark:text-slate-400 font-bold uppercase tracking-wider" data-lang-key="ws-connected">متصل</span>
                </div>
                <button onclick="Theme.toggle()" class="flsk-theme-btn text-slate-500 dark:text-slate-400 hover:text-indigo-600 dark:hover:text-white text-lg transition" title="تبديل المظهر">☀️</button>
                <button onclick="Lang.set(Lang.get()==='ar'?'en':'ar')" id="flsk-lang-btn" class="text-slate-500 dark:text-slate-400 hover:text-indigo-600 dark:hover:text-white text-xs font-bold transition">🌐 EN</button>
                <div class="h-4 w-px bg-slate-700/50"></div>
                <span id="user-email" class="text-slate-500 dark:text-slate-400 text-xs font-medium truncate max-w-[150px]">...</span>
                <button onclick="logout()" class="bg-red-500/10 hover:bg-red-500/20 text-red-400 px-3 py-1.5 rounded-lg text-xs font-bold transition" data-lang-key="logout-btn">خروج</button>
            </div>
        </div>
    </nav>

    <!-- Main Content -->
    <main class="relative w-full px-6 py-8 space-y-6">

        <!-- Welcome -->
        <div class="mb-10 slide-up">
            <h1 class="text-4xl font-bold mb-3 bg-gradient-to-r from-slate-800 via-slate-600 to-slate-800 dark:from-white dark:via-slate-100 dark:to-slate-300 bg-clip-text text-transparent" data-lang-key="dash-title">مرحباً بكم في لوحة الطاقة الذكية</h1>
            <p class="text-slate-500 dark:text-slate-400 text-lg font-medium" data-lang-key="dash-sub">📊 مراقبة استهلاك الطاقة والتيار في الوقت الفعلي</p>
        </div>

        <!-- AI Alert -->
        <div id="ai-alert-card" class="hidden glass-panel card-glow-red rounded-2xl p-6 border-red-500/20 slide-up w-full">
            <div class="flex items-start gap-4">
                <div class="w-14 h-14 bg-red-500/10 rounded-xl flex items-center justify-center text-3xl shrink-0 siren-pulse border border-red-500/20">🚨</div>
                <div class="flex-1 min-w-0">
                    <div class="flex items-center gap-2 mb-1">
                        <h3 class="text-red-400 font-bold text-lg" data-lang-key="alert-title">تنبيه ذكي</h3>
                        <span class="px-2 py-0.5 bg-red-500/10 text-red-400 text-xs rounded-full border border-red-500/20">AI</span>
                    </div>
                    <p id="ai-alert-message" class="text-slate-300 text-sm leading-relaxed break-words" data-lang-key="alert-ac-high">التكیيف بيسحب طاقة أكثر من المعتاد - يُنصح بالصیانة</p>
                    <div class="mt-3 flex items-center gap-3">
                        <span id="ai-alert-time" class="text-xs text-slate-500" data-lang-key="hero-alert-time">الآن</span>
                        <button onclick="dismissAlert()" class="text-xs text-slate-500 hover:text-slate-300 transition" data-lang-key="alert-dismiss">تجاهل</button>
                    </div>
                </div>
            </div>
        </div>

        <!-- KPI Cards -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-8">

            <!-- Cost Card -->
            <div class="glass-panel card-glow rounded-3xl p-7 slide-up hover:shadow-xl transition-all duration-300 hover:border-emerald-500/30 backdrop-blur-xl" style="animation-delay:0.1s;background:linear-gradient(135deg,rgba(5,150,105,0.05)0%,rgba(16,185,129,0.03)100%)">
                <div class="flex items-center justify-between mb-6">
                    <div class="flex items-center gap-3">
                        <div class="w-12 h-12 bg-gradient-to-br from-emerald-500 to-teal-500 rounded-2xl flex items-center justify-center text-2xl shadow-lg shadow-emerald-500/30">💰</div>
                        <div>
                            <h3 class="font-bold text-slate-800 dark:text-slate-100 text-lg" data-lang-key="cost-card-title">التكلفة التقديرية</h3>
                            <p class="text-xs text-slate-500 dark:text-slate-400 font-medium" data-lang-key="cost-card-sub">هذا الشهر</p>
                        </div>
                    </div>
                    <div class="flex items-center gap-2 bg-emerald-500/15 px-3 py-1.5 rounded-full border border-emerald-500/30">
                        <svg class="w-4 h-4 text-emerald-400 cost-arrow" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 14l-7 7m0 0l-7-7m7 7V3"/></svg>
                        <span class="text-xs font-bold text-emerald-400">-12%</span>
                    </div>
                </div>
                <div class="flex flex-col items-center justify-center mb-5">
                    <div class="flex items-baseline gap-1">
                        <span id="cost-value" class="text-5xl font-bold bg-gradient-to-r from-emerald-400 to-teal-400 bg-clip-text text-transparent">0</span>
                        <span class="text-xl text-slate-500 dark:text-slate-400 font-semibold" data-lang-key="cost-currency">جنيه</span>
                    </div>
                </div>
                <div class="space-y-3">
                    <div class="flex justify-between text-sm text-slate-500 dark:text-slate-400">
                        <span class="font-medium" data-lang-key="live-power">الاستهلاك الحالي</span>
                        <span id="cost-percent" class="font-bold text-slate-900 dark:text-white">0%</span>
                    </div>
                    <div class="h-3 bg-slate-800/50 rounded-full overflow-hidden border border-emerald-500/10">
                        <div id="cost-bar" class="h-full bg-gradient-to-r from-emerald-500 to-teal-400 rounded-full transition-all duration-700 shadow-lg shadow-emerald-500/30" style="width:0%"></div>
                    </div>
                </div>
                <div class="mt-6 pt-6 border-t border-slate-700/50 flex items-center gap-2 text-sm text-emerald-400/90">
                    <svg class="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"/></svg>
                    <span class="font-medium" data-lang-key="cost-save-label">اقلل من الشهر الماضي بنسبة 12%</span>
                </div>
            </div>

            <!-- Tier Card -->
            <div class="glass-panel card-glow rounded-3xl p-7 slide-up hover:shadow-xl transition-all duration-300 hover:border-amber-500/30 backdrop-blur-xl" style="animation-delay:0.15s;background:linear-gradient(135deg,rgba(180,83,9,0.05)0%,rgba(217,119,6,0.03)100%)">
                <div class="flex items-center gap-3 mb-6">
                    <div class="w-12 h-12 bg-gradient-to-br from-amber-500 to-orange-500 rounded-2xl flex items-center justify-center text-2xl shadow-lg shadow-amber-500/30">⚡</div>
                    <div>
                        <h3 class="font-bold text-slate-800 dark:text-slate-100 text-lg" data-lang-key="tier-card-title">الشريحة الحالية</h3>
                        <p class="text-xs text-slate-500 dark:text-slate-400 font-medium" data-lang-key="tier-card-sub">تعريفه الطاقة المصرفية</p>
                    </div>
                </div>
                <div class="flex flex-col items-center justify-center mb-5">
                    <span id="tier-name" class="text-3xl font-bold bg-gradient-to-r from-amber-400 to-orange-400 bg-clip-text text-transparent" data-lang-key="tier-1">الشريحة الأولى</span>
                </div>
                <div class="space-y-4">
                    <div class="flex justify-between text-sm font-medium">
                        <span id="tier-range" class="text-slate-500 dark:text-slate-400">0 → 50 kWh</span>
                        <span id="tier-price" class="text-amber-400 font-bold">0.58 EGP/kWh</span>
                    </div>
                    <div class="h-4 bg-slate-800/50 rounded-full overflow-hidden border border-amber-500/10 relative">
                        <div id="tier-progress" class="h-full bg-gradient-to-r from-amber-500 to-orange-400 rounded-full transition-all duration-700 shadow-lg shadow-amber-500/30" style="width:0%"></div>
                    </div>
                    <div class="flex justify-between text-xs text-slate-500 dark:text-slate-400 font-medium">
                        <span id="tier-min">0</span>
                        <span id="tier-current">0 kWh</span>
                        <span id="tier-max">50 kWh</span>
                    </div>
                </div>
                <div class="mt-6 pt-6 border-t border-slate-700/50 flex items-center justify-between">
                    <span class="text-slate-500 dark:text-slate-400 font-medium" data-lang-key="tier-remaining-lbl">الحد المتبقي</span>
                    <span id="tier-remaining" class="text-xl font-bold text-slate-900 dark:text-white">50 kWh</span>
                </div>
            </div>

            <!-- Health Card -->
            <div class="glass-panel card-glow-green rounded-3xl p-7 slide-up hover:shadow-xl transition-all duration-300 hover:border-emerald-500/30 backdrop-blur-xl" style="animation-delay:0.2s;background:linear-gradient(135deg,rgba(5,150,105,0.05)0%,rgba(16,185,129,0.03)100%)">
                <div class="flex items-center gap-3 mb-6">
                    <div class="w-12 h-12 bg-gradient-to-br from-emerald-500 to-teal-500 rounded-2xl flex items-center justify-center text-2xl shadow-lg shadow-emerald-500/30">✅</div>
                    <div>
                        <h3 class="font-bold text-slate-800 dark:text-slate-100 text-lg" data-lang-key="health-card-title">صحة الأجهزة</h3>
                        <p class="text-xs text-slate-500 dark:text-slate-400 font-medium" data-lang-key="health-card-sub">حالة جميع الأجهزة المسجلة</p>
                    </div>
                </div>
                <div class="flex items-center gap-6 mb-6">
                    <div class="relative w-24 h-24 shrink-0">
                        <div class="absolute inset-0 rounded-full bg-gradient-to-br from-emerald-500/20 to-teal-500/10 blur-xl"></div>
                        <div class="absolute inset-0 rounded-full health-ring border-2 border-emerald-500/30" style="--health-percent:100%"></div>
                        <div class="absolute inset-3 bg-gradient-to-br from-slate-800 to-slate-900 rounded-full flex items-center justify-center border border-emerald-500/20">
                            <span id="health-percent" class="text-2xl font-bold text-emerald-400">100%</span>
                        </div>
                    </div>
                    <div class="flex-1">
                        <div class="flex items-center gap-2 mb-3">
                            <span class="w-3 h-3 rounded-full bg-emerald-500 shadow-lg shadow-emerald-500/50"></span>
                            <span class="text-base text-emerald-400 font-bold" data-lang-key="health-ok">جميع الأجهزة تعمل بكفاءة</span>
                        </div>
                        <p class="text-sm text-slate-600 dark:text-slate-400 leading-relaxed" data-lang-key="health-ok-sub">لا توجد مشاكل كثيرة. استمر في مراقبة الأجهزة.</p>
                    </div>
                </div>
                <div class="grid grid-cols-3 gap-3 pt-6 border-t border-slate-700/50">
                    <div class="text-center bg-emerald-500/10 rounded-xl p-3 border border-emerald-500/20">
                        <div id="healthy-count" class="text-2xl font-bold text-emerald-400">0</div>
                        <div class="text-xs text-slate-600 dark:text-slate-400 font-medium mt-1" data-lang-key="health-healthy">سليمة</div>
                    </div>
                    <div class="text-center bg-amber-500/10 rounded-xl p-3 border border-emerald-500/20">
                        <div id="warning-count" class="text-2xl font-bold text-amber-400">0</div>
                        <div class="text-xs text-slate-600 dark:text-slate-400 font-medium mt-1" data-lang-key="health-warning">تحذير</div>
                    </div>
                    <div class="text-center bg-red-500/10 rounded-xl p-3 border border-red-500/20">
                        <div id="critical-count" class="text-2xl font-bold text-red-400">0</div>
                        <div class="text-xs text-slate-600 dark:text-slate-400 font-medium mt-1" data-lang-key="health-critical">حرجة</div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Live Telemetry -->
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4 slide-up" style="animation-delay:0.25s">
            <div class="glass-panel rounded-2xl p-5 text-center hover:border-indigo-500/30 transition-all backdrop-blur-xl border border-slate-600/30">
                <div class="text-xs text-slate-500 dark:text-slate-400 font-medium mb-2 uppercase tracking-wider" data-lang-key="live-voltage">الجهد</div>
                <div id="live-voltage" class="text-3xl font-bold bg-gradient-to-r from-indigo-400 to-blue-400 bg-clip-text text-transparent">--</div>
                <div class="text-xs text-slate-600 dark:text-slate-400 font-semibold mt-1">V</div>
            </div>
            <div class="glass-panel rounded-2xl p-5 text-center hover:border-purple-500/30 transition-all backdrop-blur-xl border border-slate-600/30">
                <div class="text-xs text-slate-500 dark:text-slate-400 font-medium mb-2 uppercase tracking-wider" data-lang-key="live-current">التيار</div>
                <div id="live-current" class="text-3xl font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">--</div>
                <div class="text-xs text-slate-600 dark:text-slate-400 font-semibold mt-1">A</div>
            </div>
            <div class="glass-panel rounded-2xl p-5 text-center hover:border-pink-500/30 transition-all backdrop-blur-xl border border-slate-600/30">
                <div class="text-xs text-slate-500 dark:text-slate-400 font-medium mb-2 uppercase tracking-wider" data-lang-key="live-power">الاستهلاك</div>
                <div id="live-power" class="text-3xl font-bold bg-gradient-to-r from-pink-400 to-rose-400 bg-clip-text text-transparent">--</div>
                <div class="text-xs text-slate-600 dark:text-slate-400 font-semibold mt-1">W</div>
            </div>
            <div class="glass-panel rounded-2xl p-5 text-center hover:border-cyan-500/30 transition-all backdrop-blur-xl border border-slate-600/30">
                <div class="text-xs text-slate-500 dark:text-slate-400 font-medium mb-2 uppercase tracking-wider" data-lang-key="live-pf">معامل القدرة</div>
                <div id="live-pf" class="text-3xl font-bold bg-gradient-to-r from-cyan-400 to-teal-400 bg-clip-text text-transparent">--</div>
                <div class="text-xs text-slate-600 dark:text-slate-400 font-semibold mt-1">PF</div>
            </div>
        </div>

        <!-- Activity Log -->
        <div class="glass-panel card-glow rounded-3xl p-7 slide-up" style="animation-delay:0.3s">
            <div class="flex items-center justify-between mb-6">
                <div>
                    <h3 class="font-bold text-slate-800 dark:text-slate-100 text-xl" data-lang-key="activity-title">📄 النشاط الآخر</h3>
                </div>
                <div class="px-4 py-2 bg-gradient-to-r from-slate-200 dark:from-slate-700/50 to-slate-100 dark:to-slate-600/30 rounded-full text-xs text-slate-500 dark:text-slate-400 font-medium border border-slate-300 dark:border-slate-600/30" data-lang-key="activity-badge">🔎 آخر 10 قراءات</div>
            </div>
            <div id="activity-log" class="space-y-2 max-h-64 overflow-y-auto">
                <div class="text-center text-slate-500 dark:text-slate-600 text-sm py-12 font-medium" data-lang-key="activity-empty">⏳ في انتظار البيانات...</div>
            </div>
        </div>
    </main>

    <!-- Footer -->
    <footer class="relative w-full px-6 py-6 text-center">
        <p class="text-xs text-slate-600" data-lang-key="footer-dash">فلوسك © 2025 — مراقبة الطاقة الذكية</p>
    </footer>

    <script src="dashboard.js"></script>
    <script src="/static/chat-widget.js"></script>
</body>
</html>
```

### Dashboard JS that updates the metrics in the page
- `frontend/static/dashboard.js`
- Key DOM ids it updates:
  - `live-voltage` (record.V)
  - `live-current` (record.I)
  - `live-power` (record.P)
  - `live-pf` (record.PF)
  - Cost/tier UI: `cost-value`, `cost-percent`, `cost-bar`, `tier-name`, `tier-progress`, `tier-current`, `tier-remaining`, etc.
  - `ai-alert-card` / `ai-alert-message` / `ai-alert-time`
  - `activity-log` (last 10 readings)

(For reference, the file uses WebSocket messages filtered by `window.userDeviceId` and accumulates energy using approximately `kWh += P/1000/3600` per second reading.)

## 4) Existing CSS variables, global styles, or color palette

### 4.1 `frontend/static/style.css` (CSS variables)
This file defines a color palette via `:root` CSS variables.

Full `:root` section:
```css
:root {
    --bg-primary: #0f172a;
    --bg-secondary: #1e293b;
    --bg-card: #334155;
    --text-primary: #f1f5f9;
    --text-secondary: #94a3b8;
    --accent-green: #22c55e;
    --accent-red: #ef4444;
    --accent-yellow: #eab308;
    --accent-blue: #3b82f6;
    --accent-purple: #a855f7;
    --accent-orange: #f97316;
    --border-radius: 12px;
    --transition: all 0.3s ease;
}
```

Other notable global styles in this file:
- Global `* { margin:0; padding:0; box-sizing:border-box; }`
- `body { font-family: 'Segoe UI', ...; background: linear-gradient(...); color: var(--text-primary); }`
- Styling for classic (non-Tailwind) components: `header`, `.badge`, `.metric-card`, `.dashboard-split`, `.diagnostics-panel`, `.modal-overlay`, `.btn-primary`, `.log-section`, etc.

### 4.2 Tailwind/custom CSS in `frontend/static/index.html`
`index.html` includes a small custom `<style>` block that defines additional styling helpers and animations:
- `.glass-panel` (uses `backdrop-filter: blur(20px)`)
- glow shadows `.card-glow`, `.card-glow-green`, `.card-glow-red`
- animations: `.siren-pulse`, `.slide-up` + keyframes, `.live-dot` + keyframes, `.cost-arrow` + keyframes
- `.health-ring` uses CSS variable `--health-percent`
- custom scrollbar styling using `::-webkit-scrollbar*`

No additional `:root {}` variables were found in `index.html` (besides Tailwind config color extension).

## 5) Tailwind configuration customization
Inside `frontend/static/index.html` `<script>` block:
- `darkMode: 'class'`
- theme extension:
  - `fontFamily.cairo`
  - `colors.slate` overrides for 950/900/850/800/750/700/600 values

---
EOF

