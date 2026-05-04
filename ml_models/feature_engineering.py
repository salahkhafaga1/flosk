import pandas as pd
import numpy as np
from sklearn.preprocessing import RobustScaler
import os


def engineer_features(cleaned_df: pd.DataFrame) -> pd.DataFrame:
    """
    Engineer domain-specific electrical features and apply RobustScaler.

    Features engineered:
      1. Apparent Power (S) = P / PF
      2. Reactive Power (Q) = sqrt(S^2 - P^2)
      3. First-order temporal differences: delta_P, delta_Q
      4. Rolling variance of 'current' over a 60-second window

    Parameters
    ----------
    cleaned_df : pd.DataFrame
        Cleaned DataFrame containing 'voltage', 'current', 'active_power', 'power_factor'.
        Must have a DatetimeIndex.

    Returns
    -------
    pd.DataFrame
        Feature-rich DataFrame with all engineered features and RobustScaler applied.
    """
    df = cleaned_df.copy()

    # ------------------------------------------------------------------
    # 1. Apparent Power (S)
    # ------------------------------------------------------------------
    df['apparent_power'] = df['active_power'] / df['power_factor']

    # ------------------------------------------------------------------
    # 2. Reactive Power (Q) = sqrt(S^2 - P^2)
    # ------------------------------------------------------------------
    # Sensor noise can make (S^2 - P^2) slightly negative.
    # We clamp to zero before taking sqrt to avoid NaNs, and flag noise-driven clamps.
    diff_sq = df['apparent_power'] ** 2 - df['active_power'] ** 2
    negative_count = (diff_sq < 0).sum()
    if negative_count > 0:
        print(f"[WARNING] {negative_count} rows had negative S^2 - P^2 due to sensor noise. Clamping to 0 before sqrt.")
    diff_sq = diff_sq.clip(lower=0)
    df['reactive_power'] = np.sqrt(diff_sq)

    # ------------------------------------------------------------------
    # 3. First-order discrete temporal differences (transient spikes)
    # ------------------------------------------------------------------
    df['delta_P'] = df['active_power'].diff()
    df['delta_Q'] = df['reactive_power'].diff()

    # ------------------------------------------------------------------
    # 4. Rolling variance for 'current' over 60-second window
    # ------------------------------------------------------------------
    df['current_rolling_var_60s'] = df['current'].rolling(window=60, min_periods=1).var()

    # ------------------------------------------------------------------
    # Drop NaNs introduced by diff() before scaling
    # ------------------------------------------------------------------
    feature_cols = [
        'voltage', 'current', 'active_power', 'power_factor',
        'apparent_power', 'reactive_power',
        'delta_P', 'delta_Q',
        'current_rolling_var_60s'
    ]

    # Ensure all required columns exist
    missing_cols = [c for c in feature_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing expected columns in DataFrame: {missing_cols}")

    df_features = df[feature_cols].copy()
    df_features = df_features.dropna()

    # ------------------------------------------------------------------
    # 5. RobustScaler normalization
    # ------------------------------------------------------------------
    scaler = RobustScaler()
    scaled_array = scaler.fit_transform(df_features)
    df_scaled = pd.DataFrame(scaled_array, columns=feature_cols, index=df_features.index)

    print(f"[INFO] RobustScaler fitted on {len(df_scaled)} rows.")
    print(f"[INFO] Features after scaling: {list(df_scaled.columns)}")

    return df_scaled


if __name__ == "__main__":
    # Import the preprocessing function from the previous script
    from preprocess_energy import load_and_clean_energy_data

    dataset_path = "d:/AI/GProject/sample_energy_data.csv"

    if not os.path.exists(dataset_path):
        raise FileNotFoundError(
            f"Cleaned dataset not found at {dataset_path}. "
            "Please run preprocess_energy.py first."
        )

    # Load / clean the raw data
    cleaned_df = load_and_clean_energy_data(dataset_path, use_iterative_imputer=True)

    # Engineer features and scale
    feature_df = engineer_features(cleaned_df)

    print("\n[INFO] Feature-engineered & scaled DataFrame head:")
    print(feature_df.head(10))

    print("\n[INFO] DataFrame info:")
    print(feature_df.info())

