// ============================================================
// فلوسك / Flowsk - Bilingual Chat Widget (Premium Redesign)
// ============================================================

function getLang() {
  return localStorage.getItem('flsk_lang') || 'ar';
}

const CHAT_RULES_AR = [
  { keywords: ["وصل","ربط","تركيب","إعداد","setup","esp","جهاز","connect"],
    response: `🔧 <b>خطوات تركيب الجهاز:</b><br>1️⃣ اشترِ جهاز ESP32<br>2️⃣ ثبّته بجانب لوحة الكهرباء<br>3️⃣ افتح <a href="/claim" style="color:#22d3ee;text-decoration:underline">ربط الجهاز</a> وأدخل الـ Device ID<br>4️⃣ انتظر الضوء الأخضر ✅` },
  { keywords: ["device id","رقم الجهاز","id الجهاز","كود الجهاز"],
    response: `🔍 <b>فين الـ Device ID؟</b><br>مكتوب على ملصق الجهاز أو بيظهر على Serial Monitor.<br>ادخل <a href="/claim" style="color:#22d3ee;text-decoration:underline">صفحة الربط</a> وحطه.` },
  { keywords: ["فاتورة","تكلفة","جنيه","شريحة","كيلو","kwh","استهلاك"],
    response: `💡 <b>شرائح الكهرباء:</b><br>🔹 الأولى: 0-50 → 0.25 ج/كيلو<br>🔹 الثانية: 51-100 → 0.43 ج/كيلو<br>🔹 الثالثة: 101-200 → 0.70 ج/كيلو<br>🔹 الرابعة: 201-350 → 0.92 ج/كيلو<br>📊 فلوسك بيحسبلك تقديرك لحظياً!` },
  { keywords: ["dashboard","لوحة","بيانات","قراءة","readings","مراقبة"],
    response: `📊 <b>لوحة التحكم:</b><br>⚡ الطاقة الفعلية<br>🔌 الجهد والتيار<br>💰 التكلفة التقديرية<br>🚨 تنبيهات الأعطال<br><a href="/dashboard" style="color:#22d3ee;text-decoration:underline">افتح لوحة التحكم</a>` },
  { keywords: ["وفر","توفير","تقليل","خفض","tips","نصائح","اقتصاد"],
    response: `💡 <b>نصائح التوفير:</b><br>✅ التكييف على 24-26°C<br>✅ افصل الأجهزة (Standby = 10%!)<br>✅ لمبات LED<br>✅ الغسالة بعد 10 مساءً<br>✅ نظّف فلتر التكييف شهرياً<br>🎯 وفر حتى <b>30%</b>!` },
  { keywords: ["تكييف","ac","بارد","حر","درجة حرارة"],
    response: `❄️ <b>التكييف والطاقة:</b><br>بياكل <b>40-60%</b> من البيت!<br>🔹 24°C → وفر 8% لكل درجة<br>🔹 نظّف الفلاتر شهرياً<br>🔹 أغلق النوافذ<br>🔹 وضع Sleep بالليل` },
  { keywords: ["ثلاجة","فريزر","براد","fridge"],
    response: `🧊 <b>الثلاجة:</b><br>✅ 3-5°C<br>✅ متحطش أكل ساخن<br>✅ ابعدها عن الحيط<br>✅ +10 سنين؟ غيّرها` },
  { keywords: ["عطل","خطأ","مشكلة","error","تنبيه","alert","anomaly"],
    response: `🚨 <b>التنبيهات الذكية:</b><br>فلوسك بيكشف الاستهلاك الغير طبيعي بالـ AI.<br>🔹 افتح لوحة التحكم<br>🔹 افصل الجهاز وشغّله<br>🔹 لو مستمر → فني صيانة` },
  { keywords: ["أجهزة","اجهزة","أضف","اضف","onboarding","غسالة","مراوح","لمبات","سخان","فرن","منزل"],
    response: `🏠 <b>إضافة أجهزة منزلك:</b><br>1️⃣ سجّل دخولك أولاً<br>2️⃣ افتح <a href="/onboarding" style="color:#22d3ee;text-decoration:underline">إعداد الأجهزة</a><br>3️⃣ اختار أجهزتك من القائمة<br>4️⃣ حدد العدد والواتية<br>5️⃣ اضغط حفظ ✅<br>👉 <a href="/onboarding" style="color:#22d3ee;text-decoration:underline;font-weight:bold">ابدأ الآن →</a>` },
  { keywords: ["سجل","تسجيل","حساب","register","login","دخول","كلمة سر"],
    response: `👤 <b>إنشاء حساب:</b><br>1️⃣ <a href="/login" style="color:#22d3ee;text-decoration:underline">تسجيل الدخول</a><br>2️⃣ اختار "حساب جديد"<br>3️⃣ أدخل الإيميل وكلمة السر<br>مجاني <b>14 يوم</b> 🎉` },
  { keywords: ["سعر","اشتراك","مجاني","free","pricing","كام","بكام"],
    response: `💰 <b>الأسعار:</b><br>🆓 مجاني 14 يوم<br>💎 بعدها 99 جنيه/شهر<br><a href="/login" style="color:#22d3ee;text-decoration:underline">ابدأ مجاناً 🚀</a>` },
  { keywords: ["مرحبا","هلو","أهلا","هاي","hi","hello","السلام","ازيك"],
    response: `👋 أهلاً بيك في <b>فلوسك</b>!<br>هساعدك في:<br>⚡ فهم استهلاكك<br>💡 توفير الطاقة<br>🔧 إعداد جهازك` },
  { keywords: ["شكر","thank","تمام","ممتاز","حلو","كويس"],
    response: `😊 العفو! أنا دايماً هنا.<br>في أي سؤال تاني؟ 🌟` }
];

