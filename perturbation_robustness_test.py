"""
Perturbation Robustness Test — Hybrid PDAC Classifier
======================================================
Tests whether the biologically constrained hybrid model captures stable
PDAC biology or merely reflects dataset-specific BRCA1/2 bias.

Perturbations applied to mutation_matrix.csv
--------------------------------------------
A. Baseline          : original data, no modification
B. BRCA ×0.5        : BRCA1/2 columns multiplied by 0.5
C. BRCA ×0.25       : BRCA1/2 columns multiplied by 0.25
D. Dropout 20 %     : 20 % of BRCA1/2 mutations randomly zeroed
E. Dropout 40 %     : 40 % of BRCA1/2 mutations randomly zeroed
F. Freq-balanced    : BRCA1/2 mutation frequency reduced to match KRAS frequency
G. BRCA removed     : BRCA1/2 dropped entirely (maximum reduction)

For each condition the hybrid pipeline is run identically:
  core forced → MI non-core selection → core amplified ×6 → interactions → train
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_selection import mutual_info_classif
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split

import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

# ── shared constants (keep in sync with hybrid_pdac_classifier.py) ──────────
RANDOM_STATE: int = 42
TEST_SIZE:    float = 0.20
CORE_GENES:   list[str] = ["KRAS", "TP53", "SMAD4", "CDKN2A"]
BRCA_GENES:   list[str] = ["BRCA1", "BRCA2"]
TOP_N:        int = 4          # non-core genes to select per run
AMPLIFY:      float = 6.0      # core gene column amplification
INTERACTION_PAIRS = [("KRAS", "TP53"), ("KRAS", "SMAD4"), ("TP53", "SMAD4")]
AUC_DROP_THRESHOLD: float = 0.05   # max acceptable AUC drop vs baseline


# ═══════════════════════════════════════════════════════════════════════════════
# PERTURBATION GENERATORS
# ═══════════════════════════════════════════════════════════════════════════════

def perturb_scale(X: pd.DataFrame, factor: float) -> pd.DataFrame:
    """Multiply BRCA1/2 columns by `factor` (e.g. 0.5, 0.25)."""
    Xp = X.copy()
    for g in BRCA_GENES:
        if g in Xp.columns:
            Xp[g] = Xp[g] * factor
    return Xp


def perturb_dropout(X: pd.DataFrame, rate: float, seed: int = 0) -> pd.DataFrame:
    """Randomly zero `rate` fraction of positive BRCA1/2 entries."""
    Xp = X.copy()
    rng = np.random.default_rng(seed)
    for g in BRCA_GENES:
        if g in Xp.columns:
            mut_idx = Xp.index[Xp[g] == 1].tolist()
            n_drop  = int(len(mut_idx) * rate)
            drop_idx = rng.choice(mut_idx, size=n_drop, replace=False)
            Xp.loc[drop_idx, g] = 0
    return Xp


def perturb_freq_balance(X: pd.DataFrame) -> pd.DataFrame:
    """Reduce BRCA1/2 mutation frequency to match KRAS mutation frequency.

    KRAS is mutated in ~50–60 % of PDAC.  In this synthetic dataset BRCA1/2
    may be over-represented.  We randomly zero out BRCA1/2 positive entries
    until their mutation rate equals the KRAS rate.
    """
    Xp = X.copy()
    n = len(Xp)
    kras_freq = float(Xp["KRAS"].mean()) if "KRAS" in Xp.columns else 0.5
    rng = np.random.default_rng(99)

    for g in BRCA_GENES:
        if g not in Xp.columns:
            continue
        current_freq = float(Xp[g].mean())
        if current_freq <= kras_freq:
            continue  # already at or below target
        target_count  = int(kras_freq * n)
        current_count = int(Xp[g].sum())
        n_to_zero     = current_count - target_count
        if n_to_zero <= 0:
            continue
        mut_idx  = Xp.index[Xp[g] == 1].tolist()
        drop_idx = rng.choice(mut_idx, size=n_to_zero, replace=False)
        Xp.loc[drop_idx, g] = 0

    return Xp


def perturb_remove(X: pd.DataFrame) -> pd.DataFrame:
    """Drop BRCA1/2 columns entirely."""
    return X.drop(columns=[g for g in BRCA_GENES if g in X.columns])


# ═══════════════════════════════════════════════════════════════════════════════
# HYBRID PIPELINE (condensed, replicates hybrid_pdac_classifier.py logic)
# ═══════════════════════════════════════════════════════════════════════════════

def _build_model() -> LogisticRegression:
    return LogisticRegression(
        penalty="l1", solver="liblinear",
        max_iter=1000, class_weight="balanced",
        random_state=RANDOM_STATE,
    )


def run_hybrid(
    X_raw: pd.DataFrame,
    y: pd.Series,
    top_n: int = TOP_N,
    amplify: float = AMPLIFY,
) -> dict:
    """Run the full hybrid pipeline on a (possibly perturbed) feature matrix.

    Returns a dict with:
        auc          : ROC-AUC on 20 % held-out test set
        effective_coef : DataFrame(feature, effective_coef) sorted desc by |eff|
        ranks        : {gene_name: rank} for all tracked genes
    """
    # 1. Force core genes
    core_present = [g for g in CORE_GENES if g in X_raw.columns]

    # 2. MI-select top N non-core
    non_core_cols = [c for c in X_raw.columns if c not in core_present]
    if non_core_cols:
        mi = mutual_info_classif(X_raw[non_core_cols], y, random_state=RANDOM_STATE)
        mi_order = np.argsort(mi)[::-1]
        selected_nc = [non_core_cols[i] for i in mi_order[:top_n]]
    else:
        selected_nc = []

    # 3. Build hybrid
    final_features = core_present + selected_nc
    X_h = X_raw[final_features].copy()

    # 3b. Amplify core columns
    for g in core_present:
        X_h[g] = X_h[g] * amplify

    # 4. Interaction features (using already-amplified core columns)
    for g1, g2 in INTERACTION_PAIRS:
        col = f"{g1}_{g2}"
        if g1 in X_h.columns and g2 in X_h.columns:
            # interactions on original scale (divide back) so values stay ~0/1
            X_h[col] = (X_raw.get(g1, pd.Series(0, index=X_h.index)) *
                        X_raw.get(g2, pd.Series(0, index=X_h.index))).astype(float)

    # 5. Train
    X_tr, X_te, y_tr, y_te = train_test_split(
        X_h, y, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=y
    )
    model = _build_model()
    model.fit(X_tr, y_tr)
    auc = float(roc_auc_score(y_te, model.predict_proba(X_te)[:, 1]))

    # 6. Effective coefficients
    raw_coef = model.coef_[0]
    eff_coef = [
        c * amplify if f in core_present else c
        for f, c in zip(X_h.columns, raw_coef)
    ]
    coef_df = (
        pd.DataFrame({"feature": X_h.columns, "effective_coef": eff_coef})
        .assign(abs_eff=lambda d: d["effective_coef"].abs())
        .sort_values("abs_eff", ascending=False)
        .drop(columns="abs_eff")
        .reset_index(drop=True)
    )

    # 7. Build rank dict (1-based)
    ranks = {}
    for feat in coef_df["feature"]:
        r = int(coef_df.index[coef_df["feature"] == feat][0]) + 1
        ranks[feat] = r
    # Fill absent genes with n+1 (unranked / not in model)
    all_tracked = CORE_GENES + BRCA_GENES + [f"{g1}_{g2}" for g1, g2 in INTERACTION_PAIRS]
    n_feats = len(X_h.columns)
    for g in all_tracked:
        if g not in ranks:
            ranks[g] = n_feats + 1  # sentinel: absent / not selected

    return {"auc": auc, "coef_df": coef_df, "ranks": ranks,
            "selected_nc": selected_nc, "n_features": n_feats}


# ═══════════════════════════════════════════════════════════════════════════════
# PERMUTATION TEST (per condition)
# ═══════════════════════════════════════════════════════════════════════════════

def permutation_test(
    X: pd.DataFrame,
    y: pd.Series,
    real_auc: float,
    n_perm: int = 200,
    top_n: int = TOP_N,
    amplify: float = AMPLIFY,
) -> dict:
    """Empirical p-value: fraction of permuted AUCs ≥ real_auc."""
    rng = np.random.default_rng(RANDOM_STATE)
    perm_aucs = []
    for i in range(n_perm):
        y_perm = pd.Series(rng.permutation(y.values), index=y.index)
        r = run_hybrid(X, y_perm, top_n=top_n, amplify=amplify)
        perm_aucs.append(r["auc"])
    perm_arr = np.array(perm_aucs)
    return {
        "mean_perm": float(perm_arr.mean()),
        "p_value":   float((perm_arr >= real_auc).mean()),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# DISPLAY HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

TRACKED_GENES = CORE_GENES + BRCA_GENES


def _tag(gene: str) -> str:
    if gene in CORE_GENES:
        return "◀ CORE"
    if gene in BRCA_GENES:
        return "▶ BRCA"
    return ""


def print_condition_summary(label: str, result: dict, perm: dict | None = None) -> None:
    sep = "─" * 62
    print(f"\n  {sep}")
    print(f"  Condition: {label}")
    print(f"  {sep}")
    print(f"  AUC          : {result['auc']:.4f}")
    if perm:
        print(f"  Mean perm AUC: {perm['mean_perm']:.4f}")
        print(f"  p-value      : {perm['p_value']:.4f}  "
              f"({'✓ significant' if perm['p_value'] < 0.05 else '✗ not significant'})")
    print(f"  Non-core selected: {result['selected_nc']}")
    print(f"\n  {'Gene':<16} {'Eff. Coef':>10}  {'Rank':>5}  Tag")
    print(f"  {'─'*48}")
    for _, row in result["coef_df"].iterrows():
        f = row["feature"]
        if f not in TRACKED_GENES and f not in [f"{g1}_{g2}" for g1, g2 in INTERACTION_PAIRS]:
            continue  # skip unlabelled non-core in detail view
        tag = _tag(f)
        print(f"  {f:<16} {row['effective_coef']:>+10.4f}  "
              f"{result['ranks'].get(f, '—'):>5}  {tag}")
    # show non-core non-BRCA too
    shown = set(TRACKED_GENES) | {f"{g1}_{g2}" for g1, g2 in INTERACTION_PAIRS}
    for _, row in result["coef_df"].iterrows():
        f = row["feature"]
        if f in shown:
            continue
        print(f"  {f:<16} {row['effective_coef']:>+10.4f}  "
              f"{result['ranks'].get(f, '—'):>5}  ")


def print_rank_shift_table(conditions: list[str], results: list[dict]) -> None:
    """Show how each tracked gene's rank moves across conditions."""
    tracked = CORE_GENES + BRCA_GENES
    col_w = 12
    header = f"  {'Gene':<14}" + "".join(f"  {c[:col_w]:>{col_w}}" for c in conditions)
    print(header)
    print("  " + "─" * (14 + len(conditions) * (col_w + 2)))
    for gene in tracked:
        tag = _tag(gene)
        row_str = f"  {gene:<10} {tag:<4}"
        for r in results:
            rank = r["ranks"].get(gene, r["n_features"] + 1)
            row_str += f"  {rank:>{col_w}}"
        print(row_str)


