"""Train and validate a PDAC RandomForest classifier with interpretability outputs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score


DEFAULT_DATA_PATH = Path("mutation_matrix.csv")
DEFAULT_PLOT_PATH = Path("feature_importance.png")
DEFAULT_GENE_PANEL_PATH = Path("src/data/gene_panel.json")


def load_gene_panel_genes(gene_panel_path: Path) -> list[str]:
    """Load ordered gene symbols from the configured gene panel JSON."""
    panel = json.loads(gene_panel_path.read_text())
    genes = [g["gene_symbol"] for g in panel.get("genes", [])]
    if not genes:
        raise ValueError(f"No genes found in panel file: {gene_panel_path}")
    return genes


def load_data(data_path: Path, gene_panel_path: Path = DEFAULT_GENE_PANEL_PATH) -> tuple[pd.DataFrame, pd.Series]:
    """Load labels and keep only panel genes as model features."""
    df = pd.read_csv(data_path)

    if "label" not in df.columns:
        raise ValueError("CSV must contain a 'label' column")

    panel_genes = load_gene_panel_genes(gene_panel_path)
    available_panel_genes = [g for g in panel_genes if g in df.columns]

    if not available_panel_genes:
        raise ValueError("No gene-panel columns found in dataset")

    y = df["label"].astype(int)
    X = df[available_panel_genes].copy()

    dropped_non_panel = [c for c in df.columns if c not in {"label", *available_panel_genes}]
    if dropped_non_panel:
        print(f"Dropped non-panel features: {len(dropped_non_panel)}")

    if X.empty:
        raise ValueError("Feature matrix is empty")
    if y.nunique() != 2:
        raise ValueError("Binary labels are required for ROC-AUC")

    return X, y


def build_model(random_state: int) -> RandomForestClassifier:
    """Create an untrained RandomForest classifier."""
    return RandomForestClassifier(
        n_estimators=200,
        random_state=random_state,
        class_weight="balanced",
    )


def print_data_summary(X: pd.DataFrame, y: pd.Series) -> None:
    """Print dataset size and binary class distribution."""
    class_counts = y.value_counts().sort_index()
    count_0 = int(class_counts.get(0, 0))
    count_1 = int(class_counts.get(1, 0))

    print(f"Dataset shape         : {X.shape[0]} samples × {X.shape[1]} features")
    print(f"Class distribution    : 0 = {count_0}, 1 = {count_1}")


def run_cross_validation(model: RandomForestClassifier, X: pd.DataFrame, y: pd.Series) -> np.ndarray:
    """Run 5-fold ROC-AUC cross-validation and print fold statistics."""
    cv_scores = cross_val_score(model, X, y, cv=5, scoring="roc_auc")

    print("\nCross-validation (5-fold ROC-AUC):")
    print("Fold AUC scores       :", [f"{score:.4f}" for score in cv_scores])
    print(f"Mean AUC              : {cv_scores.mean():.4f}")
    print(f"Standard deviation    : {cv_scores.std():.4f}")

    return cv_scores


def compute_feature_importance(
    model: RandomForestClassifier,
    X: pd.DataFrame,
) -> pd.DataFrame:
    """Return sorted feature importances paired with gene names."""
    importance_df = pd.DataFrame(
        {
            "gene": X.columns,
            "importance": model.feature_importances_,
        }
    ).sort_values("importance", ascending=False)

    print("\nFeature importance ranking:")
    for _, row in importance_df.iterrows():
        print(f"{row['gene']}: {row['importance']:.4f}")

    return importance_df


def plot_feature_importance(
    importance_df: pd.DataFrame,
    plot_path: Path,
    top_n: int | None = None,
) -> None:
    """Plot feature importances as a simple bar chart."""
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("\nPlot skipped: matplotlib is not installed.")
        return

    plot_df = importance_df.copy()
    if top_n is not None and top_n > 0:
        plot_df = plot_df.head(top_n)

    plt.figure(figsize=(10, 5))
    plt.bar(plot_df["gene"], plot_df["importance"])
    plt.xlabel("Gene")
    plt.ylabel("Feature Importance")
    plt.title("RandomForest Feature Importance")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(plot_path, dpi=150)
    plt.close()

    print(f"Feature importance plot saved to: {plot_path}")


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA_PATH, help="Path to CSV with a 'label' column")
    parser.add_argument("--random-state", type=int, default=42, help="Random seed for reproducibility")
    parser.add_argument("--plot", type=Path, default=DEFAULT_PLOT_PATH, help="Path to save feature-importance plot")
    parser.add_argument(
        "--top-n",
        type=int,
        default=None,
        help="Optional: plot only the top N most important genes",
    )
    return parser.parse_args()


def main() -> None:
    """Run validation and train final interpretable model."""
    args = parse_args()

    X, y = load_data(args.data)
    print_data_summary(X, y)

    model = build_model(args.random_state)
    run_cross_validation(model, X, y)

    # Train final model on full dataset after cross-validation.
    model.fit(X, y)
    print("\nFinal model trained on full dataset.")

    importance_df = compute_feature_importance(model, X)
    plot_feature_importance(importance_df, args.plot, top_n=args.top_n)


if __name__ == "__main__":
    main()
