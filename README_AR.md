# نظام مراقبة الطاقة المنزلي الذكي
# Smart Home Energy Monitoring System

> **الإصدار:** 3.0 — B2C SaaS مع دعم RTL العربي  
> **المكدس التكنولوجي:** ESP32 (C++) → MQTT → FastAPI (Python) → SQLite → WebSocket → لوحة تحكم HTML/JS  
> **الهدف:** كشف الشذوذ في الطاقة في الوقت الفعلي مع استدلال ML مدعوم بالحافة ، تصور سحابي ، وادعاء الجهاز متعدد المستأجرين

---

## 📁 بنية المشروع المنظمة

```
GProject/
│
├── 📁 backend/                          # خوادم FastAPI والخدمات
│   ├── main.py                          # API الرئيسي + WebSocket + MQTT + Auth
│   ├── database.py                      # نماذج SQLAlchemy (User, Device, Appliance)
│   ├── mqtt_schema_validator.py         # التحقق من صحة الحمول JSON
│   ├── ml_inference_service.py          # عبوة Isolation Forest ML
│   ├── system_health_watchdog.py        # فاحص صحة MQTT و InfluxDB
│   ├── test_integration.py              # اختبار كامل النظام
│   └── mqtt_simulator.py                # محاكاة رسائل MQTT للاختبار
│
├── 📁 frontend/                         # ملفات الواجهة الأمامية (HTML/JS/CSS)
│   ├── static/                          # ملفات ثابتة يخدمها FastAPI
│   │   ├── index.html                   # لوحة التحكم: بطاقات المقاييس، Chart.js
│   │   ├── landing.html                 # صفحة الهبوط الفاخرة (RTL عربي)
│   │   ├── login.html                   # صفحة المصادقة JWT (تسجيل/دخول)
│   │   ├── claim.html                   # تدفق ادعاء الجهاز
│   │   ├── onboarding.html              # الدليل التفاعلي
│   │   ├── app.js                       # عميل WebSocket + حراسة Auth
│   │   ├── dashboard.js                 # منطق لوحة التحكم
│   │   └── style.css                    # المظهر الداكن + دعم RTL
│   └── execute_command.js               # سكريبت تنفيذ الأوامر
│
├── 📁 firmware/                         # رمز ESP32 (C++)
│   ├── ESP32_EnergyAnomalyDetector.ino  # البرنامج الأساسي (أحادي النواة)
│   ├── ESP32_EnergyAnomalyDetector_v2.ino # البرنامج الإنتاجي (ثنائي النواة + WDT)
│   ├── IsolationForestModel.h           # نموذج C++ (تم إنشاؤه تلقائياً)
│   ├── RobustScalerParams.h             # معاملات المقياس (تم إنشاؤها تلقائياً)
│   └── platformio.ini                   # إعدادات بناء PlatformIO
│
├── 📁 ml_models/                        # سكريبتات التدريب والتصدير
│   ├── train_isolation_forest.py        # تدريب نموذج Isolation Forest
│   ├── feature_engineering.py           # استخراج الميزات (الدلتا، التباين المتداول)
│   ├── preprocess_energy.py             # تنظيف وتطبيع البيانات
│   ├── inject_anomalies.py              # حقن الشذوذ الاصطناعي
│   ├── export_iforest_to_cpp.py         # تصدير النموذج إلى رأس C++
│   └── export_scaler_to_cpp.py          # تصدير معاملات المقياس
│
├── 📁 data/                             # ملفات البيانات
│   └── sample_energy_data.csv           # مجموعة بيانات مثالية للتدريب
│
├── 📁 config/                           # ملفات الإعدادات
│   └── requirements.txt                 # المكتبات المطلوبة (pip install -r)
│
├── 📁 docs/                             # التوثيق
│   ├── PROJECT_GUIDE.md                 # دليل المشروع الشامل
│   ├── ENV_SETUP_GUIDE.md               # دليل إعداد البيئة
│   └── TODO.md                          # قائمة المهام المتبقية
│
├── 📁 scripts/                          # سكريبتات الإعداد والأتمتة
│   └── setup_vscode_esp32.ps1           # إصلاح مسارات ESP32 تلقائياً (PowerShell)
│
├── 📁 .vscode/                          # إعدادات VS Code
│   └── c_cpp_properties.json            # IntelliSense للـ ESP32
│
├── 📄 README_AR.md                      # هذا الملف (بالعربية)
├── 📄 .gitignore                        # استبعاد الملفات المؤقتة من Git
└── 📄 energy_monitor.db                 # قاعدة البيانات الحالية (SQLite)

```

---

## 📌 شرح كل مجلد

### 🔷 **backend/** - خادم الواجهة الخلفية
- **main.py**: خادم FastAPI الرئيسي
  - REST API لاستيعاب قراءات الطاقة والاستعلام عن الشذوذ
  - WebSocket لتحديثات لوحة التحكم الحية
  - مشترك MQTT للاستماع إلى بيانات تلمتري ESP32
  - مصادقة JWT وإدارة المستخدمين
  - تكامل خدمة الاستدلال ML و InfluxDB
  