def print_summary_table(
    conditions: list[str],
    results: list[dict],
    perms: list[dict | None],
    baseline_auc: float,
) -> None:
    """Compact AUC + gap + p-value summary across all conditions."""
    print(f"\n  {'Condition':<22} {'AUC':>7}  {'Δ vs baseline':>14}  "
          f"{'p-value':>9}  {'Mean perm':>10}")
    print("  " + "─" * 68)
    for cond, res, perm in zip(conditions, results, perms):
        delta = res["auc"] - baseline_auc
        p_str   = f"{perm['p_value']:.4f}" if perm else "—"
        mp_str  = f"{perm['mean_perm']:.4f}" if perm else "—"
        print(f"  {cond:<22} {res['auc']:>7.4f}  {delta:>+14.4f}  "
              f"{p_str:>9}  {mp_str:>10}")


# ═══════════════════════════════════════════════════════════════════════════════
# ROBUSTNESS METRICS
# ═══════════════════════════════════════════════════════════════════════════════

def compute_robustness_metrics(
    conditions: list[str],
    results: list[dict],
    baseline_auc: float,
) -> dict:
    aucs  = [r["auc"] for r in results]
    ranks = {g: [r["ranks"].get(g, r["n_features"] + 1) for r in results]
             for g in TRACKED_GENES}

    mean_auc  = float(np.mean(aucs))
    var_auc   = float(np.var(aucs))
    max_drop  = float(max(baseline_auc - a for a in aucs))

    # Average rank across all conditions
    avg_ranks = {g: float(np.mean(v)) for g, v in ranks.items()}
    # Trend: does rank improve (go lower) as conditions get more restrictive?
    # Conditions are ordered baseline → most perturbed — so we check last vs first rank
    rank_delta = {
        g: ranks[g][-1] - ranks[g][0]  # negative = improved (rose) in last condition
        for g in TRACKED_GENES
    }

    return {
        "mean_auc":   mean_auc,
        "var_auc":    var_auc,
        "max_drop":   max_drop,
        "avg_ranks":  avg_ranks,
        "rank_delta": rank_delta,
        "all_aucs":   aucs,
    }