const CHAT_RULES_EN = [
  { keywords: ["connect","setup","esp","device","install","wire"],
    response: `🔧 <b>Device Setup:</b><br>1️⃣ Get an ESP32 device<br>2️⃣ Install near your electrical panel<br>3️⃣ Open <a href="/claim" style="color:#22d3ee;text-decoration:underline">Device Connect</a> & enter Device ID<br>4️⃣ Wait for green light ✅` },
  { keywords: ["device id","serial","code"],
    response: `🔍 <b>Finding Device ID:</b><br>Printed on the device label or shown on Serial Monitor at first boot.<br>Go to <a href="/claim" style="color:#22d3ee;text-decoration:underline">Connect page</a>.` },
  { keywords: ["bill","cost","price","egp","tier","kwh","consumption","tariff"],
    response: `💡 <b>Egyptian Electricity Tiers:</b><br>🔹 Tier 1: 0-50 kWh → 0.25 EGP<br>🔹 Tier 2: 51-100 → 0.43 EGP<br>🔹 Tier 3: 101-200 → 0.70 EGP<br>🔹 Tier 4: 201-350 → 0.92 EGP<br>📊 Flowsk calculates your estimate in real-time!` },
  { keywords: ["dashboard","data","readings","monitor","panel"],
    response: `📊 <b>Dashboard:</b><br>⚡ Real-time power<br>🔌 Voltage & current<br>💰 Monthly cost estimate<br>🚨 Fault alerts<br><a href="/dashboard" style="color:#22d3ee;text-decoration:underline">Open Dashboard</a>` },
  { keywords: ["save","saving","reduce","tips","efficient","lower"],
    response: `💡 <b>Energy Saving Tips:</b><br>✅ Set AC to 24-26°C<br>✅ Unplug standby devices (saves 10%!)<br>✅ Use LED bulbs<br>✅ Run washer after 10 PM<br>✅ Clean AC filter monthly<br>🎯 Save up to <b>30%</b>!` },
  { keywords: ["ac","air condition","cool","heat","temperature"],
    response: `❄️ <b>AC & Energy:</b><br>AC uses <b>40-60%</b> of home power!<br>🔹 24°C saves 8% per degree<br>🔹 Clean filters monthly<br>🔹 Close windows & doors<br>🔹 Use Sleep mode at night` },
  { keywords: ["fridge","freezer","refrigerator"],
    response: `🧊 <b>Fridge Tips:</b><br>✅ Set to 3-5°C<br>✅ Don't put hot food inside<br>✅ Keep away from walls<br>✅ 10+ years old? Replace it` },
  { keywords: ["fault","error","problem","alert","anomaly","warning"],
    response: `🚨 <b>Smart Alerts:</b><br>Flowsk uses AI to detect abnormal consumption.<br>🔹 Check the dashboard<br>🔹 Restart the device<br>🔹 If persistent → call a technician` },
  { keywords: ["appliance","add","onboarding","washer","fan","light","heater","oven","home"],
    response: `🏠 <b>Add Home Appliances:</b><br>1️⃣ Sign in first<br>2️⃣ Open <a href="/onboarding" style="color:#22d3ee;text-decoration:underline">Appliance Setup</a><br>3️⃣ Pick your appliances<br>4️⃣ Set quantity & wattage<br>5️⃣ Save ✅<br>👉 <a href="/onboarding" style="color:#22d3ee;text-decoration:underline;font-weight:bold">Start Now →</a>` },
  { keywords: ["register","login","sign","account","password"],
    response: `👤 <b>Create Account:</b><br>1️⃣ Go to <a href="/login" style="color:#22d3ee;text-decoration:underline">Sign In</a><br>2️⃣ Click "New Account"<br>3️⃣ Enter email & password<br>Free for <b>14 days</b> 🎉` },
  { keywords: ["price","plan","subscription","free","pricing","how much"],
    response: `💰 <b>Pricing:</b><br>🆓 Free for 14 days<br>💎 Then 99 EGP/month<br><a href="/login" style="color:#22d3ee;text-decoration:underline">Start Free 🚀</a>` },
  { keywords: ["hello","hi","hey","good","morning","how are"],
    response: `👋 Welcome to <b>Flowsk</b>!<br>I can help with:<br>⚡ Understanding consumption<br>💡 Energy saving tips<br>🔧 Device setup` },
  { keywords: ["thank","great","nice","good","cool","awesome"],
    response: `😊 You're welcome! I'm always here.<br>Any other questions? 🌟` }
];

