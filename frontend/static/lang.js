/**
 * lang.js — Bilingual (AR/EN) language system for Flowsk / فلوسك
 * Usage: include this script, then call Lang.apply() on page load.
 * Toggle button is injected automatically.
 */

const TRANSLATIONS = {
  // ─── landing.html ────────────────────────────────────────────
  'nav-features':       { ar: 'المميزات',       en: 'Features' },
  'nav-how':            { ar: 'كيف يعمل',       en: 'How It Works' },
  'nav-pricing':        { ar: 'الأسعار',         en: 'Pricing' },
  'nav-login':          { ar: 'تسجيل الدخول',   en: 'Sign In' },
  'hero-badge':         { ar: 'وفر حتى ٣٠٪ من فاتورة الكهرباء شهرياً', en: 'Save up to 30% on your electricity bill monthly' },
  'hero-h1-line1':      { ar: 'حمّل',           en: 'Take Control of' },
  'nav-dashboard':      { ar: 'لوحة التحكم',     en: 'Dashboard' },
  'nav-connect':        { ar: 'ربط الجهاز',      en: 'Connect Your Device' },
  'nav-appliances':     { ar: 'الأجهزة',         en: 'Appliances' },
  'step-account':       { ar: 'إنشاء حساب',      en: 'New Account' },
  'step-claim':         { ar: 'ربط الجهاز',      en: 'Connect Your Device' },
  'step-onb':           { ar: 'أجهزة المنزل',     en: 'Appliances' },
  'step-dash':          { ar: 'لوحة التحكم',     en: 'Dashboard' },
  'hero-h1-brand':      { ar: 'فلوسك',           en: 'Flowsk' },
  'hero-h1-line2':      { ar: 'فواتير الكهرباء', en: 'Your Energy Bills' },
  'hero-h1-sub':        { ar: 'قبل ما تروح',     en: 'Before They Drain You' },
  'hero-desc':          { ar: 'جهاز ذكي واحد يراقب استهلاك بيتك لحظة بلحظة. يكتشف الأعطال قبل ما تحصل، ويحذرك من الأجهزة اللي بتسرق الكهرباء.', en: 'One smart device monitors your home\'s energy consumption in real-time. It detects faults before they happen and alerts you to appliances wasting electricity.' },
  'hero-cta-start':     { ar: 'ابدأ مجاناً 🚀',  en: 'Start Free 🚀' },
  'hero-cta-learn':     { ar: 'اعرف أكتر',       en: 'Learn More' },
  'hero-social':        { ar: 'انضم لـ +١٠٠٠ أسرة مصرية وفّرت فلوسها', en: 'Join 1,000+ Egyptian families who saved money' },
  'hero-card-title':    { ar: 'لوحة التحكم',      en: 'Dashboard' },
  'hero-cost-label':    { ar: 'التكلفة التقديرية', en: 'Estimated Cost' },
  'hero-cost-val':      { ar: '٤٨٥ جنيه',         en: '485 EGP' },
  'hero-cost-decrease': { ar: '▼ ٢٣٪',            en: '▼ 23%' },
  'hero-tier-label':    { ar: 'الشريحة الحالية',  en: 'Current Tier' },
  'hero-tier-val':      { ar: 'الأولى',            en: '1st' },
  'hero-health-label':  { ar: 'صحة الأجهزة',      en: 'Appliance Health' },
  'hero-health-val':    { ar: 'جيدة ✅',           en: 'Good ✅' },
  'hero-alert-title':   { ar: 'تنبيه ذكي',         en: 'Smart Alert' },
  'hero-alert-desc':    { ar: 'التكييف بيسحب طاقة أكتر من المعتاد - يُنصح بالصيانة', en: 'AC drawing more power than usual - maintenance recommended' },
  'proof-label':        { ar: 'موثوق من أسر مصرية في', en: 'Trusted by Egyptian families in' },
  'city-cairo':         { ar: 'القاهرة',           en: 'Cairo' },
  'city-giza':          { ar: 'الجيزة',            en: 'Giza' },
  'city-alex':          { ar: 'الإسكندرية',        en: 'Alexandria' },
  'city-mansoura':      { ar: 'المنصورة',          en: 'Mansoura' },
  'city-tanta':         { ar: 'طنطا',              en: 'Tanta' },
  'city-fayoum':        { ar: 'الفيوم',            en: 'Fayoum' },
  'features-title':     { ar: 'ليه <span class="gradient-text">فلوسك</span>؟', en: '<span class="gradient-text">Why Flowsk?</span>' },
  'features-sub':       { ar: 'مش مجرد عداد كهرباء ذكي — ده مساعد شخصي بيفهم بيتك ويوفر فلوسك', en: 'Not just a smart meter — a personal assistant that understands your home and saves your money' },
  'feat1-title':        { ar: 'وفر فلوسك',          en: 'Save Money' },
  'feat1-desc':         { ar: 'تعرف بالظبط كل جهاز بيستهلك كام. اكتشف الأجهزة اللي شغالة وراك وبتسرق الكهرباء. وفر حتى ٣٠٪ من قيمة الفاتورة كل شهر.', en: 'Know exactly how much each appliance consumes. Find devices running in the background wasting electricity. Save up to 30% on monthly bills.' },
  'feat2-title':        { ar: 'احمي أجهزتك',        en: 'Protect Appliances' },
  'feat2-desc':         { ar: 'الذكاء الاصطناعي بيراقب صحة كل جهاز في بيتك. لو التكييف أو الثلاجة بدأوا يستهلكوا غير طبيعي، هنحذرك قبل ما يحصل عطل مكلف.', en: 'AI monitors the health of every appliance in your home. If your AC or fridge starts drawing abnormal power, we\'ll warn you before a costly breakdown.' },
  'feat3-title':        { ar: 'صيانة قبل العطل',    en: 'Predictive Maintenance' },
  'feat3-desc':         { ar: 'متستناش العطل يحصل. نحن بنتنبأ بالمشاكل قبل ما تبوظ جهازك. استلم تنبيهات زكية بالصيانة الدورية في الوقت المناسب.', en: 'Don\'t wait for breakdowns. We predict problems before your device fails. Receive smart maintenance alerts at the right time.' },
  'how-title':          { ar: 'كيف يعمل؟',           en: 'How It Works?' },
  'how-sub':            { ar: '٣ خطوات بسيطة وانت بتتحكم في فاتورتك', en: '3 simple steps and you\'re in control of your bill' },
  'step1-title':        { ar: 'وصل الجهاز',           en: 'Connect Device' },
  'step1-desc':         { ar: 'جهاز ESP32 صغير بيوصل بلوحة الكهرباء في دقايق. مش محتاج فني.', en: 'A small ESP32 device connects to your electrical panel in minutes. No technician needed.' },
  'step2-title':        { ar: 'سجل أجهزتك',           en: 'Register Appliances' },
  'step2-desc':         { ar: 'اختار أجهزة بيتك من قائمة جاهزة. التطبيق بيعرف كل جهاز بيستهلك كام.', en: 'Choose your home appliances from a ready list. The app knows the consumption of each device.' },
  'step3-title':        { ar: 'تابع ووفر',             en: 'Monitor & Save' },
  'step3-desc':         { ar: 'شوف فاتورتك لحظة بلحظة. استلم تنبيهات ذكية وقرارات مبنية على بيانات حقيقية.', en: 'Watch your bill in real-time. Receive smart alerts and data-driven decisions.' },
  'price-title':        { ar: 'ابدأ <span class="text-green-400">مجاناً</span>', en: '<span class="text-green-400">Start Free</span>' },
  'price-sub':          { ar: 'جرب فلوسك مجاناً لمدة ١٤ يوم. مش محتاج بطاقة ائتمان.', en: 'Try Flowsk free for 14 days. No credit card required.' },
  'price-plan':         { ar: 'مجاناً',                 en: 'Free' },
  'price-after':        { ar: 'لمدة ١٤ يوم — بعدها ٩٩ جنيه/شهر', en: 'For 14 days — then 99 EGP/month' },
  'price-f1':           { ar: 'مراقبة لحظية لاستهلاك الكهرباء', en: 'Real-time electricity monitoring' },
  'price-f2':           { ar: 'تنبيهات ذكية للأعطال',   en: 'Smart fault alerts' },
  'price-f3':           { ar: 'تقدير الفاتورة قبل ما تنزل', en: 'Bill estimate before it arrives' },
  'price-f4':           { ar: 'نصائح لتوفير الطاقة',    en: 'Energy saving tips' },
  'price-cta':          { ar: 'ابدأ تجربتك المجانية',   en: 'Start Your Free Trial' },
  'footer-rights':      { ar: '© ٢٠٢٤ فلوسك. جميع الحقوق محفوظة.', en: '© 2024 Flowsk. All rights reserved.' },
  'footer-privacy':     { ar: 'الخصوصية', en: 'Privacy' },
  'footer-terms':       { ar: 'الشروط',   en: 'Terms' },
  'footer-support':     { ar: 'الدعم',    en: 'Support' },
  // ─── login.html ─────────────────────────────────────────────
  'login-subtitle':     { ar: 'سجّل دخولك وابدأ توفير فلوسك', en: 'Sign in and start saving energy' },
  'tab-login':          { ar: 'تسجيل الدخول', en: 'Sign In' },
  'tab-register':       { ar: 'حساب جديد',    en: 'New Account' },
  'lbl-email':          { ar: 'البريد الإلكتروني', en: 'Email Address' },
  'lbl-password':       { ar: 'كلمة المرور',       en: 'Password' },
  'lbl-name':           { ar: 'الاسم الكامل',       en: 'Full Name' },
  'btn-login':          { ar: 'دخول',               en: 'Sign In' },
  'btn-register':       { ar: 'إنشاء حساب',         en: 'Create Account' },
  'back-home':          { ar: '← الرجوع للصفحة الرئيسية', en: '← Back to Home' },
  // ─── dashboard / index.html ─────────────────────────────────
  'dash-title':         { ar: 'مرحباً بك في لوحة التحكم', en: 'Welcome to Dashboard' },
  'dash-sub':           { ar: '📊 مراقبة استهلاك الطاقة والتكاليف في الوقت الفعلي', en: '📊 Real-time energy consumption & cost monitoring' },
  'ws-connected':       { ar: 'متصل',    en: 'Connected' },
  'ws-disconnected':    { ar: 'منقطع',   en: 'Disconnected' },
  'logout-btn':         { ar: 'خروج',    en: 'Logout' },
  'cost-card-title':    { ar: 'التكلفة التقديرية', en: 'Estimated Cost' },
  'cost-card-sub':      { ar: 'هذا الشهر',          en: 'This month' },
  'cost-currency':      { ar: 'جنيه',               en: 'EGP' },
  'cost-save-label':    { ar: 'أقل من الشهر الماضي بنسبة 12%', en: '12% less than last month' },
  'tier-card-title':    { ar: 'الشريحة الحالية',    en: 'Current Tier' },
  'tier-card-sub':      { ar: 'تعريفة الكهرباء المصرية', en: 'Egyptian electricity tariff' },
  'tier-remaining-lbl': { ar: 'الحد المتبقي',       en: 'Remaining Limit' },
  'health-card-title':  { ar: 'صحة الأجهزة',        en: 'Appliance Health' },
  'health-card-sub':    { ar: 'حالة جميع الأجهزة المسجلة', en: 'Status of all registered appliances' },
  'health-ok':          { ar: 'جميع الأجهزة تعمل بكفاءة', en: 'All appliances running efficiently' },
  'health-ok-sub':      { ar: 'لا توجد مشاكل مكتشفة في الأجهزة المسجلة. استمر في المراقبة.', en: 'No issues detected in registered appliances. Keep monitoring.' },
  'health-healthy':     { ar: 'سليمة',   en: 'Healthy' },
  'health-warning':     { ar: 'تحذير',   en: 'Warning' },
  'health-critical':    { ar: 'حرجة',    en: 'Critical' },
  'live-voltage':       { ar: 'الجهد',   en: 'Voltage' },
  'live-current':       { ar: 'التيار',  en: 'Current' },
  'live-power':         { ar: 'الاستطاعة', en: 'Power' },
  'live-pf':            { ar: 'معامل القدرة', en: 'Power Factor' },
  'activity-title':     { ar: '📄 النشاط الأخير', en: '📄 Recent Activity' },
  'activity-badge':     { ar: '🔎 آخر 10 قراءات', en: '🔎 Last 10 Readings' },
  'activity-empty':     { ar: '⏳ في انتظار البيانات...', en: '⏳ Waiting for data...' },
  'alert-title':        { ar: 'تنبيه ذكي', en: 'Smart Alert' },
  'alert-dismiss':      { ar: 'تجاهل',    en: 'Dismiss' },
  'footer-dash':        { ar: 'فلوسك © 2025 — مراقبة الطاقة الذكية', en: 'Flowsk © 2025 — Smart Energy Monitoring' },
  // ─── claim.html ─────────────────────────────────────────────
  'claim-title':        { ar: 'ربط جهازك',           en: 'Connect Your Device' },
  'claim-sub':          { ar: 'لعرض بيانات استهلاك الطاقة في منزلك، نحتاج إلى ربط جهاز ESP32 بحسابك.', en: 'To view energy consumption data, we need to link an ESP32 device to your account.' },
  'claim-step1-h':      { ar: 'افتح Serial Monitor', en: 'Open Serial Monitor' },
  'claim-step1-p':      { ar: 'افتح Arduino IDE أو PlatformIO وشغّل Serial Monitor على baud rate 115200', en: 'Open Arduino IDE or PlatformIO and run Serial Monitor at 115200 baud rate.' },
  'claim-step2-h':      { ar: 'ابحث عن معرف الجهاز', en: 'Find Device ID' },
  'claim-step2-p':      { ar: 'عند تشغيل ESP32، سيظهر معرف الجهاز في السجل. انسخه بالكامل.', en: 'When ESP32 starts, the device ID will appear in the log. Copy it completely.' },
  'claim-step3-h':      { ar: 'أدخل المعرف هنا',     en: 'Enter ID Here' },
  'claim-step3-p':      { ar: 'الصق المعرف في الحقل المخصص واضغط "ربط الجهاز"', en: 'Paste the ID in the field and click "Connect Device".' },
  'claim-input-lbl':    { ar: 'معرف الجهاز (Device ID)', en: 'Device ID' },
  'claim-input-ph':     { ar: 'مثال: 192.168.1.4 أو esp32-energy-01', en: 'Example: 192.168.1.4 or esp32-energy-01' },
  'claim-btn':          { ar: 'ربط الجهاز',           en: 'Connect Device' },
  'claim-demo-btn':     { ar: 'استخدم جهاز المحاكاة للتجربة', en: 'Use simulation device for testing' },
  'claim-no-device':    { ar: 'ليس لديك جهاز بعد؟',    en: 'Don\'t have a device yet?' },
  'claim-success-h':    { ar: 'تم ربط الجهاز بنجاح!',  en: 'Device connected successfully!' },
  'claim-success-p':    { ar: 'جهازك الآن مرتبط بحسابك. يمكنك الانتقال إلى لوحة التحكم.', en: 'Your device is now linked. You can go to the dashboard.' },
  'claim-next-step':    { ar: 'الخطوة التالية: أجهزة المنزل ←', en: 'Next Step: Home Appliances →' },
  // ─── onboarding.html ────────────────────────────────────────
  'onb-title':          { ar: 'أضف أجهزة منزلك',     en: 'Add Your Home Appliances' },
  'onb-sub':            { ar: 'ساعد الذكاء الاصطناعي في تقديم تشخيصات دقيقة بإضافة الأجهزة الكهربائية في منزلك.', en: 'Help AI provide accurate diagnostics by adding your home electrical appliances.' },
  'onb-select-lbl':     { ar: 'اختر الجهاز',          en: 'Select Appliance' },
  'onb-select-ph':      { ar: '-- اختر جهازاً --',     en: '-- Select Appliance --' },
  'onb-wattage-lbl':    { ar: 'الاستطاعة (وات)',      en: 'Wattage (W)' },
  'onb-quantity-lbl':   { ar: 'الكمية',               en: 'Quantity' },
  'onb-add-btn':        { ar: '+ إضافة',              en: '+ Add' },
  'onb-quick-lbl':      { ar: 'إضافة سريعة:',         en: 'Quick Add:' },
  'onb-list-h':         { ar: 'الأجهزة المضافة',      en: 'Added Appliances' },
  'onb-empty-p1':       { ar: 'لم تُضف أي أجهزة بعد.', en: 'No appliances added yet.' },
  'onb-empty-p2':       { ar: 'اختر جهازاً من القائمة أعلاه واضغط "إضافة"', en: 'Choose an appliance from the list above and click "Add".' },
  'onb-summary-h':      { ar: 'ملخص المنزل',          en: 'Home Summary' },
  'onb-count-lbl':      { ar: 'عدد الأجهزة',          en: 'Device Count' },
  'onb-total-wattage':  { ar: 'إجمالي الاستطاعة',     en: 'Total Wattage' },
  'onb-est-kwh':        { ar: 'تقدير استهلاك شهري',   en: 'Estimated Monthly Consumption' },
  'onb-est-cost':       { ar: 'تقدير التكلفة الشهرية', en: 'Estimated Monthly Cost' },
  'onb-save-btn':       { ar: 'حفظ والمتابعة للوحة التحكم ←', en: 'Save and Continue to Dashboard →' },
  'onb-skip-btn':       { ar: 'تخطي هذه الخطوة ←',     en: 'Skip this step ←' },
  'onb-saving':         { ar: 'جاري الحفظ...',        en: 'Saving...' },
  // ─── Dynamic / JS strings ───────────────────────────────────
  'tier-1':             { ar: 'الشريحة الأولى',   en: '1st Tier' },
  'tier-2':             { ar: 'الشريحة الثانية',  en: '2nd Tier' },
  'tier-3':             { ar: 'الشريحة الثالثة',  en: '3rd Tier' },
  'tier-4':             { ar: 'الشريحة الرابعة',  en: '4th Tier' },
  'tier-5':             { ar: 'الشريحة الخامسة',  en: '5th Tier' },
  'tier-6':             { ar: 'الشريحة السادسة',  en: '6th Tier' },
  'tier-7':             { ar: 'الشريحة السابعة',  en: '7th Tier' },
  'ws-status-connected':    { ar: 'متصل',          en: 'Connected' },
  'ws-status-connecting':   { ar: 'جاري الاتصال...', en: 'Connecting...' },
  'ws-status-disconnected': { ar: 'غير متصل',       en: 'Disconnected' },
  'ws-status-error':        { ar: 'خطأ',            en: 'Error' },
  'unit-kwh':               { ar: 'كيلوواط',        en: 'kWh' },
  'unit-watt':              { ar: 'وات',            en: 'W' },
  'alert-ac-high':          { ar: 'التكييف بيسحب طاقة أكتر من المعتاد - يُنصح بالصيانة', en: 'AC is drawing more power than usual - maintenance recommended' },
  'alert-voltage-high':     { ar: 'ارتفاع الجهد إلى {v}V - افصل الأجهزة الحساسة فوراً', en: 'Voltage spike to {v}V - unplug sensitive devices immediately' },
  'alert-voltage-low':      { ar: 'انخفاض الجهد إلى {v}V - تجنب تشغيل الأحمال الثقيلة', en: 'Voltage drop to {v}V - avoid running heavy loads' },
  'alert-current-high':     { ar: 'تيار مرتفع ({i}A) - تحقق من الأجهزة الكبيرة', en: 'High current ({i}A) - check major appliances' },
  'alert-pf-low':           { ar: 'معامل القدرة منخفض ({pf}) - قد تحتاج لتغيير مكثفات', en: 'Low Power Factor ({pf}) - might need capacitor replacement' },
  'log-normal':             { ar: 'قراءة طبيعية',   en: 'Normal Reading' },
  'log-alert':              { ar: '⚠️ تنبيه',        en: '⚠️ Alert' },
  'priority-high':          { ar: '🔴 عالي',        en: '🔴 High' },
  'priority-medium':        { ar: '🟡 متوسط',       en: '🟡 Medium' },
  'priority-low':           { ar: '🟢 منخفض',       en: '🟢 Low' },
  'confirm-unclaim':        { ar: 'هل أنت متأكد من إلغاء ربط الجهاز؟', en: 'Are you sure you want to unclaim the device?' },
  'confirm-skip':           { ar: 'لديك أجهزة غير محفوظة. هل تريد المتابعة بدون حفظ؟', en: 'You have unsaved appliances. Continue without saving?' },
  'error-select-app':       { ar: 'الرجاء اختيار جهاز من القائمة', en: 'Please select an appliance from the list' },
  'error-valid-watt':       { ar: 'الرجاء إدخال استطاعة صحيحة', en: 'Please enter a valid wattage' },
  'error-save':             { ar: 'خطأ أثناء الحفظ',         en: 'Error saving' },
  'error-conn':             { ar: 'خطأ في الاتصال',          en: 'Connection error' },
  'unclaim-label':          { ar: 'إلغاء الربط',      en: 'Unclaim' },
  'status-online':          { ar: 'متصل الآن • آخر تحديث: ', en: 'Online now • Last seen: ' },
  'status-offline':         { ar: 'غير متصل',       en: 'Offline' },
  // ─── Appliances ─────────────────────────────────────────────
  'cat-ac':             { ar: 'تكييف وتبريد',      en: 'Air Conditioning' },
  'cat-heat':           { ar: 'سخانات',            en: 'Heaters' },
  'cat-laundry':        { ar: 'غسيل وتنظيف',       en: 'Laundry' },
  'cat-kitchen':        { ar: 'مطبخ',              en: 'Kitchen' },
  'cat-lights':         { ar: 'إضاءة وترفيه',      en: 'Lights & Fun' },
  'app-ac-15':          { ar: 'تكييف 1.5 حصان',    en: 'AC 1.5hp' },
  'app-ac-225':         { ar: 'تكييف 2.25 حصان',   en: 'AC 2.25hp' },
  'app-ac-3':           { ar: 'تكييف 3 حصان',      en: 'AC 3hp' },
  'app-fridge-14':      { ar: 'ثلاجة 14 قدم',      en: 'Fridge 14ft' },
  'app-fridge-16':      { ar: 'ثلاجة 16 قدم',      en: 'Fridge 16ft' },
  'app-fridge-18':      { ar: 'ثلاجة 18 قدم',      en: 'Fridge 18ft' },
  'app-freezer':        { ar: 'فريزر',             en: 'Freezer' },
  'app-heater-elec':    { ar: 'سخان مياه كهربائي', en: 'Electric Water Heater' },
  'app-heater-fast':    { ar: 'سخان مياه سريع',    en: 'Fast Water Heater' },
  'app-heater-space':   { ar: 'دفاية كهربائية',    en: 'Space Heater' },
  'app-washer':         { ar: 'غسالة ملابس',       en: 'Washing Machine' },
  'app-washer-heat':    { ar: 'غسالة ملابس (سخان)',en: 'Washer (with Heater)' },
  'app-dishwasher':     { ar: 'غسالة أطباق',       en: 'Dishwasher' },
  'app-iron':           { ar: 'مكواة ملابس',       en: 'Iron' },
  'app-vacuum':         { ar: 'مكنسة كهربائية',    en: 'Vacuum Cleaner' },
  'app-microwave':      { ar: 'ميكروويف',          en: 'Microwave' },
  'app-oven':           { ar: 'فرن كهربائي',       en: 'Electric Oven' },
  'app-kettle':         { ar: 'غلاية مياه (كاتل)', en: 'Kettle' },
  'app-blender':        { ar: 'خلاط',              en: 'Blender' },
  'app-airfryer':       { ar: 'قلاية هوائية',      en: 'Air Fryer' },
  'app-tv-led':         { ar: 'تلفزيون LED',       en: 'LED TV' },
  'app-pc':             { ar: 'كمبيوتر مكتبي',     en: 'Desktop PC' },
  'app-laptop':         { ar: 'لاب توب',           en: 'Laptop' },
  'app-room-light':     { ar: 'إضاءة الغرفة',      en: 'Room Lighting' },
  'app-fan':            { ar: 'مروحة',             en: 'Fan' },
  'app-other':          { ar: 'جهاز آخر',          en: 'Other' },
};