- **database.py**: نماذج SQLAlchemy
  - جداول المستخدم والجهاز والجهاز الكهربائي
  - علاقات وقيود FK
  
- **mqtt_schema_validator.py**: التحقق من صحة الحمول
  - مثل Pydantic لرسائل MQTT من ESP32
  
- **ml_inference_service.py**: عبوة ML
  - تحميل نموذج Isolation Forest المدرب
  - تنبؤات بالشذوذ مع آلية fallback
  
- **system_health_watchdog.py**: فحص الصحة
  - يراقب MQTT و InfluxDB و FastAPI
  
- **test_integration.py**: اختبار E2E
  - فحص معقول للنظام الكامل
  
- **mqtt_simulator.py**: محاكي MQTT
  - محاكاة رسائل الطاقة من ESP32 للاختبار

---

### 🔷 **frontend/** - الواجهة الأمامية
- **static/**: جميع ملفات HTML و JavaScript و CSS
  - لوحة تحكم جميلة مع رسوم بيانية Chart.js
  - دعم RTL كامل للغة العربية
  - المصادقة الآمنة بـ JWT
  - تصفية الأجهزة حسب المستخدم

---

### 🔷 **firmware/** - رمز ESP32
- **ESP32_EnergyAnomalyDetector_v2.ino**: البرنامج الإنتاجي
  - قراءة مستشعرات الطاقة (CT clamps / شنت مقاومة)
  - استدلال ML محلي (Isolation Forest)
  - اتصال WiFi و MQTT
  - ثنائي النواة مع WDT (watchdog timer)
  
- **IsolationForestModel.h**: نموذج C++ (تم إنشاؤه تلقائياً من Python)
  - يتم إنشاؤه بواسطة `ml_models/export_iforest_to_cpp.py`
  
- **RobustScalerParams.h**: معاملات التطبيع (تم إنشاؤها تلقائياً)
  - يتم إنشاؤها بواسطة `ml_models/export_scaler_to_cpp.py`

---

### 🔷 **ml_models/** - التدريب والتصدير
- **train_isolation_forest.py**: تدريب النموذج
  - يقرأ من `data/sample_energy_data.csv`
  - يدرب نموذج Isolation Forest
  
- **feature_engineering.py**: استخراج الميزات
  - حساب الدلتا والمتوسطات المتحركة والتباين
  
- **preprocess_energy.py**: تنظيف البيانات
  - إزالة القيم الشاذة والقيم المفقودة
  
- **inject_anomalies.py**: حقن بيانات شاذة اصطناعية
  - لتحسين جودة التدريب
  
- **export_iforest_to_cpp.py**: تصدير النموذج
  - ينتج عنه `firmware/IsolationForestModel.h`
  
- **export_scaler_to_cpp.py**: تصدير معاملات المقياس
  - ينتج عنه `firmware/RobustScalerParams.h`

---

### 🔷 **data/** - البيانات
- **sample_energy_data.csv**: بيانات مثالية
  - تستخدم في التدريب والاختبار

---

### 🔷 **config/** - الإعدادات
- **requirements.txt**: جميع المكتبات المطلوبة
  - FastAPI, MQTT, SQLAlchemy, scikit-learn, إلخ

---

### 🔷 **docs/** - التوثيق
- **PROJECT_GUIDE.md**: دليل شامل
- **ENV_SETUP_GUIDE.md**: خطوات الإعداد
- **TODO.md**: المهام المتبقية

---

### 🔷 **scripts/** - الأتمتة
- **setup_vscode_esp32.ps1**: إصلاح مسارات ESP32 (Windows PowerShell)

---

## 🚀 البدء السريع

### 1️⃣ تثبيت المكتبات
```bash
pip install -r config/requirements.txt
```

### 2️⃣ تدريب النموذج
```bash
cd ml_models
python train_isolation_forest.py
python export_iforest_to_cpp.py
python export_scaler_to_cpp.py
```

### 3️⃣ تشغيل الخادم
```bash
cd backend
uvicorn main:app --reload
```

### 4️⃣ الوصول إلى لوحة التحكم
```
http://localhost:8000
```

---

## 📚 الملفات المهمة

| الملف | الغرض |
|------|--------|
| `backend/main.py` | خادم FastAPI الرئيسي |
| `frontend/static/index.html` | لوحة التحكم الرئيسية |
| `firmware/ESP32_EnergyAnomalyDetector_v2.ino` | برنامج ESP32 |
| `ml_models/train_isolation_forest.py` | تدريب النموذج |
| `config/requirements.txt` | المكتبات المطلوبة |

---

## ✅ التحقق من الصحة

```bash
# اختبار شامل
python backend/test_integration.py

# فحص صحة النظام
python backend/system_health_watchdog.py

# محاكاة MQTT
python backend/mqtt_simulator.py
```

---

## 🔗 الروابط المهمة

- **دليل إعداد البيئة**: [docs/ENV_SETUP_GUIDE.md](docs/ENV_SETUP_GUIDE.md)
- **دليل المشروع**: [docs/PROJECT_GUIDE.md](docs/PROJECT_GUIDE.md)
- **قائمة المهام**: [docs/TODO.md](docs/TODO.md)

---

**تم التنظيم بنجاح! ✨**
