#!/usr/bin/env python
"""
Test script to load and use the trained Isolation Forest model
"""
import os
import sys
import joblib
import numpy as np

# Add ml_models to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ml_models'))

print("=" * 70)
print("🧪 اختبار تحميل واستخدام النموذج المدرب")
print("=" * 70)

try:
    # Path to model
    model_path = os.path.join(os.path.dirname(__file__), 'ml_models', 'iforest_model.pkl')
    
    print(f"\n[1/4] التحقق من وجود النموذج...")
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"النموذج غير موجود في: {model_path}")
    
    file_size = os.path.getsize(model_path) / 1024
    print(f"✓ النموذج موجود")
    print(f"✓ حجم الملف: {file_size:.2f} KB")
    
    print(f"\n[2/4] تحميل النموذج...")
    model = joblib.load(model_path)
    print(f"✓ تم التحميل بنجاح")
    print(f"✓ نوع النموذج: {type(model).__name__}")
    print(f"✓ عدد الأشجار: {model.n_estimators}")
    print(f"✓ نسبة الشذوذ: {model.contamination}")
    
    print(f"\n[3/4] اختبار على عينة البيانات...")
    
    # Load test data
    from preprocess_energy import load_and_clean_energy_data
    from inject_anomalies import inject_anomalies
    
    dataset_path = os.path.join(os.path.dirname(__file__), 'data', 'sample_energy_data.csv')
    cleaned_df = load_and_clean_energy_data(dataset_path, use_iterative_imputer=True)
    anomalous_df = inject_anomalies(cleaned_df, anomaly_fraction=0.03, random_state=42)
    
    # Prepare features
    feature_cols = [
        "voltage", "current", "active_power", "power_factor",
        "apparent_power", "reactive_power",
        "delta_P", "delta_Q",
        "current_rolling_var_60s",
    ]
    X = anomalous_df[feature_cols].values
    
    # Make predictions
    predictions = model.predict(X)
    anomaly_scores = model.score_samples(X)
    
    # Count results
    n_anomalies_detected = (predictions == -1).sum()
    n_normal_detected = (predictions == 1).sum()
    
    print(f"✓ تم التنبؤ على {len(X)} عينة")
    print(f"✓ عدد الشذوذ المكتشفة: {n_anomalies_detected}")
    print(f"✓ عدد القراءات الطبيعية: {n_normal_detected}")
    
    print(f"\n[4/4] عرض الإحصائيات...")
    
    print(f"\n📊 Anomaly Scores (أقل = شذوذ أكثر احتمالاً):")
    print(f"   الحد الأدنى: {anomaly_scores.min():.4f}")
    print(f"   الحد الأقصى: {anomaly_scores.max():.4f}")
    print(f"   المتوسط: {anomaly_scores.mean():.4f}")
    print(f"   الانحراف المعياري: {anomaly_scores.std():.4f}")
    
    # Show some examples
    print(f"\n📋 أمثلة على التنبؤات:")
    print(f"\n{'Index':<8} {'Prediction':<15} {'Score':<10} {'True Label':<12}")
    print("-" * 50)
    
    n_samples = min(10, len(X))
    for i in range(n_samples):
        pred = "شذوذ 🔴" if predictions[i] == -1 else "طبيعي 🟢"
        true_label = "شذوذ 🔴" if anomalous_df.iloc[i]['is_anomaly'] == -1 else "طبيعي 🟢"
        print(f"{i:<8} {pred:<15} {anomaly_scores[i]:<10.4f} {true_label:<12}")
    
    print(f"\n" + "=" * 70)
    print("✅ النموذج يعمل بشكل صحيح!")
    print("=" * 70)
    
    print(f"\n💡 الاستخدام:")
    print(f"   import joblib")
    print(f"   model = joblib.load('ml_models/iforest_model.pkl')")
    print(f"   predictions = model.predict(X_data)")
    print(f"   anomaly_scores = model.score_samples(X_data)")
    
except Exception as e:
    print(f"\n❌ خطأ: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
