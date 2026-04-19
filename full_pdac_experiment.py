"""Run a full PDAC experiment pipeline with ML, permutation testing, and rule-engine comparison."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, roc_auc_score, roc_curve
from sklearn.model_selection import train_test_split

from src.models.variant import Variant
from src.scoring.risk_engine import calculate_risk
from permutation_test import run_permutation_test


DEFAULT_DATA_PATH = Path("mutation_matrix.csv")
DEFAULT_ROC_PATH = Path("pdac_roc_comparison.png")
DEFAULT_PERM_PATH = Path("pdac_permutation_histogram.png")
DEFAULT_GENE_PANEL_PATH = Path("src/data/gene_panel.json")


# -----------------------------------------------------------------------------
# 1) DATASET LOADING / GENERATION
# -----------------------------------------------------------------------------
def generate_synthetic_dataset(n_samples: int = 170, random_state: int = 42) -> pd.DataFrame:
    """Generate a synthetic mutation dataset if no CSV is provided."""
    rng = np.random.default_rng(random_state)
    _panel = json.loads((Path(__file__).parent / "src" / "data" / "gene_panel.json").read_text())
    genes = [g["gene_symbol"] for g in _panel["genes"]]

    X = rng.binomial(n=2, p=0.30, size=(n_samples, len(genes)))
    mutation_burden = X.sum(axis=1)
    p_late = 1 / (1 + np.exp(-(mutation_burden - 5) / 2))
    y = (rng.random(n_samples) < p_late).astype(int)

    df = pd.DataFrame(X, columns=genes)
    df.insert(0, "label", y)
    return df


def load_or_generate_dataset(data_path: Path, random_state: int) -> pd.DataFrame:
    """Load dataset from CSV or generate a synthetic dataset."""
    if data_path.exists():
        print(f"[1/6] Loading dataset from: {data_path}")
        df = pd.read_csv(data_path)
    else:
        print(f"[1/6] Dataset not found at {data_path}. Generating synthetic dataset...")
        df = generate_synthetic_dataset(random_state=random_state)

    if "label" not in df.columns:
        raise ValueError("Dataset must contain a 'label' column")

    return df


def load_gene_panel_genes(gene_panel_path: Path = DEFAULT_GENE_PANEL_PATH) -> list[str]:
    """Load ordered gene symbols from the configured gene panel JSON."""
    panel = json.loads(gene_panel_path.read_text())
    genes = [g["gene_symbol"] for g in panel.get("genes", [])]
    if not genes:
        raise ValueError(f"No genes found in panel file: {gene_panel_path}")
    return genes


# -----------------------------------------------------------------------------
# 2) FEATURE MATRIX
# -----------------------------------------------------------------------------
def build_feature_matrix(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series, list[str]]:
    """Build X/y from mutation dataframe using only gene-panel features."""
    panel_genes = load_gene_panel_genes()
    feature_columns = [gene for gene in panel_genes if gene in df.columns]
    dropped_non_panel = [col for col in df.columns if col not in {"label", *feature_columns}]

    if dropped_non_panel:
        print(f"Filtered out non-panel features: {len(dropped_non_panel)}")

    X = df[feature_columns].copy()
    y = df["label"].astype(int).copy()

    if X.empty:
        raise ValueError("Feature matrix is empty")
    if y.nunique() != 2:
        raise ValueError("Binary labels required for ROC-AUC and permutation testing")

    return X, y, feature_columns


# -----------------------------------------------------------------------------
# 3) TRAIN ML MODEL
# -----------------------------------------------------------------------------
def train_random_forest(X_train: pd.DataFrame, y_train: pd.Series, random_state: int) -> RandomForestClassifier:
    """Train RandomForest classifier."""
    model = RandomForestClassifier(
        n_estimators=300,
        random_state=random_state,
        class_weight="balanced",
    )
    model.fit(X_train, y_train)
    return model


# -----------------------------------------------------------------------------
# 4) EVALUATE ML MODEL
# -----------------------------------------------------------------------------
def evaluate_predictions(y_true: np.ndarray, y_pred: np.ndarray, y_score: np.ndarray) -> dict[str, float]:
    """Compute common classification metrics."""
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_true, y_score)),
    }


def print_metrics_block(title: str, metrics: dict[str, float]) -> None:
    """Print readable metrics block."""
    print(f"\n{title}")
    print("-" * len(title))
    print(f"Accuracy : {metrics['accuracy']:.4f}")
    print(f"Precision: {metrics['precision']:.4f}")
    print(f"Recall   : {metrics['recall']:.4f}")
    print(f"ROC-AUC  : {metrics['roc_auc']:.4f}")


# -----------------------------------------------------------------------------
# 5) PERMUTATION TEST — delegated to permutation_test.py
# -----------------------------------------------------------------------------
# run_permutation_test(model, X, y, n_permutations, ...) is imported above.
# Signature: run_permutation_test(model, X, y, n_permutations=100,
#            test_size=0.2, random_state=42, plot_path=None) -> dict


# -----------------------------------------------------------------------------
# 6) RULE-BASED ENGINE + COMPARISON
# -----------------------------------------------------------------------------
def sample_to_variants(sample_row: pd.Series, patient_id: str) -> list[Variant]:
    """Convert one feature row into Variant objects for the rule engine."""
    variants: list[Variant] = []

    for gene, value in sample_row.items():
        count = int(value)
        if count <= 0:
            continue
        for c in range(count):
            variants.append(
                Variant(
                    gene=gene,
                    variant_id=f"{patient_id}:{gene}:{c+1}",
                    consequence="missense",
                    clinvar_classification="Pathogenic",
                    predicted_impact="missense",
                )
            )

    return variants


def run_rule_engine(X_test: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    """Run rule-based engine per test sample and return labels and scores."""
    rule_scores: list[float] = []
    rule_preds: list[int] = []

    for idx, (_, row) in enumerate(X_test.iterrows(), start=1):
        variants = sample_to_variants(row, patient_id=f"test_{idx}")
        result = calculate_risk(variants)

        score = float(result["score"])
        pred = 1 if result["classification"] == "Late-stage likely" else 0

        rule_scores.append(score)
        rule_preds.append(pred)

    return np.array(rule_preds), np.array(rule_scores)


def plot_roc_curves(
    y_true: np.ndarray,
    ml_scores: np.ndarray,
    rule_scores: np.ndarray,
    ml_auc: float,
    rule_auc: float,
    output_path: Path,
) -> None:
    """Plot ROC curves for ML model and rule-based engine."""
    fpr_ml, tpr_ml, _ = roc_curve(y_true, ml_scores)
    fpr_rule, tpr_rule, _ = roc_curve(y_true, rule_scores)

    plt.figure(figsize=(8, 6))
    plt.plot(fpr_ml, tpr_ml, linewidth=2, label=f"RandomForest (AUC={ml_auc:.3f})")
    plt.plot(fpr_rule, tpr_rule, linewidth=2, label=f"Rule Engine (AUC={rule_auc:.3f})")
    plt.plot([0, 1], [0, 1], "k--", label="Chance")
    plt.title("PDAC ROC Curve Comparison")
    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    plt.legend(loc="lower right")
    plt.tight_layout()
    plt.savefig(output_path, dpi=160)
    plt.close()


def print_comparison_summary(ml_metrics: dict[str, float], rule_metrics: dict[str, float], perm_mean_auc: float, perm_p: float) -> None:
    """Print compact ML vs rule-engine summary."""
    print("\nComparison Summary")
    print("------------------")
    print(f"RandomForest ROC-AUC : {ml_metrics['roc_auc']:.4f}")
    print(f"Rule Engine ROC-AUC  : {rule_metrics['roc_auc']:.4f}")
    print(f"AUC Improvement      : {ml_metrics['roc_auc'] - rule_metrics['roc_auc']:+.4f}")
    print(f"Mean Shuffled AUC    : {perm_mean_auc:.4f}")
    print(f"Permutation p-value  : {perm_p:.4f}")


# -----------------------------------------------------------------------------
# MAIN
# -----------------------------------------------------------------------------
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA_PATH, help="CSV path with label column")
    parser.add_argument("--test-size", type=float, default=0.2, help="Test split fraction")
    parser.add_argument("--n-permutations", type=int, default=100, help="Permutation iterations")
    parser.add_argument("--random-state", type=int, default=42, help="Random seed")
    parser.add_argument("--roc-out", type=Path, default=DEFAULT_ROC_PATH, help="ROC curve output image")
    parser.add_argument("--perm-out", type=Path, default=DEFAULT_PERM_PATH, help="Permutation histogram output image")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.n_permutations <= 0:
        raise ValueError("--n-permutations must be > 0")

    df = load_or_generate_dataset(args.data, random_state=args.random_state)
    X, y, _ = build_feature_matrix(df)

    print(f"[2/6] Feature matrix built: {X.shape[0]} samples × {X.shape[1]} features")

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=args.test_size,
        random_state=args.random_state,
        stratify=y,
    )

    print("[3/6] Training RandomForest model...")
    ml_model = train_random_forest(X_train, y_train, random_state=args.random_state)

    print("[4/6] Evaluating ML model...")
    ml_pred = ml_model.predict(X_test)
    ml_scores = ml_model.predict_proba(X_test)[:, 1]
    ml_metrics = evaluate_predictions(y_test.to_numpy(), ml_pred, ml_scores)
    print_metrics_block("RandomForest Metrics", ml_metrics)

    print("[5/6] Running permutation test...")
    perm_results = run_permutation_test(
        ml_model,
        X,
        y,
        n_permutations=args.n_permutations,
        test_size=args.test_size,
        random_state=args.random_state,
        plot_path=args.perm_out,
    )
    perm_mean_auc = perm_results["mean_perm"]
    real_auc      = perm_results["real_auc"]
    perm_p        = perm_results["p_value"]

    print("[6/6] Comparing with rule-based engine...")
    rule_pred, rule_scores = run_rule_engine(X_test)
    rule_metrics = evaluate_predictions(y_test.to_numpy(), rule_pred, rule_scores)
    print_metrics_block("Rule-Engine Metrics", rule_metrics)

    plot_roc_curves(
        y_true=y_test.to_numpy(),
        ml_scores=ml_scores,
        rule_scores=rule_scores,
        ml_auc=ml_metrics["roc_auc"],
        rule_auc=rule_metrics["roc_auc"],
        output_path=args.roc_out,
    )

    print_comparison_summary(ml_metrics, rule_metrics, perm_mean_auc, perm_p)

    print("\nSaved outputs")
    print("-------------")
    print(f"ROC curve plot         : {args.roc_out}")
    print(f"Permutation histogram  : {args.perm_out}")


if __name__ == "__main__":
    main()
