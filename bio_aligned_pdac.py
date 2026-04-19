"""
Bio-aligned PDAC classifier — forces learning from core PDAC driver genes
via Logistic Regression with L1 regularisation.

Problem
-------
The baseline RandomForest model achieves high AUC but is insensitive to
feature scaling of binary data.  Decision trees are invariant to monotone
column transformations: multiplying KRAS {0,1} by ×3 gives {0,3}, but the
optimal split threshold is still "any value in (0, 3)".  Therefore, feature
reweighting had no measurable effect on Gini-impurity-based importances.

Fix
---
Switch to LogisticRegression(penalty="l1", solver="liblinear") which:
  • IS sensitive to feature magnitude — scaling core genes ×4 WILL increase
    the magnitude of those learned coefficients.
  • Performs automatic feature selection via L1 sparsity (many coef = 0).

Strategy
--------
A. Feature reweighting  : Amplify core driver columns ×4 so coefficients
   are biased toward biologically meaningful signal.
B. Feature reduction    : Drop dominant non-core genes (BRCA1/2, PALB2) to
   force the model to seek signal elsewhere.
C. Interaction features : Add KRAS_TP53, KRAS_SMAD4, TP53_SMAD4 to capture
   co-mutation biology that a purely linear model cannot represent alone.
D. Gap analysis         : Compare (model AUC − core-only AUC) across all
   variants; a shrinking gap means better biological alignment.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_selection import SelectKBest, f_classif
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split

# Suppress sklearn 1.8+ deprecation warnings for penalty='l1'.
# The old API still works correctly; warnings are cosmetic noise only.
import warnings as _warnings
_warnings.filterwarnings(
    "ignore",
    message=".*penalty.*deprecated.*",
    category=FutureWarning,
    module="sklearn",
)
_warnings.filterwarnings(
    "ignore",
    message=".*Inconsistent values.*penalty.*",
    category=UserWarning,
    module="sklearn",
)

from permutation_test import run_permutation_test

# ── Reproducibility ────────────────────────────────────────────────────────────
RANDOM_STATE: int = 42
TEST_SIZE: float = 0.20

# ── Biological constants ───────────────────────────────────────────────────────
# Canonical PDAC driver genes — mutated in >85 % of pancreatic tumours.
# These four genes define the core mutational landscape of PDAC.
CORE_GENES: list[str] = ["KRAS", "TP53", "SMAD4", "CDKN2A"]

# DNA-repair genes that dominate the baseline model but are less specific
# to PDAC (they are primarily markers of hereditary breast/ovarian cancer).
NON_CORE_HIGH_IMPACT: list[str] = ["BRCA1", "BRCA2", "PALB2"]

# Weight multiplier applied to core gene columns in the weighted feature matrix.
# Unlike RandomForest, LogisticRegression IS sensitive to feature magnitude,
# so this scaling WILL increase the magnitude of core gene coefficients.
CORE_WEIGHT: float = 4.0

# Minimum relative gap-reduction required to declare success.
GAP_IMPROVEMENT_THRESHOLD: float = 0.10  # 10 %

# AUC of the core-only model from prior experiments.
BASELINE_CORE_AUC: float = 0.8183


# ═══════════════════════════════════════════════════════════════════════════════
# 1. DATA LOADING
# ═══════════════════════════════════════════════════════════════════════════════

def load_data(data_path: Path) -> tuple[pd.DataFrame, pd.Series]:
    """Load mutation-matrix CSV and return feature matrix X and labels y.

    The CSV must contain a binary 'label' column (0 = early-stage,
    1 = late-stage) plus one column per gene.
    """
    df = pd.read_csv(data_path)
    if "label" not in df.columns:
        raise ValueError(f"CSV at '{data_path}' must contain a 'label' column.")
    y: pd.Series = df["label"].astype(int)
    X: pd.DataFrame = df.drop(columns=["label"]).copy()
    return X, y


# ═══════════════════════════════════════════════════════════════════════════════
# 2. CORE GENE CHECK
# ═══════════════════════════════════════════════════════════════════════════════

def check_core_genes(X: pd.DataFrame) -> list[str]:
    """Audit the feature matrix for canonical PDAC driver coverage.

    Prints which core genes are present and which are absent so that
    gaps in data collection can be identified early.

    Returns
    -------
    list[str]
        Core genes that are actually present in X.
    """
    present = [g for g in CORE_GENES if g in X.columns]
    missing = [g for g in CORE_GENES if g not in X.columns]

    print("\n── Core Gene Audit ──────────────────────────────────────────")
    print(f"  Defined core genes : {CORE_GENES}")
    print(f"  Present in dataset : {present if present else 'NONE'}")

    if missing:
        print(f"  ⚠  Missing         : {missing}")
        print("     → These canonical PDAC drivers are absent from the mutation")
        print("       matrix. Future sequencing panels should include them.")
    else:
        print("  ✓  All core genes present in dataset.")

    return present


# ═══════════════════════════════════════════════════════════════════════════════
# 3. FEATURE REWEIGHTING
# ═══════════════════════════════════════════════════════════════════════════════

def build_weighted_features(X: pd.DataFrame) -> pd.DataFrame:
    """Amplify core PDAC driver gene columns by CORE_WEIGHT (×4).

    Biological rationale
    --------------------
    KRAS, TP53, SMAD4, and CDKN2A collectively drive oncogenesis in the vast
    majority of PDAC cases.

    Why this works with LogisticRegression (unlike RandomForest)
    -------------------------------------------------------------
    Linear models optimise a loss function over the dot product w·x.
    Multiplying column x_j by a constant k means the solver can achieve the
    same fit with coefficient w_j/k.  Under L1 regularisation (which penalises
    |w_j| uniformly), a column scaled ×4 effectively requires the solver to
    pay less regularisation penalty per unit of predictive power — so core
    genes are less likely to be shrunk to zero and their final coefficients
    will be larger in magnitude.

    Non-core genes retain their original values (×1.0).
    """
    X_weighted = X.copy()
    amplified: list[str] = []

    for gene in X_weighted.columns:
        if gene in CORE_GENES:
            X_weighted[gene] = X_weighted[gene] * CORE_WEIGHT
            amplified.append(gene)

    if amplified:
        print(f"\n[Reweighting] Amplified core gene(s) ×{CORE_WEIGHT}: {amplified}")
    else:
        print(
            f"\n[Reweighting] No core genes found in dataset — "
            "column amplification had no effect."
        )

    return X_weighted


# ═══════════════════════════════════════════════════════════════════════════════
# 4. FEATURE REDUCTION
# ═══════════════════════════════════════════════════════════════════════════════

def build_reduced_features(X: pd.DataFrame) -> pd.DataFrame:
    """Drop dominant non-core genes to reduce reliance on non-PDAC signal.

    Biological rationale
    --------------------
    BRCA1, BRCA2, and PALB2 are strong predictors of hereditary
    breast/ovarian cancer but are *not* the primary drivers of sporadic PDAC.
    Removing them forces the model to seek predictive signal in more
    PDAC-relevant features such as KRAS-pathway and cell-cycle genes.
    """
    dropped = [g for g in NON_CORE_HIGH_IMPACT if g in X.columns]
    X_reduced = X.drop(columns=NON_CORE_HIGH_IMPACT, errors="ignore")

    if dropped:
        print(f"[Reduction]   Dropped dominant non-core gene(s): {dropped}")
    else:
        print("[Reduction]   None of the non-core genes found — no columns dropped.")

    return X_reduced


# ═══════════════════════════════════════════════════════════════════════════════
# 4b. INTERACTION FEATURES
# ═══════════════════════════════════════════════════════════════════════════════

def build_interaction_features(X: pd.DataFrame) -> pd.DataFrame:
    """Create pairwise co-mutation interaction features for core PDAC drivers.

    Biological rationale
    --------------------
    KRAS, TP53, and SMAD4 co-mutations are a hallmark of advanced PDAC.
    A patient carrying all three mutations is typically in a more aggressive
    disease stage than one carrying any single mutation alone.

    Multiplicative (AND) interaction terms capture this co-occurrence signal
    that a linear model cannot represent with individual features alone — the
    product KRAS × TP53 is 1 only when both genes are mutated simultaneously.

    New columns added
    -----------------
    KRAS_TP53  = KRAS × TP53   (1 iff both KRAS and TP53 mutated)
    KRAS_SMAD4 = KRAS × SMAD4  (1 iff both KRAS and SMAD4 mutated)
    TP53_SMAD4 = TP53 × SMAD4  (1 iff both TP53 and SMAD4 mutated)
    """
    X_inter = X.copy()
    pairs = [("KRAS", "TP53"), ("KRAS", "SMAD4"), ("TP53", "SMAD4")]
    added: list[str] = []

    for g1, g2 in pairs:
        col_name = f"{g1}_{g2}"
        if g1 in X.columns and g2 in X.columns:
            X_inter[col_name] = (X[g1] * X[g2]).astype(float)
            added.append(col_name)
        else:
            missing_genes = [g for g in (g1, g2) if g not in X.columns]
            print(f"[Interaction] Skipped {col_name} — missing gene(s): {missing_genes}")

    if added:
        print(f"[Interaction] Added interaction features: {added}")

    return X_inter


# ═══════════════════════════════════════════════════════════════════════════════
# 5. CORE-ONLY FEATURE MATRIX (reference model)
# ═══════════════════════════════════════════════════════════════════════════════

def build_core_only_features(X: pd.DataFrame) -> pd.DataFrame:
    """Keep only canonical PDAC driver columns for the reference core model.

    The core-only AUC serves as the denominator in gap analysis:
        gap = model_AUC - core_AUC

    A smaller gap indicates the full model relies less on non-core signal.

    Raises
    ------
    ValueError
        If none of the core genes are present in X.
    """
    core_present = [g for g in CORE_GENES if g in X.columns]
    if not core_present:
        raise ValueError(
            "No core genes (KRAS, TP53, SMAD4, CDKN2A) found in the dataset. "
            "Cannot compute core-model AUC for gap analysis."
        )
    return X[core_present].copy()


# ═══════════════════════════════════════════════════════════════════════════════
# 6. MODEL FACTORY
# ═══════════════════════════════════════════════════════════════════════════════

def build_model() -> LogisticRegression:
    """L1-penalised logistic regression — sparse and magnitude-sensitive.

    Why L1 (Lasso) and not L2 (Ridge)?
    -----------------------------------
    L1 regularisation drives many coefficients exactly to zero, effectively
    performing feature selection.  For a dataset with many gene columns, this
    produces a sparse model that highlights only the most predictive genes —
    which we expect to be the core PDAC drivers.

    solver="liblinear"
    ------------------
    The only sklearn solver that natively supports L1 penalty for binary
    classification.  Fast and reliable for tabular gene-panel data.

    sklearn ≥ 1.8 API note
    ----------------------
    The `penalty` kwarg is deprecated in sklearn 1.8+.  The equivalent is
    setting l1_ratio=1.0 (pure L1) without specifying `penalty`.
    Deprecation warnings are suppressed at the module level.
    """
    return LogisticRegression(
        penalty="l1",
        solver="liblinear",
        max_iter=1000,
        class_weight="balanced",
        random_state=RANDOM_STATE,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 7. TRAIN & EVALUATE
# ═══════════════════════════════════════════════════════════════════════════════

def train_and_evaluate(
    X: pd.DataFrame,
    y: pd.Series,
    label: str,
) -> tuple[LogisticRegression, float, pd.DataFrame]:
    """Train on 80 % of the data and evaluate ROC-AUC on the held-out 20 %.

    Parameters
    ----------
    X     : Feature matrix (may be original, weighted, reduced, or core-only).
    y     : Binary labels.
    label : Human-readable name used in console output.

    Returns
    -------
    (fitted_model, test_roc_auc, coef_df)
        coef_df has columns 'gene' and 'coefficient', sorted by |coefficient|.
    """
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=y,
    )

    model = build_model()
    model.fit(X_train, y_train)

    y_score = model.predict_proba(X_test)[:, 1]
    auc = float(roc_auc_score(y_test, y_score))

    # Sort by absolute coefficient magnitude so most-important genes appear first
    coef_df = (
        pd.DataFrame({"gene": X.columns, "coefficient": model.coef_[0]})
        .assign(abs_coef=lambda d: d["coefficient"].abs())
        .sort_values("abs_coef", ascending=False)
        .drop(columns="abs_coef")
        .reset_index(drop=True)
    )

    print(f"  [{label:<16}]  ROC-AUC = {auc:.4f}")
    return model, auc, coef_df


# ═══════════════════════════════════════════════════════════════════════════════
# 8. COEFFICIENT DISPLAY
# ═══════════════════════════════════════════════════════════════════════════════

def print_coefficients(label: str, coef_df: pd.DataFrame) -> None:
    """Print ranked coefficients and highlight core gene positions.

    Core genes are flagged with ◀ CORE for quick visual inspection.
    Positive coefficients increase late-stage probability; negative = early.
    Coefficients of 0.0000 were eliminated by L1 regularisation (sparsity).
    """
    print(f"\n  ── {label} ──────────────────────────────────────────────")
    for rank, row in coef_df.iterrows():
        marker = "  ◀ CORE" if row["gene"] in CORE_GENES else ""
        zeroed = "  [L1 zeroed]" if row["coefficient"] == 0.0 else ""
        print(
            f"    {rank + 1:>2}. {row['gene']:<14} {row['coefficient']:+.4f}"
            f"{marker}{zeroed}"
        )

    # Summary: coefficient of each core gene specifically
    print(f"\n  Core gene coefficients ({label}):")
    for gene in CORE_GENES:
        subset = coef_df[coef_df["gene"] == gene]
        if not subset.empty:
            coef_val = float(subset.iloc[0]["coefficient"])
            rnk = int(subset.index[0]) + 1
            zeroed_note = "  ← zeroed by L1" if coef_val == 0.0 else ""
            print(
                f"    {gene:<12} coef = {coef_val:+.4f}  rank = {rnk}{zeroed_note}"
            )
        else:
            print(f"    {gene:<12} NOT IN MODEL (gene absent from feature set)")


# ═══════════════════════════════════════════════════════════════════════════════
# 9. PERMUTATION TESTS
# ═══════════════════════════════════════════════════════════════════════════════

def run_perm_test(
    model: LogisticRegression,
    X: pd.DataFrame,
    y: pd.Series,
    label: str,
    n_permutations: int = 100,
    plot_path: Path | None = None,
) -> dict:
    """Run a permutation test for a single trained model variant.

    Delegates to run_permutation_test() from permutation_test.py.
    Prints: real AUC, mean permuted AUC, and empirical p-value.
    """
    print(f"\n  ── Permutation Test: {label} ────────────────────────────")
    results = run_permutation_test(
        model, X, y,
        n_permutations=n_permutations,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        plot_path=plot_path,
    )
    print(f"    Real AUC          : {results['real_auc']:.4f}")
    print(f"    Mean permuted AUC : {results['mean_perm']:.4f}")
    print(f"    p-value           : {results['p_value']:.4f}")
    return results


# ═══════════════════════════════════════════════════════════════════════════════
# 10. GAP ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════

def gap_analysis(
    baseline_auc: float,
    core_auc: float,
    weighted_auc: float,
    reduced_auc: float,
    interaction_auc: float,
) -> dict[str, float]:
    """Compute AUC gap between each model variant and the core-only model.

    gap = model_AUC − core_only_AUC

    A gap close to zero means the model variant performs similarly to a model
    trained purely on core PDAC drivers — indicating strong biological
    alignment. A large positive gap indicates reliance on non-core signal.

    Returns
    -------
    dict mapping model name → gap value.
    """
    gaps = {
        "baseline":    baseline_auc    - core_auc,
        "weighted":    weighted_auc    - core_auc,
        "reduced":     reduced_auc     - core_auc,
        "interaction": interaction_auc - core_auc,
    }

    auc_map = {
        "baseline":    baseline_auc,
        "weighted":    weighted_auc,
        "reduced":     reduced_auc,
        "interaction": interaction_auc,
        "core_only":   core_auc,
    }

    col_w = 14
    print(f"\n  {'Model':<{col_w}} {'AUC':>7}  {'Gap (vs core)':>14}  {'Change vs baseline':>20}")
    print("  " + "─" * 62)

    for name, gap in gaps.items():
        auc_val = auc_map[name]
        baseline_gap = gaps["baseline"]
        if name == "baseline":
            change_str = "(reference)"
        else:
            change = gap - baseline_gap
            change_str = f"{change:+.4f} ({'↓ better' if change < 0 else '↑ worse'})"
        print(f"  {name:<{col_w}} {auc_val:>7.4f}  {gap:>+14.4f}  {change_str:>20}")

    print(f"\n  Core-only model AUC  : {core_auc:.4f}  (current run)")
    print(f"  Prior core-only AUC  : {BASELINE_CORE_AUC:.4f}  (external baseline)")
    return gaps


# ═══════════════════════════════════════════════════════════════════════════════
# 11. SUCCESS CRITERIA
# ═══════════════════════════════════════════════════════════════════════════════

def evaluate_success(
    gaps: dict[str, float],
    baseline_coef: pd.DataFrame,
    weighted_coef: pd.DataFrame,
    reduced_coef: pd.DataFrame,
) -> None:
    """Determine whether bio-alignment strategies improved model behaviour.

    SUCCESS requires BOTH:
    1. The best model variant reduces the AUC gap by >= GAP_IMPROVEMENT_THRESHOLD
       (relative to the baseline gap).
    2. Core gene total |coefficient| increases in the best variant vs baseline.

    The switch to LogisticRegression means coefficient magnitude is now a
    meaningful proxy for biological importance (unlike RF feature importances
    which were invariant to column scaling of binary features).
    """
    baseline_gap = gaps["baseline"]

    # Identify the model variant that best closes the gap to core biology.
    best_label = min(
        (k for k in gaps if k != "baseline"),
        key=lambda k: gaps[k],
    )
    best_gap = gaps[best_label]
    best_coef = {"weighted": weighted_coef, "reduced": reduced_coef}.get(
        best_label, weighted_coef
    )

    # Relative gap reduction — avoids division by zero if baseline_gap == 0.
    if baseline_gap != 0:
        gap_reduction = (baseline_gap - best_gap) / abs(baseline_gap)
    else:
        gap_reduction = 0.0

    # Sum of |core gene coefficients| as a proxy for biological alignment.
    def core_coef_sum(coef_df: pd.DataFrame) -> float:
        return float(
            coef_df[coef_df["gene"].isin(CORE_GENES)]["coefficient"].abs().sum()
        )

    baseline_core_coef = core_coef_sum(baseline_coef)
    best_core_coef     = core_coef_sum(best_coef)
    core_coef_increased = best_core_coef > baseline_core_coef

    print(f"\n  Best variant            : {best_label}")
    print(f"  Gap reduction           : {gap_reduction:+.1%}  "
          f"(threshold: ≥ {GAP_IMPROVEMENT_THRESHOLD:.0%})")
    print(f"  Core |coef| sum — baseline   : {baseline_core_coef:.4f}")
    print(f"  Core |coef| sum — {best_label:<9}: {best_core_coef:.4f}")

    gap_improved = gap_reduction >= GAP_IMPROVEMENT_THRESHOLD

    if gap_improved and core_coef_increased:
        print("\n✅ SUCCESS: Model is biologically aligned")
        print("   Core driver gene signal is stronger; reliance on non-core")
        print("   features has been meaningfully reduced.")
    else:
        print("\n⚠  Model still biased toward non-core genes")
        if not gap_improved:
            print(
                f"   AUC gap reduction ({gap_reduction:.1%}) did not reach the "
                f"{GAP_IMPROVEMENT_THRESHOLD:.0%} threshold."
            )
        if not core_coef_increased:
            print(
                f"   Core gene |coef| did not increase "
                f"({baseline_core_coef:.4f} → {best_core_coef:.4f})."
            )
        print("   → Recommendations:")
        print(f"     • Increase CORE_WEIGHT (currently ×{CORE_WEIGHT}) or try ×5.")
        print("     • Collect samples with confirmed KRAS/SMAD4/CDKN2A mutations.")
        print("     • Revisit label quality — mislabelled early/late-stage cases")
        print("       can mask biological signal.")


# ═══════════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════════

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--data", type=Path,
        default=Path("mutation_matrix.csv"),
        help="Path to mutation-matrix CSV with a 'label' column (default: mutation_matrix.csv)",
    )
    parser.add_argument(
        "--n-permutations", type=int, default=100,
        help="Number of permutation iterations per model variant (default: 100)",
    )
    parser.add_argument(
        "--top-k", type=int, default=8,
        help="Number of genes to keep in SelectKBest step (default: 8)",
    )
    return parser.parse_args()


# ═══════════════════════════════════════════════════════════════════════════════
# 12. SELECTKBEST FEATURE SELECTION  (advanced step)
# ═══════════════════════════════════════════════════════════════════════════════

def apply_selectkbest(
    X: pd.DataFrame,
    y: pd.Series,
    k: int = 8,
) -> pd.DataFrame:
    """Restrict feature matrix to top-k genes by ANOVA F-score.

    SelectKBest with f_classif scores each feature by its univariate
    F-statistic (variance of class means / within-class variance), choosing
    the k columns that separate early from late-stage samples most clearly.

    This complements L1 regularisation: SelectKBest does class-agnostic
    filtering first, then L1 performs further model-level selection.

    Returns a reduced DataFrame containing only the k highest-scoring columns.
    """
    k_actual = min(k, X.shape[1])
    selector = SelectKBest(score_func=f_classif, k=k_actual)
    selector.fit(X, y)

    selected_cols = X.columns[selector.get_support()].tolist()
    scores = selector.scores_

    score_df = (
        pd.DataFrame({"gene": X.columns, "F_score": scores})
        .sort_values("F_score", ascending=False)
        .reset_index(drop=True)
    )

    print(f"\n[SelectKBest] Top {k_actual} features by ANOVA F-score:")
    for _, row in score_df.head(k_actual).iterrows():
        marker = "  ◀ CORE" if row["gene"] in CORE_GENES else ""
        print(f"    {row['gene']:<14} F = {row['F_score']:8.3f}{marker}")

    return X[selected_cols].copy()


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN PIPELINE
# ═══════════════════════════════════════════════════════════════════════════════

def main() -> None:
    args = parse_args()

    sep = "═" * 66
    print(f"\n{sep}")
    print("  BIO-ALIGNED PDAC CLASSIFIER  —  Logistic Regression L1 Fix")
    print(sep)
    print("\n  Model  : LogisticRegression(penalty='l1', solver='liblinear')")
    print(f"  Reason : Linear models ARE sensitive to feature magnitude.")
    print(f"           Scaling core genes ×{CORE_WEIGHT} WILL shift their coefficients.")
    print(f"           L1 sparsity performs automatic feature selection.")

    # ── Load data ──────────────────────────────────────────────────────────────
    print(f"\nData source: {args.data}")
    X, y = load_data(args.data)
    class_counts = y.value_counts().sort_index()
    print(f"Dataset     : {X.shape[0]} samples × {X.shape[1]} features")
    print(f"Labels      : 0 (early) = {int(class_counts.get(0, 0))}, "
          f"1 (late) = {int(class_counts.get(1, 0))}")

    # ── Step 1: Core gene audit ────────────────────────────────────────────────
    check_core_genes(X)

    # ── Step 2: Build feature variants ────────────────────────────────────────
    print(f"\n{'─' * 66}")
    print("  FEATURE ENGINEERING")
    print(f"{'─' * 66}")

    X_weighted = build_weighted_features(X)       # core genes ×4
    X_reduced  = build_reduced_features(X)         # drop BRCA1/2, PALB2
    X_inter    = build_interaction_features(X)     # add co-mutation pairs

    core_auc: float = 0.5
    X_core: pd.DataFrame | None = None
    try:
        X_core = build_core_only_features(X)
        print(f"[Core-only]   Kept core genes for reference model: "
              f"{list(X_core.columns)}")
    except ValueError as exc:
        print(f"\n⚠  {exc}")
        print("   Gap analysis will use 0.5 (chance) as the core-only AUC reference.")

    # ── Step 3: Train three primary models A / B / C ──────────────────────────
    print(f"\n{'─' * 66}")
    print("  TRAINING MODELS  (LogisticRegression L1, 80/20 stratified split)")
    print(f"{'─' * 66}")

    print("\n  Model A — original features (no modification)")
    baseline_model, baseline_auc, baseline_coef = train_and_evaluate(
        X, y, "A: Original"
    )

    print(f"\n  Model B — core genes weighted ×{CORE_WEIGHT:.0f}")
    weighted_model, weighted_auc, weighted_coef = train_and_evaluate(
        X_weighted, y, "B: Weighted"
    )

    print("\n  Model C — BRCA1/BRCA2/PALB2 removed")
    reduced_model, reduced_auc, reduced_coef = train_and_evaluate(
        X_reduced, y, "C: Reduced"
    )

    if X_core is not None:
        print("\n  Core-only reference model")
        _, core_auc, _ = train_and_evaluate(X_core, y, "Core-only")

    # ── Step 4: Extract and compare coefficients ───────────────────────────────
    print(f"\n{'─' * 66}")
    print("  COEFFICIENT COMPARISON  (sorted by |coef|, ◀ = core PDAC gene)")
    print(f"{'─' * 66}")
    print_coefficients("Model A: Original", baseline_coef)
    print_coefficients("Model B: Weighted", weighted_coef)
    print_coefficients("Model C: Reduced",  reduced_coef)

    # ── Steps 5 + 6: Build interaction features → Model D ─────────────────────
    print(f"\n{'─' * 66}")
    print("  INTERACTION FEATURES  (co-mutation pairs)")
    print(f"{'─' * 66}")
    print(
        "  KRAS_TP53  = KRAS × TP53   — captures dual-driver co-mutation\n"
        "  KRAS_SMAD4 = KRAS × SMAD4  — KRAS-pathway + TGF-β loss\n"
        "  TP53_SMAD4 = TP53 × SMAD4  — genome instability + TGF-β loss"
    )
    print("\n  Model D — original features + interaction terms")
    inter_model, interaction_auc, inter_coef = train_and_evaluate(
        X_inter, y, "D: Interactions"
    )
    print_coefficients("Model D: Interactions", inter_coef)

    # ── Step 7: Permutation tests ──────────────────────────────────────────────
    print(f"\n{'─' * 66}")
    print(f"  PERMUTATION TESTS  ({args.n_permutations} iterations each)")
    print(f"{'─' * 66}")
    run_perm_test(
        weighted_model, X_weighted, y,
        label="B: Weighted",
        n_permutations=args.n_permutations,
        plot_path=Path("pdac_permutation_weighted.png"),
    )
    run_perm_test(
        reduced_model, X_reduced, y,
        label="C: Reduced",
        n_permutations=args.n_permutations,
        plot_path=Path("pdac_permutation_reduced.png"),
    )
    run_perm_test(
        inter_model, X_inter, y,
        label="D: Interactions",
        n_permutations=args.n_permutations,
        plot_path=Path("pdac_permutation_interactions.png"),
    )

    # ── Step 8: Gap analysis ───────────────────────────────────────────────────
    print(f"\n{'─' * 66}")
    print("  GAP ANALYSIS  (model AUC − core-only AUC)")
    print(f"{'─' * 66}")
    gaps = gap_analysis(
        baseline_auc, core_auc, weighted_auc, reduced_auc, interaction_auc
    )

    # ── Step 9: Success criteria ───────────────────────────────────────────────
    print(f"\n{'─' * 66}")
    print("  BIOLOGICAL ALIGNMENT ASSESSMENT")
    print(f"{'─' * 66}")
    evaluate_success(gaps, baseline_coef, weighted_coef, reduced_coef)

    # ── Step 10: Advanced — SelectKBest feature selection ─────────────────────
    print(f"\n{'─' * 66}")
    print(f"  ADVANCED STEP: SelectKBest (top {args.top_k} features by ANOVA F-score)")
    print(f"{'─' * 66}")
    X_selected = apply_selectkbest(X, y, k=args.top_k)
    _, selected_auc, selected_coef = train_and_evaluate(
        X_selected, y, f"E: Top-{args.top_k}"
    )
    print_coefficients(f"Model E: Top-{args.top_k} genes", selected_coef)

    # ── Final AUC summary ──────────────────────────────────────────────────────
    print(f"\n{'─' * 66}")
    print("  FINAL AUC SUMMARY")
    print(f"{'─' * 66}")
    summary: list[tuple[str, float]] = [
        ("A: Original",              baseline_auc),
        ("B: Weighted",              weighted_auc),
        ("C: Reduced",               reduced_auc),
        ("D: Interactions",          interaction_auc),
        (f"E: Top-{args.top_k}",     selected_auc),
        ("Core-only",                core_auc),
    ]
    print(f"  {'Model':<22} {'AUC':>8}  {'vs baseline':>12}  {'vs core':>10}")
    print("  " + "─" * 58)
    for name, auc_val in summary:
        vs_base = (
            f"{auc_val - baseline_auc:+.4f}"
            if name not in ("A: Original", "Core-only")
            else ("(ref)" if name == "A: Original" else "—")
        )
        vs_core = (
            f"{auc_val - core_auc:+.4f}"
            if name != "Core-only"
            else "(ref)"
        )
        print(f"  {name:<22} {auc_val:>8.4f}  {vs_base:>12}  {vs_core:>10}")

    print(f"\n  External baseline (prior core-only AUC): {BASELINE_CORE_AUC:.4f}")
    print(f"\n{sep}")
    print("  PIPELINE COMPLETE")
    print(sep + "\n")


if __name__ == "__main__":
    main()