def evaluate_robustness(metrics: dict, conditions: list[str], results: list[dict]) -> None:
    """Print final robustness verdict."""
    auc_stable    = metrics["max_drop"] < AUC_DROP_THRESHOLD
    # Core genes should rise (rank decreases, lower number = better) as BRCA weakens
    # Compare baseline (cond 0) vs BRCA-removed (last cond)
    core_improve  = all(
        metrics["rank_delta"][g] <= 0 for g in CORE_GENES
    )
    brca_worsen   = all(
        metrics["rank_delta"][g] >= 0 for g in BRCA_GENES
    )

    print("\n  Robustness Metrics")
    print("  " + "─" * 50)
    print(f"  Mean AUC across conditions : {metrics['mean_auc']:.4f}")
    print(f"  AUC variance               : {metrics['var_auc']:.6f}")
    print(f"  Max AUC drop vs baseline   : {metrics['max_drop']:.4f}  "
          f"(threshold < {AUC_DROP_THRESHOLD:.2f})")

    print(f"\n  Average gene ranks (lower = more important):")
    for g in TRACKED_GENES:
        delta_str = f"Δ {metrics['rank_delta'][g]:+d}"
        tag = _tag(g)
        print(f"    {g:<12} avg rank = {metrics['avg_ranks'][g]:5.1f}   "
              f"{delta_str:>8}  ({tag})")

    print(f"\n  AUC stable (drop < {AUC_DROP_THRESHOLD:.2f}) : "
          f"{'✓ YES' if auc_stable else '✗ NO'}")
    print(f"  Core gene ranks improve    : "
          f"{'✓ YES' if core_improve else '✗ NO (partial)'}")
    print(f"  BRCA gene ranks worsen     : "
          f"{'✓ YES (expected)' if brca_worsen else '✗ NO'}")

    print("\n" + "═" * 62)
    if auc_stable and core_improve:
        print("  ✅ Model is biologically robust")
        print("     AUC is stable across BRCA perturbations and core gene")
        print("     coefficients rise consistently as BRCA signal weakens.")
    else:
        print("  ⚠  Model depends heavily on dataset bias")
        if not auc_stable:
            print(f"     AUC drops {metrics['max_drop']:.4f} — exceeds the "
                  f"{AUC_DROP_THRESHOLD:.2f} stability threshold.")
        if not core_improve:
            print("     Core gene ranks do not uniformly improve when BRCA is removed.")
    print("═" * 62)


