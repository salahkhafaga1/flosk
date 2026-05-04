import numpy as np
import pandas as pd
from sklearn.preprocessing import RobustScaler
from feature_engineering import engineer_features
from preprocess_energy import load_and_clean_energy_data
import os

dataset_path = "d:/AI/GProject/sample_energy_data.csv"

print("[INFO] Loading and cleaning data...")
cleaned_df = load_and_clean_energy_data(dataset_path, use_iterative_imputer=True)

print("[INFO] Engineering features and fitting RobustScaler...")
# Recreate the exact feature engineering pipeline to capture scaler params
df = cleaned_df.copy()

# 1. Apparent Power
df['apparent_power'] = df['active_power'] / df['power_factor']

# 2. Reactive Power
diff_sq = df['apparent_power'] ** 2 - df['active_power'] ** 2
diff_sq = diff_sq.clip(lower=0)
df['reactive_power'] = np.sqrt(diff_sq)

# 3. Deltas
df['delta_P'] = df['active_power'].diff()
df['delta_Q'] = df['reactive_power'].diff()

# 4. Rolling variance
df['current_rolling_var_60s'] = df['current'].rolling(window=60, min_periods=1).var()

feature_cols = [
    'voltage', 'current', 'active_power', 'power_factor',
    'apparent_power', 'reactive_power',
    'delta_P', 'delta_Q',
    'current_rolling_var_60s'
]

df_features = df[feature_cols].copy()
df_features = df_features.dropna()

# Fit RobustScaler
scaler = RobustScaler()
scaler.fit(df_features)

median = scaler.center_
iqr = scaler.scale_

print(f"[INFO] Scaler fitted on {len(df_features)} rows.")
print(f"[INFO] Medians: {median}")
print(f"[INFO] IQRs:    {iqr}")

# Export to C++ header
header_path = "d:/AI/GProject/RobustScalerParams.h"
with open(header_path, "w") as f:
    f.write("// Auto-generated RobustScaler parameters for ESP32\n")
    f.write("// DO NOT EDIT MANUALLY\n\n")
    f.write("#ifndef ROBUST_SCALER_PARAMS_H\n")
    f.write("#define ROBUST_SCALER_PARAMS_H\n\n")
    f.write(f"#define N_FEATURES {len(feature_cols)}\n\n")
    
    f.write("static const float SCALER_MEDIAN[N_FEATURES] = {\n  ")
    f.write(", ".join([f"{v:.6f}f" for v in median]))
    f.write("\n};\n\n")
    
    f.write("static const float SCALER_IQR[N_FEATURES] = {\n  ")
    f.write(", ".join([f"{v:.6f}f" for v in iqr]))
    f.write("\n};\n\n")
    
    f.write("#endif // ROBUST_SCALER_PARAMS_H\n")

print(f"[INFO] Exported scaler params to: {header_path}")
