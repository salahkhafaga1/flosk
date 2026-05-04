"""
export_iforest_to_cpp.py

Trains the TinyML Isolation Forest and exports every tree into a self-contained
C++ header (IsolationForestModel.h) suitable for ESP32 (no STL, no heap allocs).
"""

import os
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.metrics import classification_report, f1_score

# ---------------------------------------------------------------------------
# 1. Load / clean / inject (same pipeline as before)
# ---------------------------------------------------------------------------
from preprocess_energy import load_and_clean_energy_data
from inject_anomalies import inject_anomalies

dataset_path = "d:/AI/GProject/sample_energy_data.csv"
cleaned_df = load_and_clean_energy_data(dataset_path, use_iterative_imputer=True)
anomalous_df = inject_anomalies(cleaned_df, anomaly_fraction=0.03, random_state=42)

feature_cols = [
    "voltage", "current", "active_power", "power_factor",
    "apparent_power", "reactive_power",
    "delta_P", "delta_Q",
    "current_rolling_var_60s",
]
X = anomalous_df[feature_cols].values.astype(np.float32)
y_true = anomalous_df["is_anomaly"].values

# ---------------------------------------------------------------------------
# 2. Train the model
# ---------------------------------------------------------------------------
model = IsolationForest(
    n_estimators=50,
    max_samples=256,
    contamination=0.03,
    random_state=42,
    n_jobs=-1,
)
model.fit(X)

# Quick sanity-check
y_pred = model.predict(X)
print("\n" + "=" * 60)
print("CLASSIFICATION REPORT")
print("=" * 60)
print(classification_report(y_true, y_pred, target_names=["Anomaly", "Normal"], labels=[-1, 1]))
print(f"F1-Score (Anomaly): {f1_score(y_true, y_pred, pos_label=-1):.4f}")

# ---------------------------------------------------------------------------
# 3. C++ code generation
# ---------------------------------------------------------------------------

N_FEATURES = len(feature_cols)
N_ESTIMATORS = len(model.estimators_)
MAX_SAMPLES = model.max_samples


def c_average_path_length(n):
    """Harmonic number used by sklearn IsolationForest."""
    if n <= 1:
        return 0.0
    return 2.0 * (np.log(n - 1) + 0.5772156649) - 2.0 * (n - 1) / n


C_VAL = c_average_path_length(MAX_SAMPLES)

# Build per-tree flat arrays
tree_nodes = []   # list of dicts, one per tree
tree_offsets = [] # offset into the global arrays for each tree

for est in model.estimators_:
    tree = est.tree_
    n_nodes = tree.node_count
    tree_nodes.append({
        "n_nodes": n_nodes,
        "feature": tree.feature.tolist(),
        "threshold": tree.threshold.tolist(),
        "children_left": tree.children_left.tolist(),
        "children_right": tree.children_right.tolist(),
    })

# ---------------------------------------------------------------------------
# Write header
# ---------------------------------------------------------------------------
header_path = "d:/AI/GProject/IsolationForestModel.h"

with open(header_path, "w") as f:
    f.write("// Auto-generated Isolation Forest C++ header for ESP32\n")
    f.write("// DO NOT EDIT MANUALLY\n\n")
    f.write(f"#ifndef ISOLATION_FOREST_MODEL_H\n")
    f.write(f"#define ISOLATION_FOREST_MODEL_H\n\n")

    f.write(f"#define N_FEATURES {N_FEATURES}\n")
    f.write(f"#define N_ESTIMATORS {N_ESTIMATORS}\n")
    f.write(f"#define MAX_SAMPLES {MAX_SAMPLES}\n\n")

    # Flatten all trees into global constant arrays
    all_feature = []
    all_threshold = []
    all_left = []
    all_right = []
    offsets = []

    for t in tree_nodes:
        offsets.append(len(all_feature))
        all_feature.extend(t["feature"])
        all_threshold.extend(t["threshold"])
        all_left.extend(t["children_left"])
        all_right.extend(t["children_right"])

    total_nodes = len(all_feature)

    f.write(f"static const int TOTAL_NODES = {total_nodes};\n\n")

    # Helper to write array
    def write_array(name, arr, dtype="float"):
        f.write(f"static const {dtype} {name}[{len(arr)}] = {{\n  ")
        f.write(", ".join(str(v) for v in arr))
        f.write("\n};\n\n")

    write_array("TREE_FEATURE", all_feature, "int")
    write_array("TREE_THRESHOLD", [f"{v:.6f}f" for v in all_threshold], "float")
    write_array("TREE_LEFT", all_left, "int")
    write_array("TREE_RIGHT", all_right, "int")

    f.write(f"static const int TREE_OFFSET[N_ESTIMATORS] = {{\n  ")
    f.write(", ".join(str(v) for v in offsets))
    f.write("\n};\n\n")

    f.write(f"static const float C_VAL = {C_VAL:.6f}f;\n\n")

    # ------------------------------------------------------------------
    # C++ prediction logic
    # ------------------------------------------------------------------
    f.write("inline float c_average_path_length(int n) {\n")
    f.write("  if (n <= 1) return 0.0f;\n")
    f.write("  return 2.0f * (logf(n - 1) + 0.5772156649f) - 2.0f * (n - 1) / n;\n")
    f.write("}\n\n")

    f.write("inline float path_length(const float* sample, int tree_idx) {\n")
    f.write("  int node = TREE_OFFSET[tree_idx];\n")
    f.write("  float depth = 0.0f;\n")
    f.write("  while (TREE_LEFT[node] != TREE_RIGHT[node]) {\n")
    f.write("    int feat = TREE_FEATURE[node];\n")
    f.write("    float thresh = TREE_THRESHOLD[node];\n")
    f.write("    if (sample[feat] <= thresh) {\n")
    f.write("      node = TREE_LEFT[node] + TREE_OFFSET[tree_idx];\n")
    f.write("    } else {\n")
    f.write("      node = TREE_RIGHT[node] + TREE_OFFSET[tree_idx];\n")
    f.write("    }\n")
    f.write("    depth += 1.0f;\n")
    f.write("  }\n")
    f.write("  depth += c_average_path_length(TREE_LEFT[node]); // leaf size approximation\n")
    f.write("  return depth;\n")
    f.write("}\n\n")

    f.write("float predict_anomaly(const float* features) {\n")
    f.write("  float avg_depth = 0.0f;\n")
    f.write("  for (int i = 0; i < N_ESTIMATORS; ++i) {\n")
    f.write("    avg_depth += path_length(features, i);\n")
    f.write("  }\n")
    f.write("  avg_depth /= N_ESTIMATORS;\n")
    f.write("  float score = powf(2.0f, -avg_depth / C_VAL);\n")
    f.write("  return score;\n")
    f.write("}\n\n")

    f.write("#endif // ISOLATION_FOREST_MODEL_H\n")

print(f"[INFO] C++ header exported to: {header_path}")
print(f"[INFO] Total nodes across {N_ESTIMATORS} trees: {total_nodes}")
print(f"[INFO] Estimated ROM usage: ~{total_nodes * 12 / 1024:.1f} KB")

