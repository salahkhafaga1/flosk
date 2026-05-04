# استخدام النموذج المدرب

## 📦 ملف النموذج

**الموقع:** `ml_models/iforest_model.pkl`  
**الحجم:** ~569 KB  
**الصيغة:** joblib (Python pickle)  
**النموذج:** Isolation Forest مع 50 estimators

---

## 🚀 تحميل واستخدام النموذج

### في Python:

```python
import joblib
import numpy as np

# 1. تحميل النموذج
model = joblib.load('ml_models/iforest_model.pkl')

# 2. تحضير البيانات (نفس الميزات المستخدمة في التدريب)
features = np.array([
    [voltage, current, active_power, power_factor, 
     apparent_power, reactive_power, delta_P, delta_Q, 
     current_rolling_var_60s]
])

# 3. التنبؤ
prediction = model.predict(features)

# النتيجة:
# -1 = شذوذ / anomaly
#  1 = طبيعي / normal

if prediction[0] == -1:
    print("⚠️ شذوذ مكتشف!")
else:
    print("✓ قراءة طبيعية")

# 4. احسب score الشذوذ (كلما أقل = شذوذ أكثر احتمالاً)
anomaly_score = model.score_samples(features)
print(f"Anomaly Score: {anomaly_score[0]}")
```

---

## 📊 خصائص النموذج

### معاملات التدريب:
- **n_estimators:** 50 (عدد الأشجار)
- **max_samples:** 256 (حد أقصى للعينات)
- **contamination:** 0.03 (نسبة الشذوذ المتوقعة = 3%)
- **random_state:** 42 (للتكرار)

### أداء النموذج:
```
              precision    recall  f1-score   support

     Anomaly       0.65      0.66      0.66        59
      Normal       0.99      0.99      0.99      1940

    accuracy                           0.98      1999
```

### الميزات المستخدمة (9 ميزات):
1. `voltage` - الجهد الكهربائي
2. `current` - التيار
3. `active_power` - القوة الفعالة
4. `power_factor` - معامل القدرة
5. `apparent_power` - القوة الظاهرة
6. `reactive_power` - القوة التفاعلية
7. `delta_P` - تغير القوة الفعالة
8. `delta_Q` - تغير القوة التفاعلية
9. `current_rolling_var_60s` - التباين المتحرك للتيار (نافذة 60 ثانية)

---

## 📥 تحميل وتصدير إلى C++ (للـ ESP32)

إذا أردت استخدام النموذج على ESP32:

```bash
cd ml_models
python export_iforest_to_cpp.py
python export_scaler_to_cpp.py
```

سينتج عنه:
- `firmware/IsolationForestModel.h` - نموذج C++
- `firmware/RobustScalerParams.h` - معاملات المقياس

---

## 🧪 اختبار النموذج

```python
import joblib
import pandas as pd
from preprocess_energy import load_and_clean_energy_data
from inject_anomalies import inject_anomalies

# تحميل البيانات
df = load_and_clean_energy_data('data/sample_energy_data.csv')
anomalous_df = inject_anomalies(df, anomaly_fraction=0.03, random_state=42)

# تحميل النموذج
model = joblib.load('ml_models/iforest_model.pkl')

# الميزات
feature_cols = [
    "voltage", "current", "active_power", "power_factor",
    "apparent_power", "reactive_power",
    "delta_P", "delta_Q",
    "current_rolling_var_60s",
]
X = anomalous_df[feature_cols].values

# التنبؤ
predictions = model.predict(X)

# حساب الدقة
from sklearn.metrics import classification_report
print(classification_report(
    anomalous_df['is_anomaly'], 
    predictions, 
    target_names=['Anomaly', 'Normal'],
    labels=[-1, 1]
))
```

---

## ⚙️ إعادة تدريب النموذج

إذا أردت إعادة تدريب النموذج بعد الحصول على بيانات جديدة:

```bash
python run_training.py
```

سينشئ ملف `ml_models/iforest_model.pkl` جديد.

---

## 📝 ملاحظات مهمة

- ✅ النموذج **حساس جداً لترتيب الميزات** - يجب استخدام نفس الترتيب دائماً
- ✅ البيانات يجب أن تكون **مُعاملة ومُطبعة نفس طريقة التدريب**
- ✅ استخدم `RobustScaler` للتطبيع قبل الإدخال للنموذج
- ✅ النموذج مصغر **خفيف الوزن** (569 KB) - مناسب للـ ESP32

---

## 🔗 الملفات ذات الصلة

- `ml_models/train_isolation_forest.py` - سكريبت التدريب
- `ml_models/export_iforest_to_cpp.py` - تصدير إلى C++
- `run_training.py` - سكريبت الواجهة العلوية
