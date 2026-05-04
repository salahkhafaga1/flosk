import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.metrics import classification_report, f1_score
import os
import joblib


def train_and_evaluate_isolation_forest(anomalous_df: pd.DataFrame):
    """
    Train an Isolation Forest on the engineered features for anomaly detection.

    Hardware-conscious constraints for eventual ESP32 deployment:
      - n_estimators = 50
      - max_samples  = 256
      - contamination = 0.03 (matches synthetic anomaly ratio)

    Parameters
    ----------
    anomalous_df : pd.DataFrame
        DataFrame containing engineered features + 'is_anomaly' ground-truth column.

    Returns
    -------
    tuple
        (model, predictions) - Trained IsolationForest model and predicted labels.
    """
    # Feature matrix (exclude the ground-truth label)
    feature_cols = [
        "voltage", "current", "active_power", "power_factor",
        "apparent_power", "reactive_power",
        "delta_P", "delta_Q",
        "current_rolling_var_60s",
    ]
    X = anomalous_df[feature_cols].values
    y_true = anomalous_df["is_anomaly"].values

    # ------------------------------------------------------------------
    # TinyML-friendly Isolation Forest
    # ------------------------------------------------------------------
    model = IsolationForest(
        n_estimators=50,
        max_samples=256,
        contamination=0.03,
        random_state=42,
        n_jobs=-1,
    )

    print("[INFO] Training Isolation Forest ...")
    model.fit(X)

    # Predict: sklearn returns 1 (inlier) / -1 (outlier)
    y_pred = model.predict(X)

    # ------------------------------------------------------------------
    # Evaluation
    # ------------------------------------------------------------------
    print("\n" + "=" * 60)
    print("CLASSIFICATION REPORT")
    print("=" * 60)
    print(classification_report(y_true, y_pred, target_names=["Anomaly", "Normal"], labels=[-1, 1]))

    f1 = f1_score(y_true, y_pred, pos_label=-1)
    print(f"F1-Score (Anomaly class, label=-1): {f1:.4f}")

    # Sanity-check overlap
    n_detected = (y_pred == -1).sum()
    n_true = (y_true == -1).sum()
    n_correct = ((y_true == -1) & (y_pred == -1)).sum()
    print(f"\n[INFO] True anomalies     : {n_true}")
    print(f"[INFO] Detected anomalies : {n_detected}")
    print(f"[INFO] Correctly detected : {n_correct}")

    predictions = pd.Series(y_pred, index=anomalous_df.index, name="prediction")
    
    return model, predictions


if __name__ == "__main__":
    from preprocess_energy import load_and_clean_energy_data
    from inject_anomalies import inject_anomalies

    # Get the data path - relative to the ml_models directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    dataset_path = os.path.join(current_dir, "..", "data", "sample_energy_data.csv")
    model_save_path = os.path.join(current_dir, "iforest_model.pkl")

    if not os.path.exists(dataset_path):
        raise FileNotFoundError(
            f"Dataset not found at {dataset_path}. Run preprocess_energy.py first."
        )

    # 1. Load / clean
    print("\n[STEP 1/4] Loading and cleaning data...")
    cleaned_df = load_and_clean_energy_data(dataset_path, use_iterative_imputer=True)
    print(f"✓ Loaded {len(cleaned_df)} rows")

    # 2. Inject anomalies
    print("\n[STEP 2/4] Injecting synthetic anomalies...")
    anomalous_df = inject_anomalies(cleaned_df, anomaly_fraction=0.03, random_state=42)
    print(f"✓ Created {len(anomalous_df)} rows with anomalies")

    # 3. Train & evaluate TinyML Isolation Forest
    print("\n[STEP 3/4] Training Isolation Forest model...")
    model, predictions = train_and_evaluate_isolation_forest(anomalous_df)
    
    # 4. Save model to PKL file
    print("\n[STEP 4/4] Saving model to PKL file...")
    joblib.dump(model, model_save_path)
    print(f"✓ Model saved to: {model_save_path}")
    print(f"✓ File size: {os.path.getsize(model_save_path) / 1024:.2f} KB")
    
    print("\n" + "=" * 60)
    print("✅ TRAINING COMPLETE!")
    print("=" * 60)
    print(f"\n📦 Model saved at: {model_save_path}")
    print(f"   You can load it with: joblib.load('{model_save_path}')")