# ═══════════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════════

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Perturbation robustness test for the hybrid PDAC classifier.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--data", type=Path, default=Path("mutation_matrix.csv"))
    p.add_argument("--top-n", type=int, default=TOP_N)
    p.add_argument("--amplify", type=float, default=AMPLIFY)
    p.add_argument("--n-permutations", type=int, default=200,
                   help="Permutation iterations per condition (0 = skip)")
    return p.parse_args()


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main() -> None:
    args = parse_args()

    SEP = "═" * 62
    print(f"\n{SEP}")
    print("  PDAC HYBRID CLASSIFIER — PERTURBATION ROBUSTNESS TEST")
    print(SEP)
    print(f"  Amplification  : ×{args.amplify:.0f} (core genes)")
    print(f"  Non-core top-N : {args.top_n}")
    print(f"  Permutations   : {args.n_permutations} per condition")

    # ── Load ───────────────────────────────────────────────────────────────
    df = pd.read_csv(args.data)
    y = df["label"].astype(int)
    X = df.drop(columns=["label"]).copy()
    print(f"\n  Dataset : {X.shape[0]} samples × {X.shape[1]} genes")

    # BRCA mutation frequencies (for reference)
    print(f"\n  Baseline mutation frequencies:")
    for g in CORE_GENES + BRCA_GENES:
        if g in X.columns:
            freq = X[g].mean()
            print(f"    {g:<12} {freq:.3f}  ({int(X[g].sum())}/{len(X)} positive)")

    # ── Define perturbations ───────────────────────────────────────────────
    perturbations: list[tuple[str, pd.DataFrame]] = [
        ("A. Baseline",        X.copy()),
        ("B. BRCA ×0.5",       perturb_scale(X, 0.5)),
        ("C. BRCA ×0.25",      perturb_scale(X, 0.25)),
        ("D. Dropout 20 %",    perturb_dropout(X, 0.20, seed=7)),
        ("E. Dropout 40 %",    perturb_dropout(X, 0.40, seed=7)),
        ("F. Freq-balanced",   perturb_freq_balance(X)),
        ("G. BRCA removed",    perturb_remove(X)),
    ]

    # ── Run hybrid on each perturbation ───────────────────────────────────
    print(f"\n{SEP}")
    print("  RUNNING HYBRID PIPELINE ON EACH PERTURBATION")
    print(SEP)

    condition_labels: list[str] = []
    all_results:      list[dict] = []
    all_perms:        list[dict | None] = []

    for label, X_pert in perturbations:
        print(f"\n  ▶ {label}")

        result = run_hybrid(X_pert, y, top_n=args.top_n, amplify=args.amplify)
        print(f"    AUC = {result['auc']:.4f}   "
              f"non-core selected: {result['selected_nc']}")

        perm_result: dict | None = None
        if args.n_permutations > 0:
            perm_result = permutation_test(
                X_pert, y, result["auc"],
                n_perm=args.n_permutations,
                top_n=args.top_n,
                amplify=args.amplify,
            )
            print(f"    p-value = {perm_result['p_value']:.4f}   "
                  f"mean perm AUC = {perm_result['mean_perm']:.4f}")

        condition_labels.append(label)
        all_results.append(result)
        all_perms.append(perm_result)

    baseline_auc = all_results[0]["auc"]

    # ── Per-condition detail ───────────────────────────────────────────────
    print(f"\n{SEP}")
    print("  PER-CONDITION COEFFICIENT DETAIL")
    print(SEP)
    for label, result, perm in zip(condition_labels, all_results, all_perms):
        print_condition_summary(label, result, perm)

    # ── Rank shift table ───────────────────────────────────────────────────
    print(f"\n{SEP}")
    print("  GENE RANK SHIFT ACROSS CONDITIONS  (lower rank = more important)")
    print(f"  (numbers are effective-coefficient rank; n+1 = not in model)")
    print(SEP)
    print_rank_shift_table(condition_labels, all_results)

    # ── AUC + permutation summary ──────────────────────────────────────────
    print(f"\n{SEP}")
    print("  AUC & PERMUTATION SUMMARY")
    print(SEP)
    print_summary_table(condition_labels, all_results, all_perms, baseline_auc)

    # ── Robustness metrics & verdict ──────────────────────────────────────
    print(f"\n{SEP}")
    print("  ROBUSTNESS METRICS & VERDICT")
    print(SEP)
    metrics = compute_robustness_metrics(condition_labels, all_results, baseline_auc)
    evaluate_robustness(metrics, condition_labels, all_results)

    print(f"\n{SEP}")
    print("  PERTURBATION ROBUSTNESS TEST COMPLETE")
    print(f"{SEP}\n")


if __name__ == "__main__":
    main()
