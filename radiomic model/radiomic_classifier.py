"""
Radiomic Classifier for PDAC Stage Prediction
==============================================
Uses simulated radiomic features (tumor phenotype characteristics)
to classify early vs late-stage pancreatic ductal adenocarcinoma (PDAC).
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, accuracy_score

# ─────────────────────────────────────────────
# 1. DATA GENERATION
# ─────────────────────────────────────────────

def generate_radiomic_dataset(n_samples: int = 200, random_state: int = 42) -> pd.DataFrame:
    """
    Synthesise radiomic features with realistic early vs late-stage trends.

    Early stage (label = 0):
        smaller size, higher compactness, lower heterogeneity,
        sharper edges, lower necrosis, lower intensity variance

    Late stage (label = 1):
        larger size, lower compactness, higher heterogeneity,
        blurred edges, higher necrosis, higher intensity variance
    """
    rng = np.random.default_rng(random_state)

    n_early = n_samples // 2
    n_late  = n_samples - n_early

    # --- Early-stage patients ---
    early = pd.DataFrame({
        "Tumor_Size":            rng.normal(loc=2.0,  scale=0.4,  size=n_early),   # cm
        "Tumor_Compactness":     rng.normal(loc=0.75, scale=0.08, size=n_early),   # 0–1
        "Texture_Heterogeneity": rng.normal(loc=0.30, scale=0.06, size=n_early),   # 0–1
        "Edge_Sharpness":        rng.normal(loc=0.80, scale=0.07, size=n_early),   # 0–1
        "Necrosis_Score":        rng.normal(loc=0.20, scale=0.06, size=n_early),   # 0–1
        "Intensity_Variance":    rng.normal(loc=15.0, scale=3.0,  size=n_early),   # a.u.
        "Stage":                 0,
    })

    # --- Late-stage patients ---
    late = pd.DataFrame({
        "Tumor_Size":            rng.normal(loc=4.5,  scale=0.6,  size=n_late),
        "Tumor_Compactness":     rng.normal(loc=0.45, scale=0.08, size=n_late),
        "Texture_Heterogeneity": rng.normal(loc=0.70, scale=0.07, size=n_late),
        "Edge_Sharpness":        rng.normal(loc=0.40, scale=0.08, size=n_late),
        "Necrosis_Score":        rng.normal(loc=0.65, scale=0.08, size=n_late),
        "Intensity_Variance":    rng.normal(loc=45.0, scale=6.0,  size=n_late),
        "Stage":                 1,
    })

    df = (
        pd.concat([early, late], ignore_index=True)
        .sample(frac=1, random_state=random_state)   # shuffle rows
        .reset_index(drop=True)
    )

    # Clip proportional features to valid [0, 1] range
    for col in ["Tumor_Compactness", "Texture_Heterogeneity",
                "Edge_Sharpness", "Necrosis_Score"]:
        df[col] = df[col].clip(0.0, 1.0)

    return df


# ─────────────────────────────────────────────
# 2. MODEL TRAINING & EVALUATION
# ─────────────────────────────────────────────

def train_and_evaluate(df: pd.DataFrame) -> None:
    FEATURE_COLS = [
        "Tumor_Size",
        "Tumor_Compactness",
        "Texture_Heterogeneity",
        "Edge_Sharpness",
        "Necrosis_Score",
        "Intensity_Variance",
    ]
    LABEL_COL = "Stage"

    X = df[FEATURE_COLS].values
    y = df[LABEL_COL].values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    clf = RandomForestClassifier(n_estimators=100, random_state=42)
    clf.fit(X_train, y_train)

    y_pred       = clf.predict(X_test)
    y_prob       = clf.predict_proba(X_test)[:, 1]
    auc          = roc_auc_score(y_test, y_prob)
    accuracy     = accuracy_score(y_test, y_pred)

    # ─────────────────────────────────────────
    # 3. FEATURE IMPORTANCE
    # ─────────────────────────────────────────

    importances = clf.feature_importances_
    ranked = sorted(
        zip(FEATURE_COLS, importances),
        key=lambda x: x[1],
        reverse=True,
    )

    # ─────────────────────────────────────────
    # 4. OUTPUT
    # ─────────────────────────────────────────

    divider = "─" * 42

    print("\n" + divider)
    print("  PDAC Radiomic Stage Classifier — Results")
    print(divider)
    print(f"  ROC-AUC  : {auc:.4f}")
    print(f"  Accuracy : {accuracy:.4f}  ({int(accuracy * len(y_test))}/{len(y_test)} correct)")
    print(divider)

    print("\n  Feature Importance Ranking")
    print(f"  {'Feature':<26} {'Importance':>10}")
    print("  " + "─" * 38)
    for rank, (feature, importance) in enumerate(ranked, start=1):
        bar = "█" * int(importance * 40)
        print(f"  {rank}. {feature:<23} {importance:>10.4f}  {bar}")

    print("\n" + divider + "\n")


# ─────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("Generating synthetic radiomic dataset (200 patients)…")
    df = generate_radiomic_dataset(n_samples=200)

    print(f"Dataset shape : {df.shape}")
    print(f"Class balance : {dict(df['Stage'].value_counts().sort_index())}\n")

    train_and_evaluate(df)
