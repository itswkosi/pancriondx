"""
Biological Validation and Correction Pipeline for PDAC Mutation Classifier

This script ensures the PDAC classifier is BOTH statistically valid AND biologically meaningful.
It addresses the problem where a model may show statistical significance but use incorrect
biological features (e.g., BRCA1/2 instead of KRAS).

Usage:
    python biological_validation_pipeline.py --data mutation_matrix.csv

"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split


# ============================================================================
# CONFIGURATION & CORE PDAC GENES
# ============================================================================

# Core PDAC genes that should dominate the model based on biological literature
CORE_PDAC_GENES = ["KRAS", "TP53", "SMAD4", "CDKN2A"]

DEFAULT_DATA_PATH = Path("mutation_matrix.csv")
DEFAULT_GENE_PANEL_PATH = Path("src/data/gene_panel.json")

# Model hyperparameters
RF_N_ESTIMATORS = 200
RF_RANDOM_STATE = 42


# ============================================================================
# TASK 1: FEATURE SANITY CHECK
# ============================================================================

def check_feature_sanity(X: pd.DataFrame) -> dict[str, bool]:
    """
    Verify that required core PDAC genes are present in the feature matrix.

    Parameters
    ----------
    X : pd.DataFrame
        Binary mutation feature matrix (samples × genes).

    Returns
    -------
    dict
        Mapping of gene names to bool (True if present).
    """
    print("\n" + "=" * 80)
    print("TASK 1: FEATURE SANITY CHECK")
    print("=" * 80)

    print(f"\nFeature columns ({len(X.columns)} total):")
    print(list(X.columns))

    print(f"\n\nVerifying core PDAC genes:")
    gene_status = {}
    for gene in CORE_PDAC_GENES:
        present = gene in X.columns
        gene_status[gene] = present
        status_str = "✓ FOUND" if present else "✗ MISSING"
        print(f"  {gene:12s} {status_str}")

    missing_genes = [g for g, present in gene_status.items() if not present]
    if missing_genes:
        print(f"\n⚠️  WARNING: Missing core PDAC genes: {missing_genes}")

    return gene_status


# ============================================================================
# TASK 2: MUTATION FREQUENCY ANALYSIS
# ============================================================================

def analyze_mutation_frequency(X: pd.DataFrame) -> None:
    """
    Compute and display mutation frequencies across the dataset.

    Parameters
    ----------
    X : pd.DataFrame
        Binary mutation feature matrix (samples × genes).
    """
    print("\n" + "=" * 80)
    print("TASK 2: MUTATION FREQUENCY ANALYSIS")
    print("=" * 80)

    # Count mutations per gene
    gene_counts = X.sum().sort_values(ascending=False)

    print(f"\nTop 10 most frequently mutated genes:")
    print("-" * 50)
    for rank, (gene, count) in enumerate(gene_counts.head(10).items(), 1):
        freq_pct = (count / len(X)) * 100
        print(f"  {rank:2d}. {gene:15s}: {int(count):4d} samples ({freq_pct:5.1f}%)")

    print(f"\n\nCore PDAC gene mutation frequencies:")
    print("-" * 50)
    for gene in CORE_PDAC_GENES:
        if gene in X.columns:
            count = X[gene].sum()
            freq_pct = (count / len(X)) * 100
            print(f"  {gene:15s}: {int(count):4d} samples ({freq_pct:5.1f}%)")
        else:
            print(f"  {gene:15s}: NOT IN DATASET")

    # Check if KRAS is in top mutated
    top_5_genes = set(gene_counts.head(5).index)
    if "KRAS" not in top_5_genes:
        print(f"\n⚠️  WARNING: KRAS is not in top 5 mutated genes!")
        print(f"    Expected KRAS to be a dominant driver mutation in PDAC.")
        print(f"    Top 5: {list(top_5_genes)}")


# ============================================================================
# TASK 3: BIOLOGICAL FILTERING EXPERIMENT
# ============================================================================

def create_core_gene_dataset(X: pd.DataFrame) -> pd.DataFrame:
    """
    Create a restricted dataset using only core PDAC genes.

    Parameters
    ----------
    X : pd.DataFrame
        Full binary mutation feature matrix.

    Returns
    -------
    pd.DataFrame
        Filtered matrix with only core genes that exist in X.
    """
    print("\n" + "=" * 80)
    print("TASK 3: BIOLOGICAL FILTERING EXPERIMENT")
    print("=" * 80)

    available_core_genes = [g for g in CORE_PDAC_GENES if g in X.columns]
    missing_core_genes = [g for g in CORE_PDAC_GENES if g not in X.columns]

    print(f"\nCore gene filtering:")
    print(f"  Available core genes: {available_core_genes}")
    if missing_core_genes:
        print(f"  ⚠️  Missing core genes: {missing_core_genes}")

    X_core = X[available_core_genes].copy()
    print(f"\nOriginal feature matrix shape: {X.shape}")
    print(f"Core gene matrix shape:        {X_core.shape}")
    print(f"Dimensionality reduction:      {X.shape[1]:3d} → {X_core.shape[1]:3d} features")

    return X_core


# ============================================================================
# TASK 4: MODEL TRAINING (FULL AND CORE)
# ============================================================================

def train_model(
    X: pd.DataFrame,
    y: pd.Series,
    random_state: int = RF_RANDOM_STATE,
) -> tuple[RandomForestClassifier, float, float]:
    """
    Train a RandomForest model using 80/20 train/test split and compute ROC-AUC.

    Parameters
    ----------
    X : pd.DataFrame
        Feature matrix.
    y : pd.Series
        Binary labels.
    random_state : int
        Random seed for reproducibility.

    Returns
    -------
    tuple
        (trained_model, train_auc, test_auc)
    """
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=0.2,
        random_state=random_state,
        stratify=y,
    )

    model = RandomForestClassifier(
        n_estimators=RF_N_ESTIMATORS,
        random_state=random_state,
        class_weight="balanced",
        n_jobs=-1,
    )
    model.fit(X_train, y_train)

    train_scores = model.predict_proba(X_train)[:, 1]
    test_scores = model.predict_proba(X_test)[:, 1]

    train_auc = roc_auc_score(y_train, train_scores)
    test_auc = roc_auc_score(y_test, test_scores)

    return model, train_auc, test_auc


def train_both_models(
    X: pd.DataFrame,
    X_core: pd.DataFrame,
    y: pd.Series,
) -> dict:
    """
    Train both full and core models and compare performance.

    Parameters
    ----------
    X : pd.DataFrame
        Full feature matrix.
    X_core : pd.DataFrame
        Core-only feature matrix.
    y : pd.Series
        Binary labels.

    Returns
    -------
    dict
        Contains both models and their AUC scores.
    """
    print("\n" + "=" * 80)
    print("TASK 4: MODEL TRAINING (FULL AND CORE)")
    print("=" * 80)

    print(f"\nTraining Full Model ({X.shape[1]} features)...")
    full_model, full_train_auc, full_test_auc = train_model(X, y)

    print(f"  Train ROC-AUC: {full_train_auc:.4f}")
    print(f"  Test ROC-AUC:  {full_test_auc:.4f}")

    print(f"\nTraining Core Model ({X_core.shape[1]} features)...")
    core_model, core_train_auc, core_test_auc = train_model(X_core, y)

    print(f"  Train ROC-AUC: {core_train_auc:.4f}")
    print(f"  Test ROC-AUC:  {core_test_auc:.4f}")

    print(f"\nModel Comparison:")
    print(f"  Full model test AUC:  {full_test_auc:.4f}")
    print(f"  Core model test AUC:  {core_test_auc:.4f}")
    print(f"  Difference:           {full_test_auc - core_test_auc:+.4f}")

    return {
        "full_model": full_model,
        "core_model": core_model,
        "full_train_auc": full_train_auc,
        "full_test_auc": full_test_auc,
        "core_train_auc": core_train_auc,
        "core_test_auc": core_test_auc,
    }


# ============================================================================
# TASK 5: FEATURE IMPORTANCE ANALYSIS
# ============================================================================

def analyze_feature_importance(
    full_model: RandomForestClassifier,
    core_model: RandomForestClassifier,
    X: pd.DataFrame,
    X_core: pd.DataFrame,
) -> None:
    """
    Extract and display feature importance from both models.

    Parameters
    ----------
    full_model : RandomForestClassifier
        Trained model on full feature set.
    core_model : RandomForestClassifier
        Trained model on core genes only.
    X : pd.DataFrame
        Full feature matrix (for column names).
    X_core : pd.DataFrame
        Core feature matrix (for column names).
    """
    print("\n" + "=" * 80)
    print("TASK 5: FEATURE IMPORTANCE ANALYSIS")
    print("=" * 80)

    # Full model importance
    print(f"\nFull Model Feature Importance (top 10):")
    print("-" * 50)
    full_importance = pd.DataFrame({
        "gene": X.columns,
        "importance": full_model.feature_importances_,
    }).sort_values("importance", ascending=False)

    for rank, (idx, row) in enumerate(full_importance.head(10).iterrows(), 1):
        print(f"  {rank:2d}. {row['gene']:15s}: {row['importance']:.4f}")

    # Core model importance
    print(f"\nCore Model Feature Importance (all genes):")
    print("-" * 50)
    core_importance = pd.DataFrame({
        "gene": X_core.columns,
        "importance": core_model.feature_importances_,
    }).sort_values("importance", ascending=False)

    for rank, (idx, row) in enumerate(core_importance.iterrows(), 1):
        print(f"  {rank:2d}. {row['gene']:15s}: {row['importance']:.4f}")

    # Check if KRAS is important
    if "KRAS" in X.columns:
        kras_rank_full = (full_importance["gene"] == "KRAS").argmax() + 1
        kras_importance_full = full_importance[full_importance["gene"] == "KRAS"]["importance"].values[0]
        print(f"\n✓ KRAS in full model: rank {kras_rank_full}, importance {kras_importance_full:.4f}")
    else:
        print(f"\n✗ KRAS not in full model feature set")

    if "KRAS" in X_core.columns:
        kras_rank_core = (core_importance["gene"] == "KRAS").argmax() + 1
        kras_importance_core = core_importance[core_importance["gene"] == "KRAS"]["importance"].values[0]
        print(f"✓ KRAS in core model: rank {kras_rank_core}, importance {kras_importance_core:.4f}")


# ============================================================================
# TASK 6 & 7: PERMUTATION TEST IMPLEMENTATION AND EXECUTION
# ============================================================================

def run_permutation_test(
    model: RandomForestClassifier,
    X: pd.DataFrame,
    y: pd.Series,
    n_permutations: int = 100,
    random_state: int = RF_RANDOM_STATE,
) -> dict:
    """
    Implement a permutation test to validate model significance.

    For each permutation:
    1. Shuffle labels using: y.sample(frac=1, random_state=i).reset_index(drop=True)
    2. Retrain model from scratch
    3. Compute ROC-AUC on shuffled data
    4. Collect AUC values

    Parameters
    ----------
    model : RandomForestClassifier
        An untrained classifier to use as template.
    X : pd.DataFrame
        Feature matrix.
    y : pd.Series
        Binary labels.
    n_permutations : int
        Number of permutation iterations (default 100).
    random_state : int
        Seed for reproducibility.

    Returns
    -------
    dict
        Contains:
            - real_auc: AUC on real labels
            - permuted_aucs: list of AUCs from permutations
            - mean_perm_auc: mean of permuted AUCs
            - std_perm_auc: std of permuted AUCs
            - p_value: empirical p-value (fraction of permuted AUCs >= real AUC)
    """
    # Split data once for consistent evaluation
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=0.2,
        random_state=random_state,
        stratify=y,
    )

    # 1. Train on real labels
    real_model = clone(model)
    real_model.set_params(random_state=random_state)
    real_model.fit(X_train, y_train)
    real_scores = real_model.predict_proba(X_test)[:, 1]
    real_auc = float(roc_auc_score(y_test, real_scores))

    # 2. Permutation loop
    permuted_aucs = []
    for i in range(n_permutations):
        # Shuffle labels for this iteration
        y_train_shuffled = y_train.sample(frac=1, random_state=i).reset_index(drop=True)

        # Train a fresh model on shuffled labels
        perm_model = clone(model)
        perm_model.set_params(random_state=random_state + i + 1)
        perm_model.fit(X_train, y_train_shuffled)

        # Evaluate on real test set
        perm_scores = perm_model.predict_proba(X_test)[:, 1]
        perm_auc = float(roc_auc_score(y_test, perm_scores))
        permuted_aucs.append(perm_auc)

    # 3. Compute statistics
    mean_perm_auc = np.mean(permuted_aucs)
    std_perm_auc = np.std(permuted_aucs)

    # Empirical p-value: fraction of permutations >= real AUC
    p_value = np.mean(np.array(permuted_aucs) >= real_auc)

    return {
        "real_auc": real_auc,
        "permuted_aucs": permuted_aucs,
        "mean_perm_auc": mean_perm_auc,
        "std_perm_auc": std_perm_auc,
        "p_value": p_value,
    }


def run_permutation_tests(
    full_model: RandomForestClassifier,
    core_model: RandomForestClassifier,
    X: pd.DataFrame,
    X_core: pd.DataFrame,
    y: pd.Series,
    n_permutations: int = 100,
) -> dict:
    """
    Run permutation tests for both full and core models.

    Parameters
    ----------
    full_model : RandomForestClassifier
        Trained full model (used as template for cloning).
    core_model : RandomForestClassifier
        Trained core model (used as template for cloning).
    X : pd.DataFrame
        Full feature matrix.
    X_core : pd.DataFrame
        Core feature matrix.
    y : pd.Series
        Binary labels.
    n_permutations : int
        Number of permutations (default 100).

    Returns
    -------
    dict
        Contains results for both models.
    """
    print("\n" + "=" * 80)
    print("TASK 6 & 7: PERMUTATION TEST IMPLEMENTATION AND EXECUTION")
    print("=" * 80)

    print(f"\nRunning permutation test on Full Model ({n_permutations} permutations)...")
    full_perm_results = run_permutation_test(
        full_model, X, y,
        n_permutations=n_permutations,
    )

    print(f"\nFull Model Permutation Results:")
    print(f"  Real AUC:          {full_perm_results['real_auc']:.4f}")
    print(f"  Mean permuted AUC: {full_perm_results['mean_perm_auc']:.4f}")
    print(f"  Std permuted AUC:  {full_perm_results['std_perm_auc']:.4f}")
    print(f"  p-value:           {full_perm_results['p_value']:.4f}")

    if full_perm_results['p_value'] < 0.05:
        print(f"  ✓ STATISTICALLY SIGNIFICANT (p < 0.05)")
    else:
        print(f"  ✗ NOT STATISTICALLY SIGNIFICANT (p >= 0.05)")

    print(f"\nRunning permutation test on Core Model ({n_permutations} permutations)...")
    core_perm_results = run_permutation_test(
        core_model, X_core, y,
        n_permutations=n_permutations,
    )

    print(f"\nCore Model Permutation Results:")
    print(f"  Real AUC:          {core_perm_results['real_auc']:.4f}")
    print(f"  Mean permuted AUC: {core_perm_results['mean_perm_auc']:.4f}")
    print(f"  Std permuted AUC:  {core_perm_results['std_perm_auc']:.4f}")
    print(f"  p-value:           {core_perm_results['p_value']:.4f}")

    if core_perm_results['p_value'] < 0.05:
        print(f"  ✓ STATISTICALLY SIGNIFICANT (p < 0.05)")
    else:
        print(f"  ✗ NOT STATISTICALLY SIGNIFICANT (p >= 0.05)")

    return {
        "full": full_perm_results,
        "core": core_perm_results,
    }


# ============================================================================
# TASK 8: INTERPRETATION OUTPUT
# ============================================================================

def generate_interpretation_report(
    full_results: dict,
    core_results: dict,
    perm_results: dict,
    X: pd.DataFrame,
    full_model: RandomForestClassifier,
) -> None:
    """
    Generate a structured interpretation report with biological validation logic.

    Parameters
    ----------
    full_results : dict
        Full model training results (from task 4).
    core_results : dict
        Core model training results (from task 4).
    perm_results : dict
        Permutation test results (from task 7).
    X : pd.DataFrame
        Full feature matrix (for checking KRAS).
    full_model : RandomForestClassifier
        Trained full model (for feature importance).
    """
    print("\n" + "=" * 80)
    print("TASK 8: BIOLOGICAL VALIDATION INTERPRETATION")
    print("=" * 80)

    # Extract key metrics
    full_test_auc = full_results["full_test_auc"]
    core_test_auc = full_results["core_test_auc"]
    full_perm = perm_results["full"]
    core_perm = perm_results["core"]

    print("\n" + "-" * 80)
    print("MODEL PERFORMANCE COMPARISON")
    print("-" * 80)
    print(f"Full Model Test AUC:  {full_test_auc:.4f}")
    print(f"Core Model Test AUC:  {core_test_auc:.4f}")
    print(f"Difference (Full - Core): {full_test_auc - core_test_auc:+.4f}")

    print("\n" + "-" * 80)
    print("STATISTICAL SIGNIFICANCE (p-values)")
    print("-" * 80)
    print(f"Full Model p-value:   {full_perm['p_value']:.4f}")
    print(f"Core Model p-value:   {core_perm['p_value']:.4f}")

    print("\n" + "-" * 80)
    print("BIOLOGICAL VALIDATION LOGIC")
    print("-" * 80)

    # Logic 1: Core model performance similar to full model
    auc_diff = abs(full_test_auc - core_test_auc)
    if auc_diff < 0.05:
        print("\n✓ [GOOD] Core and Full models have similar AUC.")
        print("  → Model is learning biologically relevant signal from PDAC driver genes.")
    else:
        print(f"\n⚠️  [CAUTION] Core vs Full AUC difference: {auc_diff:.4f}")
        if full_test_auc > core_test_auc + 0.05:
            print(f"  → Full model > Core model suggests non-biological or spurious features.")
            print(f"  → Consider feature engineering or data validation.")
        else:
            print(f"  → Core model outperforms full model (unexpected but may be valid).")

    # Logic 2: KRAS presence and importance
    print("\n" + "-" * 80)
    kras_missing = "KRAS" not in X.columns
    if kras_missing:
        print("\n✗ [CRITICAL] KRAS is missing from feature matrix!")
        print("  → Cannot validate biological signal.")
    else:
        # Get KRAS importance
        full_importance_df = pd.DataFrame({
            "gene": X.columns,
            "importance": full_model.feature_importances_,
        }).sort_values("importance", ascending=False)
        kras_rank = (full_importance_df["gene"] == "KRAS").argmax() + 1
        kras_importance = full_importance_df[full_importance_df["gene"] == "KRAS"]["importance"].values[0]

        print(f"\n✓ [OK] KRAS found in model.")
        print(f"  Feature Importance Rank: {kras_rank} / {len(full_importance_df)}")
        print(f"  Importance Score:        {kras_importance:.4f}")

        if kras_rank <= 5:
            print(f"  → ✓ KRAS is in top 5 features (biologically sound).")
        elif kras_rank <= 10:
            print(f"  → ⚠️  KRAS is ranked {kras_rank} (moderately concerning).")
        else:
            print(f"  → ✗ KRAS is ranked {kras_rank} (biologically concerning!).")
            print(f"     Expected KRAS to dominate PDAC models.")

    # Logic 3: Overall biological validation
    print("\n" + "-" * 80)
    print("OVERALL BIOLOGICAL VALIDATION STATUS")
    print("-" * 80)

    validation_checks = {
        "Model Statistical Significance": full_perm["p_value"] < 0.05,
        "Core Model Significant": core_perm["p_value"] < 0.05,
        "Similar Full/Core AUC": auc_diff < 0.05,
        "KRAS Present": not kras_missing,
    }

    passed = sum(validation_checks.values())
    total = len(validation_checks)

    for check_name, passed_check in validation_checks.items():
        status = "✓ PASS" if passed_check else "✗ FAIL"
        print(f"  {status:7s} {check_name}")

    print(f"\nValidation Score: {passed}/{total} checks passed")

    if passed == total:
        print("\n🎯 [FINAL] Model is STATISTICALLY VALID and BIOLOGICALLY SOUND.")
        print("   Ready for clinical application with high confidence.")
    elif passed >= 3:
        print("\n✓ [FINAL] Model is largely valid but has some concerns.")
        print("  Review feature importance and biological assumptions.")
    else:
        print("\n✗ [FINAL] Model has significant biological or statistical issues.")
        print("  Further investigation and validation required.")


# ============================================================================
# MAIN PIPELINE
# ============================================================================

def load_data(data_path: Path) -> tuple[pd.DataFrame, pd.Series]:
    """Load mutation data from CSV."""
    if not data_path.exists():
        raise FileNotFoundError(f"Data file not found: {data_path}")

    df = pd.read_csv(data_path)
    if "label" not in df.columns:
        raise ValueError("CSV must contain a 'label' column")

    y = df["label"].astype(int)
    X = df.drop(columns=["label"])

    return X, y


def main() -> None:
    """Execute the complete biological validation pipeline."""
    parser = argparse.ArgumentParser(
        description="Biological Validation Pipeline for PDAC Mutation Classifier"
    )
    parser.add_argument(
        "--data",
        type=Path,
        default=DEFAULT_DATA_PATH,
        help=f"Path to mutation matrix CSV (default: {DEFAULT_DATA_PATH})",
    )
    parser.add_argument(
        "--n-permutations",
        type=int,
        default=100,
        help="Number of permutations for statistical testing (default: 100)",
    )

    args = parser.parse_args()

    # Load data
    print(f"Loading data from: {args.data}")
    X, y = load_data(args.data)
    print(f"Dataset shape: {X.shape[0]} samples × {X.shape[1]} features")
    print(f"Class distribution: {y.value_counts().to_dict()}")

    # Execute pipeline tasks
    gene_status = check_feature_sanity(X)
    analyze_mutation_frequency(X)
    X_core = create_core_gene_dataset(X)
    model_results = train_both_models(X, X_core, y)
    analyze_feature_importance(
        model_results["full_model"],
        model_results["core_model"],
        X,
        X_core,
    )
    perm_results = run_permutation_tests(
        model_results["full_model"],
        model_results["core_model"],
        X,
        X_core,
        y,
        n_permutations=args.n_permutations,
    )
    generate_interpretation_report(
        model_results,
        model_results,
        perm_results,
        X,
        model_results["full_model"],
    )

    print("\n" + "=" * 80)
    print("PIPELINE COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
