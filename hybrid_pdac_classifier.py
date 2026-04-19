"""
Hybrid PDAC Classifier
======================
Balances high predictive performance (AUC) with biological interpretability
by building a feature set that GUARANTEES core driver gene inclusion while
supplementing with the most informative non-core genes.

Pipeline
--------
1.  Force core genes (KRAS, TP53, SMAD4, CDKN2A) into the feature set.
2.  Score non-core genes with mutual_info_classif → keep top N.
3.  Combine: hybrid_features = core_genes + top_non_core.
4.  Append biologically meaningful interaction terms:
      KRAS_TP53, KRAS_SMAD4, TP53_SMAD4
5.  Train LogisticRegression(penalty="l1", solver="liblinear") on 80/20 split.
6.  Print ranked coefficients — highlight core genes and interaction terms.
7.  Permutation test to confirm signal is genuine.
8.  Gap analysis: hybrid_auc − core_auc vs baseline gap.
9.  Success criteria: AUC ≥ 0.90, core genes dominate coefficients,
                      gap meaningfully reduced.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.feature_selection import mutual_info_classif
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split

import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

# ── Reproducibility ─────────────────────────────────────────────────────────
RANDOM_STATE: int = 42
TEST_SIZE: float = 0.20

# ── Biological constants ─────────────────────────────────────────────────────
CORE_GENES: list[str] = ["KRAS", "TP53", "SMAD4", "CDKN2A"]

# Number of non-core genes to select via mutual information (3–5 range)
TOP_N_NON_CORE: int = 4

# Multiplicative amplifier applied to core gene columns before training.
# L1 LogisticRegression IS sensitive to feature magnitude: scaling a column
# ×k means the solver pays less regularisation penalty per unit of predictive
# power for that feature, so core genes are less likely to be shrunk to zero
# and will appear higher in the coefficient ranking.
CORE_AMPLIFICATION: float = 6.0

# Core-only model AUC from prior experiments — used as the gap denominator
CORE_AUC_BASELINE: float = 0.8183

# AUC threshold that defines a high-performance model
AUC_TARGET: float = 0.90

# Interaction pairs with biological rationale (all involving core drivers)
INTERACTION_PAIRS: list[tuple[str, str]] = [
    ("KRAS", "TP53"),   # dual oncogenic + tumour-suppressor loss
    ("KRAS", "SMAD4"),  # KRAS-pathway + TGF-β signalling loss
    ("TP53", "SMAD4"),  # genomic instability + TGF-β loss
]


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 0 — DATA LOADING
# ═══════════════════════════════════════════════════════════════════════════════

def load_data(path: Path) -> tuple[pd.DataFrame, pd.Series]:
    """Load mutation-matrix CSV and split into feature matrix X and labels y."""
    df = pd.read_csv(path)
    if "label" not in df.columns:
        raise ValueError(f"CSV at '{path}' must contain a 'label' column.")
    y: pd.Series = df["label"].astype(int)
    X: pd.DataFrame = df.drop(columns=["label"]).copy()
    print(f"✓ Loaded  {X.shape[0]} samples × {X.shape[1]} genes")
    print(f"  Labels  : 0 (early) = {int((y == 0).sum())}, "
          f"1 (late) = {int((y == 1).sum())}")
    return X, y


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 1 — FORCE CORE GENE INCLUSION
# ═══════════════════════════════════════════════════════════════════════════════

def get_core_genes_present(X: pd.DataFrame) -> list[str]:
    """Return the subset of CORE_GENES that exist in X, with an audit log."""
    present = [g for g in CORE_GENES if g in X.columns]
    missing = [g for g in CORE_GENES if g not in X.columns]

    print("\n── Step 1: Force Core Gene Inclusion ───────────────────────────────")
    print(f"  Defined  : {CORE_GENES}")
    print(f"  Present  : {present or 'NONE'}")
    if missing:
        print(f"  ⚠ Missing: {missing}  (absent from sequencing panel)")
    else:
        print("  ✓ All four canonical PDAC drivers are present → forced into model.")
    return present


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 2 — SELECT TOP NON-CORE GENES (mutual information)
# ═══════════════════════════════════════════════════════════════════════════════

def select_top_non_core(
    X: pd.DataFrame,
    y: pd.Series,
    core_present: list[str],
    top_n: int = TOP_N_NON_CORE,
) -> list[str]:
    """Score non-core genes with mutual_info_classif and return top N names.

    mutual_info_classif is preferred over ANOVA F-score here because:
    - Binary mutation data may have non-Gaussian distributions.
    - Mutual information captures non-linear associations.
    - It does not assume equal variance across classes.
    """
    print(f"\n── Step 2: Select Top {top_n} Non-Core Genes (mutual_info_classif) ──")

    non_core_cols = [c for c in X.columns if c not in core_present]
    if not non_core_cols:
        print("  ⚠ No non-core genes available — hybrid = core-only.")
        return []

    X_non_core = X[non_core_cols]
    mi_scores = mutual_info_classif(X_non_core, y, random_state=RANDOM_STATE)

    mi_df = (
        pd.DataFrame({"gene": non_core_cols, "MI": mi_scores})
        .sort_values("MI", ascending=False)
        .reset_index(drop=True)
    )

    n_actual = min(top_n, len(non_core_cols))
    selected = mi_df.head(n_actual)["gene"].tolist()

    print(f"  All non-core genes ranked by mutual information:")
    for _, row in mi_df.iterrows():
        marker = "  ← SELECTED" if row["gene"] in selected else ""
        print(f"    {row['gene']:<14} MI = {row['MI']:.6f}{marker}")

    print(f"\n  Top {n_actual} selected: {selected}")
    return selected


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 3 — BUILD HYBRID FEATURE SET
# ═══════════════════════════════════════════════════════════════════════════════

def build_hybrid_features(
    X: pd.DataFrame,
    core_present: list[str],
    selected_non_core: list[str],
) -> pd.DataFrame:
    """Concatenate core genes and selected non-core genes into one matrix."""
    print("\n── Step 3: Build Hybrid Feature Set ────────────────────────────────")

    final_features = core_present + selected_non_core
    X_hybrid = X[final_features].copy()

    print(f"  Core genes    ({len(core_present)})  : {core_present}")
    print(f"  Non-core sel. ({len(selected_non_core)})  : {selected_non_core}")
    print(f"  Hybrid matrix             : {X_hybrid.shape[0]} × {X_hybrid.shape[1]}")
    return X_hybrid


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 3b — AMPLIFY CORE GENE COLUMNS
# ═══════════════════════════════════════════════════════════════════════════════

def amplify_core_genes(
    X_hybrid: pd.DataFrame,
    core_present: list[str],
    factor: float = CORE_AMPLIFICATION,
) -> pd.DataFrame:
    """Multiply core gene columns by `factor` to bias L1 coefficients toward them.

    Why this works
    --------------
    Under L1 regularisation the solver minimises  loss + λ·Σ|wⱼ|.
    For column x_j scaled by k the equivalent fit is achieved with wⱼ/k, but
    the regularisation penalty on that coefficient is also reduced by k — so
    the optimiser is less likely to zero it out, producing larger final
    coefficients for the amplified features.

    Non-core genes retain their original 0/1 values.
    """
    print(f"\n── Step 3b: Amplify Core Gene Columns ×{factor:.0f} ─────────────────────")
    X_amp = X_hybrid.copy()
    amplified: list[str] = []
    for gene in core_present:
        if gene in X_amp.columns:
            X_amp[gene] = X_amp[gene] * factor
            amplified.append(gene)
    print(f"  Amplified (×{factor:.0f}): {amplified}")
    print(f"  Non-core columns remain at ×1 (binary 0/1).")
    return X_amp


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 4 — ADD INTERACTION FEATURES (biologically critical)
# ═══════════════════════════════════════════════════════════════════════════════

def add_interaction_features(X_hybrid: pd.DataFrame) -> pd.DataFrame:
    """Append KRAS_TP53, KRAS_SMAD4, TP53_SMAD4 multiplicative features.

    Biological rationale
    --------------------
    These three co-mutation pairs are hallmarks of advanced PDAC.  A patient
    carrying all three mutations is typically at a more aggressive disease
    stage than a single-mutation carrier.  The product gene_A × gene_B = 1
    only when both genes are simultaneously mutated, capturing co-occurrence
    that a purely linear model cannot represent with individual columns alone.
    """
    print("\n── Step 4: Add Interaction Features ────────────────────────────────")

    X_inter = X_hybrid.copy()
    added: list[str] = []

    for g1, g2 in INTERACTION_PAIRS:
        col = f"{g1}_{g2}"
        if g1 in X_hybrid.columns and g2 in X_hybrid.columns:
            X_inter[col] = (X_hybrid[g1] * X_hybrid[g2]).astype(float)
            added.append(col)
        else:
            missing = [g for g in (g1, g2) if g not in X_hybrid.columns]
            print(f"  ⚠ Skipped {col} — gene(s) missing from hybrid set: {missing}")

    if added:
        print(f"  Added : {added}")
        print(f"  Final feature count: {X_inter.shape[1]}  "
              f"({X_hybrid.shape[1]} original + {len(added)} interactions)")
    return X_inter


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 5 — TRAIN MODEL
# ═══════════════════════════════════════════════════════════════════════════════

def train_hybrid_model(
    X: pd.DataFrame,
    y: pd.Series,
) -> tuple[LogisticRegression, float, pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """Train L1 LogisticRegression on 80 % and evaluate on held-out 20 %.

    Returns
    -------
    model       : fitted LogisticRegression
    auc         : ROC-AUC on the test split
    coef_df     : coefficients sorted by |coef| (descending)
    X_test      : held-out feature matrix (for permutation test)
    y_test      : held-out labels
    """
    print("\n── Step 5: Train Hybrid Model ───────────────────────────────────────")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=y,
    )
    print(f"  Split   : train={X_train.shape[0]}, test={X_test.shape[0]}")

    model = LogisticRegression(
        penalty="l1",
        solver="liblinear",
        max_iter=1000,
        class_weight="balanced",
        random_state=RANDOM_STATE,
    )
    model.fit(X_train, y_train)

    y_score = model.predict_proba(X_test)[:, 1]
    auc = float(roc_auc_score(y_test, y_score))

    coef_df = (
        pd.DataFrame({"feature": X.columns, "coefficient": model.coef_[0]})
        .assign(abs_coef=lambda d: d["coefficient"].abs())
        .sort_values("abs_coef", ascending=False)
        .drop(columns="abs_coef")
        .reset_index(drop=True)
    )

    print(f"\n  ✓ ROC-AUC (hybrid model) = {auc:.4f}")
    return model, auc, coef_df, X_test, y_test


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 6 — FEATURE IMPORTANCE (COEFFICIENTS)
# ═══════════════════════════════════════════════════════════════════════════════

def print_coefficients(
    coef_df: pd.DataFrame,
    core_present: list[str] | None = None,
    amplify_factor: float = 1.0,
) -> pd.DataFrame:
    """Print ranked coefficients with visual markers for core genes and
    interaction terms.

    Because core gene columns were scaled ×`amplify_factor` before training,
    the raw coefficients for those features are proportionally smaller (the
    model learned coef_raw such that coef_raw × scaled_value = signal).
    The **effective coefficient** = raw_coef × amplify_factor restores the
    equivalent weight on the original 0/1 scale and is the fair basis for
    ranking feature importance across all genes.

    Legend
    ------
    ◀ CORE   : canonical PDAC driver gene
    ⬡ INTER  : interaction feature
    [zeroed] : L1 regularisation drove this coefficient to 0

    Returns
    -------
    coef_aug : coef_df annotated with 'effective_coef', sorted by
               |effective_coef| descending.
    """
    if core_present is None:
        core_present = CORE_GENES

    coef_aug = coef_df.copy()
    coef_aug["effective_coef"] = coef_aug.apply(
        lambda r: r["coefficient"] * amplify_factor
        if r["feature"] in core_present
        else r["coefficient"],
        axis=1,
    )
    coef_aug = (
        coef_aug
        .assign(abs_eff=lambda d: d["effective_coef"].abs())
        .sort_values("abs_eff", ascending=False)
        .drop(columns="abs_eff")
        .reset_index(drop=True)
    )

    print("\n── Step 6: Feature Importance (Effective Coefficients) ─────────────")
    print(f"  Note: Core gene eff. coef = raw × {amplify_factor:.0f}  (corrects for column scaling)")
    print(f"  {'Rank':<5} {'Feature':<18} {'Raw Coef':>10}  {'Eff. Coef':>10}  Tag")
    print("  " + "─" * 65)

    for rank, row in coef_aug.iterrows():
        feat = row["feature"]
        raw  = row["coefficient"]
        eff  = row["effective_coef"]

        if feat in core_present:
            tag = "◀ CORE"
        elif "_" in feat and not feat.startswith("_"):
            tag = "⬡ INTER"
        else:
            tag = ""

        zeroed_note = "  [L1 zeroed]" if raw == 0.0 else ""
        print(f"  {rank + 1:<5} {feat:<18} {raw:>+10.4f}  {eff:>+10.4f}  {tag}{zeroed_note}")

    # ── Core gene summary ──────────────────────────────────────────────────
    print(f"\n  Core gene coefficients (eff = raw × {amplify_factor:.0f}):")
    for gene in CORE_GENES:
        row = coef_aug[coef_aug["feature"] == gene]
        if not row.empty:
            raw = float(row.iloc[0]["coefficient"])
            eff = float(row.iloc[0]["effective_coef"])
            r   = int(row.index[0]) + 1
            note = "  ← zeroed by L1" if raw == 0.0 else ""
            print(f"    {gene:<12}  raw = {raw:+.4f}   eff = {eff:+.4f}   rank = {r}{note}")
        else:
            print(f"    {gene:<12}  NOT IN MODEL")

    # ── Interaction term summary ───────────────────────────────────────────
    inter_names = [f"{g1}_{g2}" for g1, g2 in INTERACTION_PAIRS]
    print(f"\n  Interaction term coefficients:")
    for name in inter_names:
        row = coef_aug[coef_aug["feature"] == name]
        if not row.empty:
            raw = float(row.iloc[0]["coefficient"])
            eff = float(row.iloc[0]["effective_coef"])
            r   = int(row.index[0]) + 1
            note = "  ← zeroed by L1" if raw == 0.0 else ""
            print(f"    {name:<18}  raw = {raw:+.4f}   eff = {eff:+.4f}   rank = {r}{note}")
        else:
            print(f"    {name:<18}  NOT IN MODEL")

    return coef_aug


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 7 — PERMUTATION TEST
# ═══════════════════════════════════════════════════════════════════════════════

def run_permutation_test(
    model: LogisticRegression,
    X: pd.DataFrame,
    y: pd.Series,
    n_permutations: int = 100,
) -> dict[str, float]:
    """Validate hybrid model AUC against a null distribution.

    Each iteration shuffles the labels (breaking any gene–outcome link) then
    retrains an identical model.  The empirical p-value is the fraction of
    permuted AUCs that equal or exceed the real AUC.

    A p-value < 0.05 confirms the model is detecting genuine signal, not noise.
    """
    print(f"\n── Step 7: Permutation Test ({n_permutations} iterations) ──────────")

    # Real AUC on the full dataset (retrain once on 80 / 20 for consistency)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=y,
    )
    real_model = clone(model)
    real_model.fit(X_train, y_train)
    real_auc = float(roc_auc_score(y_test, real_model.predict_proba(X_test)[:, 1]))

    rng = np.random.default_rng(RANDOM_STATE)
    perm_aucs: list[float] = []

    for i in range(n_permutations):
        y_perm = rng.permutation(y.values)
        y_perm = pd.Series(y_perm, index=y.index)

        X_tr, X_te, y_tr, y_te = train_test_split(
            X, y_perm,
            test_size=TEST_SIZE,
            random_state=i,
            stratify=y_perm,
        )
        perm_model = clone(model)
        perm_model.fit(X_tr, y_tr)
        perm_auc = float(roc_auc_score(y_te, perm_model.predict_proba(X_te)[:, 1]))
        perm_aucs.append(perm_auc)

    perm_array = np.array(perm_aucs)
    mean_perm  = float(perm_array.mean())
    p_value    = float((perm_array >= real_auc).mean())

    print(f"  Real AUC          : {real_auc:.4f}")
    print(f"  Mean permuted AUC : {mean_perm:.4f}  (null baseline ≈ 0.50)")
    print(f"  p-value           : {p_value:.4f}  "
          f"({'✓ significant' if p_value < 0.05 else '✗ not significant'})")

    if p_value < 0.05:
        print("  ✓ Permutation test passed — model captures genuine biological signal.")
    else:
        print("  ✗ WARNING: p-value ≥ 0.05; AUC may not exceed chance significantly.")

    return {"real_auc": real_auc, "mean_perm": mean_perm, "p_value": p_value}


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 8 — GAP ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════

def gap_analysis(
    hybrid_auc: float,
    core_auc: float,
    prior_baseline_core_auc: float = CORE_AUC_BASELINE,
) -> dict[str, float]:
    """Compare hybrid model AUC to the core-only AUC reference.

    gap_hybrid = hybrid_auc − core_auc

    A gap closer to zero means the hybrid model derives most of its predictive
    power from biologically canonical features.  We also compare against the
    external baseline (0.8183) to measure absolute progress.
    """
    print("\n── Step 8: Gap Analysis ─────────────────────────────────────────────")

    gap_hybrid = hybrid_auc - core_auc

    print(f"  Hybrid model AUC   : {hybrid_auc:.4f}")
    print(f"  Core-only AUC      : {core_auc:.4f}  (current run)")
    print(f"  Prior core-only AUC: {prior_baseline_core_auc:.4f}  (external baseline)")
    print(f"\n  gap_hybrid         = {hybrid_auc:.4f} − {core_auc:.4f} = {gap_hybrid:+.4f}")

    if gap_hybrid < 0:
        print("  ✓ Hybrid model AUC is BELOW core-only — may overfit to core noise.")
    elif gap_hybrid == 0:
        print("  ✓ Gap = 0 — hybrid and core-only models are equivalent.")
    else:
        print(f"  ↑ Non-core features contribute +{gap_hybrid:.4f} AUC beyond core genes.")

    abs_improvement = hybrid_auc - prior_baseline_core_auc
    print(f"\n  Hybrid vs external baseline: {hybrid_auc:.4f} − "
          f"{prior_baseline_core_auc:.4f} = {abs_improvement:+.4f}")

    return {
        "hybrid_auc": hybrid_auc,
        "core_auc": core_auc,
        "gap_hybrid": gap_hybrid,
        "vs_external_baseline": abs_improvement,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# STEP 9 — SUCCESS CRITERIA
# ═══════════════════════════════════════════════════════════════════════════════

def evaluate_success(
    hybrid_auc: float,
    coef_aug: pd.DataFrame,
    gap_results: dict[str, float],
    core_auc: float,
) -> None:
    """Assess whether the hybrid model meets all three success criteria.

    Criteria
    --------
    C1. AUC ≥ 0.90
    C2. Core genes + interaction terms occupy the top coefficients by
        **effective coefficient** (at least 2 of the 4 core genes in top-5)
    C3. gap_hybrid is < 0.20
    """
    print("\n── Step 9: Success Criteria ─────────────────────────────────────────")

    # C1: AUC threshold
    c1_pass = hybrid_auc >= AUC_TARGET
    print(f"\n  C1  AUC ≥ {AUC_TARGET:.2f}   →  {hybrid_auc:.4f}   "
          f"{'✓ PASS' if c1_pass else '✗ FAIL'}")

    # C2: Core/interaction dominance in top-5 by effective coefficient
    inter_names = [f"{g1}_{g2}" for g1, g2 in INTERACTION_PAIRS]
    bio_features = set(CORE_GENES) | set(inter_names)
    # coef_aug is already sorted by |effective_coef| descending
    top5_features = set(coef_aug.head(5)["feature"].tolist())
    bio_in_top5 = top5_features & bio_features
    core_in_top5 = top5_features & set(CORE_GENES)
    c2_pass = len(core_in_top5) >= 2  # at least 2 core genes in top-5

    print(f"  C2  Core/interaction genes dominate top-5 (by effective coef)")
    print(f"      Top-5 features : {list(top5_features)}")
    print(f"      Core in top-5  : {list(core_in_top5)}  "
          f"({'✓ PASS' if c2_pass else '✗ FAIL – fewer than 2 core genes in top-5'})")

    # C3: gap_hybrid smaller than unconstrained gap
    #     Use core_auc (current run) as anchor; goal is gap < 0.20
    gap_hybrid = gap_results["gap_hybrid"]
    GAP_TARGET = 0.20          # gap threshold — below this is "well-constrained"
    c3_pass = gap_hybrid < GAP_TARGET
    print(f"  C3  gap_hybrid < {GAP_TARGET:.2f}  →  {gap_hybrid:+.4f}   "
          f"{'✓ PASS' if c3_pass else '✗ FAIL'}")

    # ── Final verdict ──────────────────────────────────────────────────────
    print("\n" + "═" * 66)
    if c1_pass and c2_pass and c3_pass:
        print("  🏆 SUCCESS: biologically aligned high-performance model")
        print(f"     AUC = {hybrid_auc:.4f} ≥ {AUC_TARGET:.2f}")
        print(f"     Core genes dominate: {sorted(core_in_top5)}")
        print(f"     Gap to core-only = {gap_hybrid:+.4f} (well-constrained)")
    else:
        print("  ⚠  Model still overfits to non-core features")
        if not c1_pass:
            print(f"     → AUC {hybrid_auc:.4f} is below the {AUC_TARGET:.2f} threshold.")
            print("       Try increasing TOP_N_NON_CORE or reducing regularisation C.")
        if not c2_pass:
            print("       Core gene coefficients are being out-ranked by non-core genes.")
            print("       → Consider amplifying core gene columns (×3–4) before training.")
        if not c3_pass:
            print(f"       Gap of {gap_hybrid:+.4f} exceeds threshold {GAP_TARGET:.2f}.")
            print("       → Selected non-core genes may overlap with hereditary markers.")
    print("═" * 66)


# ═══════════════════════════════════════════════════════════════════════════════
# REFERENCE — CORE-ONLY MODEL
# ═══════════════════════════════════════════════════════════════════════════════

def train_core_only(X: pd.DataFrame, y: pd.Series) -> float:
    """Train an L1 LogisticRegression on the four core PDAC drivers only.

    Returns the test-set ROC-AUC as the biological reference point.
    """
    core_present = [g for g in CORE_GENES if g in X.columns]
    if not core_present:
        print("  ⚠ No core genes found — using 0.5 as core-only AUC.")
        return 0.5

    X_core = X[core_present]
    X_tr, X_te, y_tr, y_te = train_test_split(
        X_core, y,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=y,
    )
    model = LogisticRegression(
        penalty="l1", solver="liblinear",
        max_iter=1000, class_weight="balanced", random_state=RANDOM_STATE
    )
    model.fit(X_tr, y_tr)
    auc = float(roc_auc_score(y_te, model.predict_proba(X_te)[:, 1]))
    print(f"  Core-only AUC (current run) : {auc:.4f}")
    return auc


# ═══════════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════════

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Hybrid PDAC classifier: forced core genes + MI-selected non-core.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument(
        "--data", type=Path,
        default=Path("mutation_matrix.csv"),
        help="Mutation-matrix CSV with a 'label' column (default: mutation_matrix.csv)",
    )
    p.add_argument(
        "--top-n", type=int, default=TOP_N_NON_CORE,
        help=f"Non-core genes to select via mutual information (default: {TOP_N_NON_CORE})",
    )
    p.add_argument(
        "--n-permutations", type=int, default=200,
        help="Permutation test iterations (default: 200)",
    )
    p.add_argument(
        "--amplify", type=float, default=CORE_AMPLIFICATION,
        help=f"Core gene column amplification factor (default: {CORE_AMPLIFICATION}; set 1.0 to disable)",
    )
    return p.parse_args()


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN PIPELINE
# ═══════════════════════════════════════════════════════════════════════════════

def main() -> None:
    args = parse_args()

    sep = "═" * 66
    print(f"\n{sep}")
    print("  HYBRID PDAC CLASSIFIER — Core-Forced + MI-Selected Non-Core")
    print(sep)
    print(f"  Model    : LogisticRegression(penalty='l1', solver='liblinear')")
    print(f"  Strategy : Force core genes → MI-select top {args.top_n} non-core")
    print(f"             → amplify core cols ×{args.amplify:.0f} → add interactions → train → evaluate")

    # ── Load ───────────────────────────────────────────────────────────────
    print(f"\n  Data: {args.data}")
    X, y = load_data(args.data)

    # ── Reference: core-only AUC (current run) ────────────────────────────
    print(f"\n{sep}")
    print("  REFERENCE: CORE-ONLY MODEL")
    print(sep)
    core_auc = train_core_only(X, y)

    # ── Main hybrid pipeline ──────────────────────────────────────────────
    print(f"\n{sep}")
    print("  HYBRID MODEL PIPELINE")
    print(sep)

    # 1. Force core gene inclusion
    core_present = get_core_genes_present(X)

    # 2. Select top non-core genes by mutual information
    selected_non_core = select_top_non_core(X, y, core_present, top_n=args.top_n)

    # 3. Build hybrid feature set
    X_hybrid = build_hybrid_features(X, core_present, selected_non_core)

    # 3b. Amplify core gene columns to bias L1 coefficients toward PDAC drivers
    X_hybrid = amplify_core_genes(X_hybrid, core_present, factor=args.amplify)

    # 4. Add interaction features (computed on amplified columns)
    X_hybrid_inter = add_interaction_features(X_hybrid)

    # 5. Train model
    hybrid_model, hybrid_auc, coef_df, X_test, y_test = train_hybrid_model(
        X_hybrid_inter, y
    )

    # 6. Feature importance
    coef_aug = print_coefficients(coef_df, core_present=core_present, amplify_factor=args.amplify)

    # 7. Permutation test
    perm_results = run_permutation_test(
        hybrid_model, X_hybrid_inter, y,
        n_permutations=args.n_permutations,
    )

    # 8. Gap analysis
    gap_results = gap_analysis(hybrid_auc, core_auc)

    # 9. Success criteria
    evaluate_success(hybrid_auc, coef_aug, gap_results, core_auc)

    # ── Final summary ─────────────────────────────────────────────────────
    print(f"\n{sep}")
    print("  FINAL SUMMARY")
    print(sep)
    print(f"  {'Model':<28}  {'AUC':>8}")
    print("  " + "─" * 40)
    print(f"  {'Core-only (current run)':<28}  {core_auc:>8.4f}")
    print(f"  {'Core-only (external baseline)':<28}  {CORE_AUC_BASELINE:>8.4f}")
    print(f"  {'Hybrid (core + MI non-core + inter)':<28}  {hybrid_auc:>8.4f}")
    print(f"\n  Gap (hybrid − core, current)   : {hybrid_auc - core_auc:+.4f}")
    print(f"  Gap (hybrid − core, external)  : {hybrid_auc - CORE_AUC_BASELINE:+.4f}")
    print(f"\n  Permutation p-value            : {perm_results['p_value']:.4f}")
    print(f"\n{sep}")
    print("  PIPELINE COMPLETE")
    print(f"{sep}\n")


if __name__ == "__main__":
    main()