const FALLBACK_AR = `🤔 مش فاهم سؤالك.<br>جرب تسأل عن:<br>🔧 إعداد الجهاز<br>⚡ الاستهلاك<br>💡 نصائح التوفير<br>🚨 التنبيهات`;
const FALLBACK_EN = `🤔 I didn't understand that.<br>Try asking about:<br>🔧 Device setup<br>⚡ Consumption<br>💡 Saving tips<br>🚨 Alerts`;

const QUICK_AR = [
  { text: "🏠 أضف أجهزتك", query: "أضيف أجهزة منزلي" },
  { text: "💡 نصائح التوفير", query: "نصائح توفير" },
  { text: "🔧 إعداد الجهاز", query: "كيف أوصل الجهاز" },
  { text: "📊 الاستهلاك", query: "كيف أشوف الاستهلاك" },
];
const QUICK_EN = [
  { text: "🏠 Add Appliances", query: "add home appliances" },
  { text: "💡 Saving Tips", query: "energy saving tips" },
  { text: "🔧 Setup Device", query: "how to connect device" },
  { text: "📊 Consumption", query: "how to monitor consumption" },
];

function getBotResponse(input) {
  const lang = getLang();
  const rules = lang === 'en' ? CHAT_RULES_EN : CHAT_RULES_AR;
  const fallback = lang === 'en' ? FALLBACK_EN : FALLBACK_AR;
  const lower = input.toLowerCase();
  for (const r of rules) {
    if (r.keywords.some(k => lower.includes(k))) return r.response;
  }
  return fallback;
}