const Lang = (() => {
  let current = localStorage.getItem('flsk_lang') || 'ar';

  function set(lang) {
    current = lang;
    localStorage.setItem('flsk_lang', lang);
    location.reload();
  }

  function get() { return current; }

  function t(key) {
    const entry = TRANSLATIONS[key];
    if (!entry) return key;
    return entry[current] || entry['ar'];
  }

  function apply() {
    const html = document.documentElement;
    if (current === 'ar') {
      html.setAttribute('lang', 'ar');
      html.setAttribute('dir', 'rtl');
    } else {
      html.setAttribute('lang', 'en');
      html.setAttribute('dir', 'ltr');
    }

    // Update all elements with data-lang-key
    document.querySelectorAll('[data-lang-key]').forEach(el => {
      const key = el.getAttribute('data-lang-key');
      const val = t(key);
      if (el.tagName === 'INPUT' && el.hasAttribute('placeholder')) {
        // handled separately via data-lang-placeholder
      } else {
        el.innerHTML = val;
      }
    });

    // Placeholders
    document.querySelectorAll('[data-lang-placeholder]').forEach(el => {
      const key = el.getAttribute('data-lang-placeholder');
      el.placeholder = t(key);
    });

    // Labels (for optgroup, etc.)
    document.querySelectorAll('[data-lang-label]').forEach(el => {
      const key = el.getAttribute('data-lang-label');
      el.label = t(key);
    });

    // Update toggle button
    const btn = document.getElementById('flsk-lang-btn');
    if (btn) {
      btn.textContent = current === 'ar' ? '🌐 English' : '🌐 عربي';
    }

    // Page title
    const titleKey = document.documentElement.getAttribute('data-title-key');
    if (titleKey) document.title = t(titleKey);
  }

  function injectToggleButton(containerSelector) {
    if (document.getElementById('flsk-lang-btn')) return;

    const btn = document.createElement('button');
    btn.id = 'flsk-lang-btn';
    btn.textContent = current === 'ar' ? '🌐 English' : '🌐 عربي';
    btn.style.cssText = `
      font-family: 'Cairo', sans-serif;
      background: rgba(99,102,241,0.12);
      border: 1px solid rgba(99,102,241,0.3);
      color: #a5b4fc;
      padding: 6px 14px;
      border-radius: 20px;
      font-size: 13px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s;
      letter-spacing: 0.3px;
    `;
    btn.onmouseenter = () => { btn.style.background = 'rgba(99,102,241,0.25)'; btn.style.color = '#fff'; };
    btn.onmouseleave = () => { btn.style.background = 'rgba(99,102,241,0.12)'; btn.style.color = '#a5b4fc'; };
    btn.onclick = () => set(current === 'ar' ? 'en' : 'ar');

    if (containerSelector) {
      const container = document.querySelector(containerSelector);
      if (container) { container.appendChild(btn); return; }
    }

    // Default: fixed top-left
    btn.style.cssText += 'position:fixed;top:18px;right:18px;z-index:99999;';
    document.body.appendChild(btn);
  }

  return { set, get, t, apply, injectToggleButton };
})();

// Auto-apply on DOMContentLoaded
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => { Lang.apply(); Lang.injectToggleButton(); });
} else {
  Lang.apply();
  Lang.injectToggleButton();
}

// ============================================================
// Theme Toggle System (Light/Dark Mode)
// ============================================================
const Theme = (() => {
  let current = localStorage.getItem('flsk_theme') || 'dark'; // Default is dark

  function toggle() {
    current = current === 'dark' ? 'light' : 'dark';
    localStorage.setItem('flsk_theme', current);
    apply();
  }

  function apply() {
    const html = document.documentElement;
    if (current === 'dark') {
      html.classList.add('dark');
    } else {
      html.classList.remove('dark');
    }
    
    // Update all theme toggle buttons
    document.querySelectorAll('.flsk-theme-btn').forEach(btn => {
      btn.textContent = current === 'dark' ? '☀️' : '🌙';
    });
  }

  return { toggle, apply };
})();

// Apply theme immediately to prevent flashing
Theme.apply();
