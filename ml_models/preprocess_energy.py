import pandas as pd
import numpy as np
from sklearn.experimental import enable_iterative_imputer  # noqa: F401
from sklearn.impute import IterativeImputer
import os


def generate_sample_data(filepath: str, n_rows: int = 1000, freq: str = "1S", missing_rate: float = 0.05):
    """
    Generate a sample energy dataset similar to iAWE/OMPM for demonstration.
    The dataset includes timestamp, voltage, current, active_power, and power_factor.
    """
    rng = np.random.default_rng(seed=42)
    timestamps = pd.date_range(start="2024-01-01 00:00:00", periods=n_rows, freq=freq.lower())

    # Simulate realistic low-frequency smart-home electrical signals
    voltage = 230 + rng.normal(loc=0, scale=2, size=n_rows)                     # ~230V RMS
    current = 2 + 0.5 * np.sin(np.linspace(0, 20 * np.pi, n_rows)) + rng.normal(loc=0, scale=0.1, size=n_rows)
    active_power = voltage * current * (0.85 + 0.05 * rng.random(size=n_rows))  # P = V * I * PF (approx)
    power_factor = 0.85 + 0.1 * np.sin(np.linspace(0, 10 * np.pi, n_rows)) + rng.normal(loc=0, scale=0.02, size=n_rows)
    power_factor = np.clip(power_factor, 0.5, 1.0)

    df = pd.DataFrame({
        "timestamp": timestamps,
        "voltage": voltage,
        "current": current,
        "active_power": active_power,
        "power_factor": power_factor
    })

    # Introduce missing values to simulate network packet drops
    n_missing = int(n_rows * missing_rate)
    missing_indices = rng.choice(df.index, size=n_missing, replace=False)
    df.loc[missing_indices, ["voltage", "current", "active_power", "power_factor"]] = np.nan

    df.to_csv(filepath, index=False)
    print(f"[INFO] Sample dataset generated at: {filepath}")


def load_and_clean_energy_data(filepath: str, use_iterative_imputer: bool = True) -> pd.DataFrame:
    """
    Load an energy dataset and perform preprocessing:
      1. Parse 'timestamp' and set as datetime index.
      2. Resample to strict 1Hz frequency.
      3. Impute missing values using an advanced interpolation technique.

    Parameters
    ----------
    filepath : str
        Path to the raw CSV dataset.
    use_iterative_imputer : bool, default True
        If True, uses sklearn's IterativeImputer (suitable for multivariate correlations).
        If False, falls back to piecewise-polynomial (cubic spline) interpolation.

    Returns
    -------
    pd.DataFrame
        Cleaned DataFrame with a strict DatetimeIndex at 1Hz.
    """
    # ------------------------------------------------------------------
    # 1. Load raw data
    # ------------------------------------------------------------------
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Dataset not found at: {filepath}")

    df = pd.read_csv(filepath)

    if "timestamp" not in df.columns:
        raise ValueError("Dataset must contain a 'timestamp' column.")

    # Parse timestamps and set as index
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df = df.dropna(subset=["timestamp"])
    df = df.set_index("timestamp")

    # Ensure numeric types for electrical channels
    numeric_cols = ["voltage", "current", "active_power", "power_factor"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # ------------------------------------------------------------------
    # 2. Resample to strict 1Hz
    # ------------------------------------------------------------------
    # First, sort index to guarantee monotonic time
    df = df.sort_index()

    # Aggregate sub-second duplicates by mean (if any) then enforce 1-second bins
    df = df.resample("1s").mean()

    # ------------------------------------------------------------------
    # 3. Advanced imputation of missing values
    # ------------------------------------------------------------------
    # Simple forward-fill is avoided because it artificially elongates transient spikes.
    # We prefer methods that respect the multivariate structure and smoothness of electrical signals.

    missing_before = df.isna().sum().sum()
    print(f"[INFO] Missing values before imputation: {missing_before}")

    if use_iterative_imputer:
        # IterativeImputer models each feature as a function of the others.
        # This is powerful for electrical data where voltage, current, active_power, and power_factor
        # are physically correlated (e.g., P = V * I * PF).
        imputer = IterativeImputer(
            max_iter=10,
            random_state=42,
            sample_posterior=False,  # deterministic imputation
        )
        imputed_array = imputer.fit_transform(df[numeric_cols])
        df_imputed = pd.DataFrame(imputed_array, columns=numeric_cols, index=df.index)
    else:
        # Fallback: cubic spline interpolation (piecewise polynomial, order=3).
        # Suitable for smooth electrical waveforms sampled at 1Hz.
        df_imputed = df[numeric_cols].interpolate(method="polynomial", order=3)
        # In case leading/trailing NaNs remain after interpolation, use limited-direction filling
        df_imputed = df_imputed.interpolate(method="linear", limit_direction="both")

    # Preserve any extra non-numeric columns if present (optional safety)
    extra_cols = [c for c in df.columns if c not in numeric_cols]
    if extra_cols:
        df_imputed = pd.concat([df_imputed, df[extra_cols]], axis=1)

    missing_after = df_imputed.isna().sum().sum()
    print(f"[INFO] Missing values after imputation: {missing_after}")

    return df_imputed


if __name__ == "__main__":
    dataset_path = "d:/AI/GProject/sample_energy_data.csv"

    # Generate sample data if it doesn't exist
    if not os.path.exists(dataset_path):
        generate_sample_data(dataset_path, n_rows=2000, missing_rate=0.05)

    # Run preprocessing pipeline
    cleaned_df = load_and_clean_energy_data(dataset_path, use_iterative_imputer=True)

    print("\n[INFO] Cleaned DataFrame head:")
    print(cleaned_df.head(10))

    print("\n[INFO] DataFrame info:")
    print(cleaned_df.info())