function createWidget() {
  const lang = getLang();
  const isEn = lang === 'en';
  const quickReplies = isEn ? QUICK_EN : QUICK_AR;

  const style = document.createElement('style');
  style.textContent = `
    /* ── Chat Button ── */
    #flsk-chat-btn{position:fixed;bottom:28px;left:28px;z-index:9999;width:60px;height:60px;border-radius:50%;background:linear-gradient(135deg,#06b6d4,#7c3aed);border:none;cursor:pointer;box-shadow:0 8px 32px rgba(6,182,212,0.3),0 0 0 4px rgba(6,182,212,0.08);display:flex;align-items:center;justify-content:center;font-size:24px;transition:all .3s cubic-bezier(.34,1.56,.64,1)}
    #flsk-chat-btn:hover{transform:scale(1.1);box-shadow:0 12px 40px rgba(6,182,212,0.4),0 0 0 6px rgba(6,182,212,0.12)}
    #flsk-chat-btn .badge{position:absolute;top:-2px;right:-2px;width:20px;height:20px;background:#ef4444;border-radius:50%;font-size:10px;color:#fff;display:flex;align-items:center;justify-content:center;font-weight:bold;border:2px solid #050816;box-shadow:0 2px 8px rgba(239,68,68,0.4)}
    :is(html:not(.dark)) #flsk-chat-btn .badge{border-color:#ffffff;}
    
    /* ── Chat Panel ── */
    #flsk-chat-panel{position:fixed;bottom:100px;left:28px;z-index:9998;width:380px;max-height:560px;border-radius:24px;display:flex;flex-direction:column;transform:scale(.92) translateY(16px);opacity:0;pointer-events:none;transition:all .35s cubic-bezier(.34,1.56,.64,1);font-family:'Cairo',sans-serif;overflow:hidden}
    #flsk-chat-panel.open{transform:scale(1) translateY(0);opacity:1;pointer-events:all}
    
    :is(.dark) #flsk-chat-panel{background:linear-gradient(180deg,#0f172a 0%,#050816 100%);border:1px solid rgba(6,182,212,0.15);box-shadow:0 24px 64px rgba(0,0,0,.7),0 0 0 1px rgba(6,182,212,0.06)}
    :is(html:not(.dark)) #flsk-chat-panel{background:#ffffff;border:1px solid #e2e8f0;box-shadow:0 20px 40px rgba(0,0,0,.12)}

    /* ── Header ── */
    #flsk-chat-header{background:linear-gradient(135deg,#0891b2 0%,#7c3aed 100%);padding:16px 20px;display:flex;align-items:center;justify-content:space-between}
    #flsk-chat-header .info{display:flex;align-items:center;gap:12px}
    #flsk-chat-header .avatar{width:38px;height:38px;border-radius:12px;background:rgba(255,255,255,0.15);backdrop-filter:blur(10px);display:flex;align-items:center;justify-content:center;font-size:18px;border:1px solid rgba(255,255,255,0.2)}
    #flsk-chat-header .name{font-weight:700;color:#fff;font-size:14px}
    #flsk-chat-header .status{font-size:10px;color:#c7d2fe;display:flex;align-items:center;gap:4px}
    #flsk-chat-header .status::before{content:'';width:5px;height:5px;background:#4ade80;border-radius:50%;display:inline-block;box-shadow:0 0 6px rgba(74,222,128,0.6)}
    #flsk-chat-header button{background:rgba(255,255,255,.1);border:none;cursor:pointer;color:#fff;width:30px;height:30px;border-radius:10px;font-size:13px;display:flex;align-items:center;justify-content:center;transition:background .15s}
    #flsk-chat-header button:hover{background:rgba(255,255,255,.2)}
    
    /* ── Messages ── */
    #flsk-chat-messages{flex:1;overflow-y:auto;padding:14px 16px;display:flex;flex-direction:column;gap:8px;direction:${isEn?'ltr':'rtl'};min-height:200px}
    #flsk-chat-messages::-webkit-scrollbar{width:3px}
    #flsk-chat-messages::-webkit-scrollbar-track{background:transparent}
    #flsk-chat-messages::-webkit-scrollbar-thumb{background:rgba(6,182,212,0.2);border-radius:4px}
    
    .msg{max-width:88%;padding:10px 14px;border-radius:16px;font-size:13px;line-height:1.6;animation:msgIn .25s cubic-bezier(.2,.9,.2,1)}
    @keyframes msgIn{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}
    
    .msg.bot{border-radius:16px 16px 16px 4px;align-self:${isEn?'flex-start':'flex-end'};}
    :is(.dark) .msg.bot{background:linear-gradient(135deg,#1e293b,#0f172a);color:#e2e8f0;border:1px solid rgba(6,182,212,0.08)}
    :is(html:not(.dark)) .msg.bot{background:#f1f5f9;color:#0f172a;border:1px solid #e2e8f0;}
    
    .msg.user{background:linear-gradient(135deg,#0891b2,#7c3aed);color:#fff;border-radius:16px 16px 4px 16px;align-self:${isEn?'flex-end':'flex-start'}}
    
    .msg a{color:#22d3ee!important;text-decoration:underline}
    :is(html:not(.dark)) .msg a{color:#0891b2!important;}
    
    /* ── Typing ── */
    .typing{display:flex;gap:4px;padding:10px 14px;border-radius:16px;align-self:${isEn?'flex-start':'flex-end'};width:fit-content;}
    :is(.dark) .typing{background:linear-gradient(135deg,#1e293b,#0f172a);border:1px solid rgba(6,182,212,0.08)}
    :is(html:not(.dark)) .typing{background:#f1f5f9;border:1px solid #e2e8f0;}
    .typing span{width:6px;height:6px;background:#06b6d4;border-radius:50%;animation:bounce .9s infinite}
    .typing span:nth-child(2){animation-delay:.15s}
    .typing span:nth-child(3){animation-delay:.3s}
    @keyframes bounce{0%,60%,100%{transform:translateY(0)}30%{transform:translateY(-5px)}}
    
    /* ── Quick Replies ── */
    #flsk-quick-replies{padding:0 14px 10px;display:flex;flex-wrap:wrap;gap:4px;direction:${isEn?'ltr':'rtl'};justify-content:${isEn?'flex-start':'flex-end'}}
    .quick-btn{padding:5px 12px;border-radius:16px;font-size:11px;cursor:pointer;transition:all .2s;font-family:'Cairo',sans-serif;font-weight:600}
    :is(.dark) .quick-btn{background:rgba(6,182,212,0.06);border:1px solid rgba(6,182,212,0.15);color:#22d3ee;}
    :is(html:not(.dark)) .quick-btn{background:#f8fafc;border:1px solid #cbd5e1;color:#0891b2;}
    .quick-btn:hover{transform:translateY(-1px)}
    :is(.dark) .quick-btn:hover{background:#06b6d4;color:#fff;border-color:#06b6d4;}
    :is(html:not(.dark)) .quick-btn:hover{background:#e0e7ff;border-color:#818cf8;}
    
    /* ── Input Row ── */
    #flsk-chat-input-row{padding:12px 14px;display:flex;gap:8px;align-items:center;}
    :is(.dark) #flsk-chat-input-row{border-top:1px solid rgba(6,182,212,0.08);background:rgba(15,23,42,0.4)}
    :is(html:not(.dark)) #flsk-chat-input-row{border-top:1px solid #e2e8f0;background:#ffffff}
    
    #flsk-chat-input{flex:1;border-radius:14px;padding:8px 14px;font-size:13px;outline:none;font-family:'Cairo',sans-serif;direction:${isEn?'ltr':'rtl'};transition:all .2s}
    :is(.dark) #flsk-chat-input{background:rgba(30,41,59,0.5);border:1px solid rgba(6,182,212,0.1);color:#e2e8f0;}
    :is(html:not(.dark)) #flsk-chat-input{background:#f8fafc;border:1px solid #cbd5e1;color:#0f172a;}
    #flsk-chat-input:focus{border-color:#06b6d4;box-shadow:0 0 0 3px rgba(6,182,212,0.1)}
    :is(.dark) #flsk-chat-input::placeholder{color:#475569}
    :is(html:not(.dark)) #flsk-chat-input::placeholder{color:#94a3b8}
    
    #flsk-send-btn{width:38px;height:38px;background:linear-gradient(135deg,#06b6d4,#7c3aed);border:none;border-radius:12px;cursor:pointer;color:#fff;font-size:15px;display:flex;align-items:center;justify-content:center;flex-shrink:0;transition:all .2s}
    #flsk-send-btn:hover{transform:scale(1.08);box-shadow:0 4px 16px rgba(6,182,212,0.3)}
  `;
  document.head.appendChild(style);

  const headerName = isEn ? 'Flowsk Assistant' : 'مساعد فلوسك';
  const headerStatus = isEn ? 'Online now' : 'متاح الآن';
  const placeholder = isEn ? 'Ask me anything...' : 'اكتب سؤالك هنا...';

  const wrapper = document.createElement('div');
  wrapper.innerHTML = `
    <button id="flsk-chat-btn" title="${isEn?'Chat with assistant':'تحدث مع المساعد'}">💬<span class="badge">1</span></button>
    <div id="flsk-chat-panel">
      <div id="flsk-chat-header">
        <div class="info"><div class="avatar">⚡</div><div><div class="name">${headerName}</div><div class="status">${headerStatus}</div></div></div>
        <button id="flsk-close-btn" title="${isEn?'Close':'إغلاق'}">✕</button>
      </div>
      <div id="flsk-chat-messages"></div>
      <div id="flsk-quick-replies">${quickReplies.map(q=>`<button class="quick-btn" data-query="${q.query}">${q.text}</button>`).join('')}</div>
      <div id="flsk-chat-input-row">
        ${isEn?'':'<button id="flsk-send-btn">➤</button>'}
        <input id="flsk-chat-input" type="text" placeholder="${placeholder}" maxlength="200">
        ${isEn?'<button id="flsk-send-btn">➤</button>':''}
      </div>
    </div>`;
  document.body.appendChild(wrapper);

  const btn = document.getElementById('flsk-chat-btn');
  const panel = document.getElementById('flsk-chat-panel');
  const closeBtn = document.getElementById('flsk-close-btn');
  const messages = document.getElementById('flsk-chat-messages');
  const input = document.getElementById('flsk-chat-input');
  const sendBtn = document.getElementById('flsk-send-btn');
  const badge = btn.querySelector('.badge');
  let isOpen = false;

  function toggle() { isOpen = !isOpen; panel.classList.toggle('open', isOpen); if(isOpen){badge.style.display='none';setTimeout(()=>input.focus(),300);} }
  function addMsg(h,type) { const d=document.createElement('div');d.className=`msg ${type}`;d.innerHTML=h;messages.appendChild(d);messages.scrollTop=messages.scrollHeight; }
  function showTyping() { const t=document.createElement('div');t.className='typing';t.innerHTML='<span></span><span></span><span></span>';messages.appendChild(t);messages.scrollTop=messages.scrollHeight;return t; }
  function send(text) { text=text.trim();if(!text)return;addMsg(text,'user');input.value='';const t=showTyping();setTimeout(()=>{t.remove();addMsg(getBotResponse(text),'bot');},600+Math.random()*400); }

  btn.addEventListener('click', toggle);
  closeBtn.addEventListener('click', toggle);
  sendBtn.addEventListener('click', () => send(input.value));
  input.addEventListener('keydown', e => { if(e.key==='Enter') send(input.value); });
  document.querySelectorAll('.quick-btn').forEach(b => b.addEventListener('click', () => send(b.dataset.query)));

  const welcome = isEn
    ? '👋 Hi! I\'m the <b>Flowsk</b> assistant.<br>Ask me about consumption, savings, or device setup! ⚡'
    : '👋 أهلاً! أنا مساعد <b>فلوسك</b>.<br>اسألني عن الاستهلاك، التوفير، أو إعداد جهازك! ⚡';
  setTimeout(() => addMsg(welcome, 'bot'), 500);
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', createWidget);
} else { createWidget(); }