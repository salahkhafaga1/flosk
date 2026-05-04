import pandas as pd
import numpy as np
from sklearn.preprocessing import RobustScaler
import os


def inject_anomalies(cleaned_df: pd.DataFrame, anomaly_fraction: float = 0.03, random_state: int = 42):
    """
    Inject synthetic anomalies into exactly `anomaly_fraction` of the data points.

    Two anomaly signatures are injected:

    1. 'Compressor Degradation':
       - 5% drop in 'voltage'   (multiply by 0.95)
       - 20% spike in 'active_power' (multiply by 1.20)
       - 40% spike in 'reactive_power' (multiply by 1.40)

    2. 'Arcing/Loose Contact':
       - Rapid, high-variance oscillations in 'current' and 'power_factor'
         over contiguous ~10-second windows.
       - 'active_power' remains relatively stable (only tiny noise added).

    Parameters
    ----------
    cleaned_df : pd.DataFrame
        Cleaned DataFrame with base columns ['voltage', 'current', 'active_power', 'power_factor']
        and a DatetimeIndex.
    anomaly_fraction : float, default 0.03
        Exact fraction of rows to turn anomalous (3% = 0.03).
    random_state : int, default 42
        Seed for reproducibility.

    Returns
    -------
    pd.DataFrame
        DataFrame with injected anomalies and an 'is_anomaly' column
        (1 = normal, -1 = anomalous).
    """
    df = cleaned_df.copy()
    n_rows = len(df)
    n_anomalies = int(round(n_rows * anomaly_fraction))
    rng = np.random.default_rng(random_state)

    # Initialise label column: 1 = normal, -1 = anomalous
    df["is_anomaly"] = 1

    # ------------------------------------------------------------------
    # Split the anomaly budget evenly between the two signatures
    # ------------------------------------------------------------------
    n_compressor = n_anomalies // 2
    n_arcing = n_anomalies - n_compressor

    # ------------------------------------------------------------------
    # 1. Compressor Degradation — point-wise injections
    # ------------------------------------------------------------------
    compressor_idx = rng.choice(df.index, size=n_compressor, replace=False)
    df.loc[compressor_idx, "voltage"] *= 0.95
    df.loc[compressor_idx, "active_power"] *= 1.20
    df.loc[compressor_idx, "is_anomaly"] = -1

    # ------------------------------------------------------------------
    # 2. Arcing / Loose Contact — contiguous ~10 s blocks
    # ------------------------------------------------------------------
    block_size = 10
    n_blocks = max(1, n_arcing // block_size)
    available_idx = list(df.index)
    arcing_idx = []

    for _ in range(n_blocks):
        if len(available_idx) < block_size + 5:
            break
        start = rng.integers(0, len(available_idx) - block_size + 1)
        block = available_idx[start:start + block_size]
        arcing_idx.extend(block)
        # Remove the block plus a small buffer to avoid overlap
        available_idx = (
            available_idx[:max(0, start - 5)]
            + available_idx[start + block_size + 5:]
        )

    # Trim to the exact budget for arcing
    arcing_idx = arcing_idx[:n_arcing]

    for idx in arcing_idx:
        base_current = df.loc[idx, "current"]
        base_pf = df.loc[idx, "power_factor"]

        # High-variance oscillations (30 % std for current, 15 % std for PF)
        current_osc = rng.normal(0, 0.30 * abs(base_current))
        pf_osc = rng.normal(0, 0.15 * abs(base_pf))

        df.loc[idx, "current"] = base_current + current_osc
        df.loc[idx, "power_factor"] = np.clip(base_pf + pf_osc, 0.3, 1.0)
        # Keep active_power relatively stable — only 2 % gaussian noise
        df.loc[idx, "active_power"] *= (1 + rng.normal(0, 0.02))

    df.loc[arcing_idx, "is_anomaly"] = -1

    # ------------------------------------------------------------------
    # Recompute derived features so they reflect the anomalous signatures
    # ------------------------------------------------------------------
    df["apparent_power"] = df["active_power"] / df["power_factor"]

    diff_sq = df["apparent_power"] ** 2 - df["active_power"] ** 2
    negative_mask = diff_sq < 0
    if negative_mask.any():
        print(f"[WARNING] {negative_mask.sum()} rows had negative S²-P² after injection; clamping to 0.")
    diff_sq = diff_sq.clip(lower=0)
    df["reactive_power"] = np.sqrt(diff_sq)

    # For compressor rows the 20 % P-spike already raised Q by ~20 %.
    # We need a net 40 % spike, so scale by the remaining factor.
    df.loc[compressor_idx, "reactive_power"] *= (1.40 / 1.20)

    # Temporal differences
    df["delta_P"] = df["active_power"].diff()
    df["delta_Q"] = df["reactive_power"].diff()

    # Rolling variance of current (60-second window)
    df["current_rolling_var_60s"] = df["current"].rolling(window=60, min_periods=1).var()

    # ------------------------------------------------------------------
    # RobustScaler — fit only on normal rows, transform everything
    # This prevents the scaler from being biased by the anomalies.
    # ------------------------------------------------------------------
    feature_cols = [
        "voltage", "current", "active_power", "power_factor",
        "apparent_power", "reactive_power",
        "delta_P", "delta_Q",
        "current_rolling_var_60s",
    ]

    df_features = df[feature_cols].copy().dropna()
    normal_mask = df.loc[df_features.index, "is_anomaly"] == 1

    scaler = RobustScaler()
    scaler.fit(df_features[normal_mask])
    scaled_array = scaler.transform(df_features)

    df_scaled = pd.DataFrame(
        scaled_array, columns=feature_cols, index=df_features.index
    )
    df_scaled["is_anomaly"] = df.loc[df_scaled.index, "is_anomaly"].astype(int)

    # Verify exact anomaly fraction
    actual_fraction = (df_scaled["is_anomaly"] == -1).mean()
    print(f"[INFO] Injected {n_anomalies} anomalies ({actual_fraction:.2%} of data).")
    print(f"[INFO]   -> Compressor degradation: {len(compressor_idx)} rows")
    print(f"[INFO]   -> Arcing/loose contact : {len(arcing_idx)} rows")

    return df_scaled


if __name__ == "__main__":
    from preprocess_energy import load_and_clean_energy_data

    dataset_path = "d:/AI/GProject/sample_energy_data.csv"

    if not os.path.exists(dataset_path):
        raise FileNotFoundError(
            f"Dataset not found at {dataset_path}. Run preprocess_energy.py first."
        )

    # 1. Load & clean
    cleaned_df = load_and_clean_energy_data(dataset_path, use_iterative_imputer=True)

    # 2. Inject anomalies (exactly 3 % of rows)
    anomalous_df = inject_anomalies(cleaned_df, anomaly_fraction=0.03, random_state=42)

    print("\n[INFO] Anomalous DataFrame head:")
    print(anomalous_df.head(10))

    print("\n[INFO] Anomaly value counts:")
    print(anomalous_df["is_anomaly"].value_counts())

    print("\n[INFO] DataFrame info:")
    print(anomalous_df.info())

