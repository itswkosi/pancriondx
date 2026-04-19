"""
Transcriptomic Classifier for PDAC Stage Prediction
====================================================
Uses RNA-seq gene expression to classify early (stage I/II) vs late (stage III/IV)
pancreatic ductal adenocarcinoma (PDAC) and identifies key expression shifts.

Pipeline
--------
1.  Accept a patient × gene expression DataFrame + binary labels (0=early, 1=late).
2.  Preprocess: log-transform then z-score normalization.
3.  Train LogisticRegression and RandomForestClassifier (80/20 split, random_state=42).
4.  Evaluate: ROC-AUC and Accuracy on the held-out test set.
5.  Differential expression: mean expression per group → (late − early) shift.
6.  Report: AUC, accuracy, ranked gene shifts, top up/downregulated genes.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score, accuracy_score

import warnings
warnings.filterwarnings("ignore")

# ── Constants ────────────────────────────────────────────────────────────────

RANDOM_STATE: int = 42
TEST_SIZE: float = 0.20
LOG_PSEUDOCOUNT: float = 1.0          # added before log2 to avoid log(0)
TOP_N_GENES: int = 5                  # genes to highlight in the report


# ── 1. Synthetic data generator (for standalone execution) ────────────────────

def make_synthetic_expression_data(
    n_patients: int = 200,
    random_state: int = RANDOM_STATE,
) -> tuple[pd.DataFrame, pd.Series]:
    """
    Generate a realistic synthetic RNA-seq count matrix for PDAC.

    Returns
    -------
    X : DataFrame  shape (n_patients, n_genes)  — raw counts (TPM-like)
    y : Series     shape (n_patients,)           — 0 = early, 1 = late
    """
    rng = np.random.default_rng(random_state)

    genes = [
        # Oncogenes / proliferation
        "KRAS", "MYC", "EGFR", "ERBB2", "MKI67",
        # Tumour suppressors
        "TP53", "SMAD4", "CDKN2A", "BRCA2", "ARID1A",
        # EMT / invasion
        "VIM", "CDH1", "SNAI1", "TWIST1", "FN1",
        # Stroma / signalling
        "ACTA2", "FAP", "COL1A1", "TGFB1", "VEGFA",
    ]
    n_genes = len(genes)
    n_early = n_patients // 2
    n_late = n_patients - n_early

    # Base expression drawn from log-normal (mimics TPM counts)
    base_mean = rng.uniform(2.0, 6.0, size=n_genes)   # log-space centres
    base_std = rng.uniform(0.4, 0.8, size=n_genes)

    X_early = np.exp(rng.normal(base_mean, base_std, size=(n_early, n_genes)))
    X_late = np.exp(
        rng.normal(
            base_mean + rng.uniform(-0.8, 1.2, size=n_genes),   # stage shift
            base_std,
            size=(n_late, n_genes),
        )
    )

    X = np.vstack([X_early, X_late])
    y_vals = np.array([0] * n_early + [1] * n_late)

    X_df = pd.DataFrame(X, columns=genes)
    y_series = pd.Series(y_vals, name="stage")

    print(f"✓ Synthetic data: {n_patients} patients × {n_genes} genes")
    print(f"  Early (0): {n_early}   Late (1): {n_late}\n")
    return X_df, y_series


# ── 2. Preprocessing ──────────────────────────────────────────────────────────

def preprocess(X: pd.DataFrame) -> pd.DataFrame:
    """
    Two-step normalisation:
      (a) log2(x + 1)  — stabilises variance across the expression range.
      (b) z-score per gene  — centres and scales each gene to mean=0, std=1.

    Parameters
    ----------
    X : raw count / TPM expression DataFrame

    Returns
    -------
    X_norm : normalised DataFrame (same columns and index)
    """
    # (a) log2 transform
    X_log = np.log2(X + LOG_PSEUDOCOUNT)

    # (b) z-score across patients for each gene
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_log)

    return pd.DataFrame(X_scaled, columns=X.columns, index=X.index)


# ── 3. Model training ─────────────────────────────────────────────────────────

def train_models(
    X_train: np.ndarray,
    y_train: np.ndarray,
) -> dict[str, LogisticRegression | RandomForestClassifier]:
    """
    Train a LogisticRegression and a RandomForestClassifier.

    Both use class_weight='balanced' to handle mild class imbalance.
    """
    models = {
        "LogisticRegression": LogisticRegression(
            max_iter=1000,
            class_weight="balanced",
            random_state=RANDOM_STATE,
        ),
        "RandomForest": RandomForestClassifier(
            n_estimators=200,
            max_depth=6,
            class_weight="balanced",
            random_state=RANDOM_STATE,
        ),
    }

    for name, model in models.items():
        model.fit(X_train, y_train)
        print(f"✓ Trained {name}")

    return models


# ── 4. Evaluation ─────────────────────────────────────────────────────────────

def evaluate_models(
    models: dict,
    X_test: np.ndarray,
    y_test: np.ndarray,
) -> dict[str, dict[str, float]]:
    """
    Compute ROC-AUC and Accuracy for every trained model.

    Returns a nested dict: { model_name: { "AUC": ..., "Accuracy": ... } }
    """
    results: dict[str, dict[str, float]] = {}

    print("\n── Evaluation ─────────────────────────────────────────────────")
    for name, model in models.items():
        y_pred = model.predict(X_test)
        y_prob = model.predict_proba(X_test)[:, 1]

        auc = roc_auc_score(y_test, y_prob)
        acc = accuracy_score(y_test, y_pred)

        results[name] = {"AUC": auc, "Accuracy": acc}
        print(f"  {name:<22}  AUC = {auc:.4f}   Accuracy = {acc:.4f}")

    return results


# ── 5. Differential expression ────────────────────────────────────────────────

def differential_expression(
    X_norm: pd.DataFrame,
    y: pd.Series,
) -> pd.DataFrame:
    """
    Compute mean normalised expression per stage and the (late − early) shift.

    Parameters
    ----------
    X_norm : normalised expression DataFrame
    y      : binary labels (0 = early, 1 = late)

    Returns
    -------
    de_df : DataFrame with columns [mean_early, mean_late, shift]
            sorted by shift descending (most upregulated in late stage first)
    """
    early_mask = y == 0
    late_mask = y == 1

    mean_early = X_norm[early_mask.values].mean(axis=0)
    mean_late = X_norm[late_mask.values].mean(axis=0)
    shift = mean_late - mean_early

    de_df = pd.DataFrame({
        "mean_early": mean_early,
        "mean_late": mean_late,
        "shift": shift,
    }).sort_values("shift", ascending=False)

    return de_df


# ── 6. Report ─────────────────────────────────────────────────────────────────

def print_report(
    results: dict[str, dict[str, float]],
    de_df: pd.DataFrame,
    top_n: int = TOP_N_GENES,
) -> None:
    """Print the final summary: AUC/accuracy + top up/downregulated genes."""
    print("\n── Model Results ──────────────────────────────────────────────")
    best_name = max(results, key=lambda n: results[n]["AUC"])
    best = results[best_name]
    print(f"  Best model  : {best_name}")
    print(f"  AUC         : {best['AUC']:.4f}")
    print(f"  Accuracy    : {best['Accuracy']:.4f}")

    print("\n── Differential Expression (late − early) ──────────────────────")
    print(f"\n  Top {top_n} UPREGULATED in late-stage PDAC:")
    print(de_df.head(top_n).to_string(
        float_format=lambda v: f"{v:+.4f}",
        header=True,
    ))

    print(f"\n  Top {top_n} DOWNREGULATED in late-stage PDAC:")
    print(de_df.tail(top_n).sort_values("shift").to_string(
        float_format=lambda v: f"{v:+.4f}",
        header=True,
    ))

    print("\n── Full gene ranking by expression shift ───────────────────────")
    print(de_df.to_string(float_format=lambda v: f"{v:+.4f}"))
    print()


# ── Main pipeline ─────────────────────────────────────────────────────────────

def run_pipeline(
    X: pd.DataFrame,
    y: pd.Series,
) -> dict[str, dict[str, float]]:
    """
    End-to-end pipeline: preprocess → split → train → evaluate → differential
    expression → report.

    Parameters
    ----------
    X : raw gene expression DataFrame  (patients × genes)
    y : binary stage labels            (0 = early, 1 = late)

    Returns
    -------
    results : evaluation metrics for each model
    """
    print("=" * 60)
    print("  PancrionDX — Transcriptomic PDAC Stage Classifier")
    print("=" * 60 + "\n")

    # ── Preprocess ────────────────────────────────────────────────
    print("── Preprocessing ──────────────────────────────────────────────")
    X_norm = preprocess(X)
    print(f"✓ log2(x+1) transform applied")
    print(f"✓ z-score normalisation applied  (shape: {X_norm.shape})\n")

    # ── Train / test split ────────────────────────────────────────
    X_train, X_test, y_train, y_test = train_test_split(
        X_norm.values, y.values,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=y.values,
    )
    print(f"── Train/Test Split ───────────────────────────────────────────")
    print(f"  Train: {X_train.shape[0]} samples   Test: {X_test.shape[0]} samples\n")

    # ── Train ─────────────────────────────────────────────────────
    print("── Training ───────────────────────────────────────────────────")
    models = train_models(X_train, y_train)

    # ── Evaluate ──────────────────────────────────────────────────
    results = evaluate_models(models, X_test, y_test)

    # ── Differential expression ───────────────────────────────────
    de_df = differential_expression(X_norm, y)

    # ── Report ────────────────────────────────────────────────────
    print_report(results, de_df)

    return results


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Generate synthetic PDAC expression data and run the full pipeline
    X, y = make_synthetic_expression_data(n_patients=200)
    run_pipeline(X, y)
