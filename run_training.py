#!/usr/bin/env python
"""
Simple script to run model training with model saving
"""
import sys
import os

# Add ml_models to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ml_models'))

print("=" * 60)
print("🚀 جاري تشغيل تدريب النموذج...")
print("=" * 60)

try:
    # Change to ml_models directory
    os.chdir(os.path.join(os.path.dirname(__file__), 'ml_models'))
    
    # Import and run
    from train_isolation_forest import train_and_evaluate_isolation_forest
    from preprocess_energy import load_and_clean_energy_data
    from inject_anomalies import inject_anomalies
    import joblib
    
    print("\n[1/4] تحميل وتنظيف البيانات...")
    dataset_path = os.path.join(os.path.dirname(__file__), 'data', 'sample_energy_data.csv')
    cleaned_df = load_and_clean_energy_data(dataset_path, use_iterative_imputer=True)
    print(f"✓ تم تحميل {len(cleaned_df)} صف من البيانات")
    
    print("\n[2/4] حقن البيانات الشاذة...")
    anomalous_df = inject_anomalies(cleaned_df, anomaly_fraction=0.03, random_state=42)
    print(f"✓ تم إنشاء {len(anomalous_df)} صف مع بيانات شاذة")
    
    print("\n[3/4] تدريب نموذج Isolation Forest...")
    model, predictions = train_and_evaluate_isolation_forest(anomalous_df)
    print("✓ تم التدريب بنجاح!")
    
    print("\n[4/4] حفظ النموذج...")
    model_path = os.path.join(os.path.dirname(__file__), 'ml_models', 'iforest_model.pkl')
    joblib.dump(model, model_path)
    file_size = os.path.getsize(model_path) / 1024
    print(f"✓ تم حفظ النموذج في: {model_path}")
    print(f"✓ حجم الملف: {file_size:.2f} KB")
    
    print("\n" + "=" * 60)
    print("✅ اكتمل التدريب والحفظ بنجاح!")
    print("=" * 60)
    print(f"\n📦 النموذج محفوظ في: {model_path}")
    print(f"   يمكنك تحميله مع: joblib.load('{model_path}')")
    
except Exception as e:
    print(f"\n❌ خطأ: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

