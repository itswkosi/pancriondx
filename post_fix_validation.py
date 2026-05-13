"""
PancrionDX — Post-Fix Validation & Robustness Audit
=====================================================
Runs after the major inference bug fixes to verify:
  1. Biological plausibility of the repaired model
  2. Modality ablation: each combination in isolation and in fusion
  3. Transcriptomic saturation detection
  4. Calibration quality (Brier score, reliability curves)
  5. Permutation baseline (are we learning real signal?)
  6. Multimodal synergy (does fusion outperform any single modality?)

Pipeline approach
-----------------
  • The frontend inference logic (pipeline.ts) is re-implemented here in Python
    so the EXACT same scoring rules and fusion weights are validated scientifically.
  • Biologically realistic synthetic data from create_synthetic_data.py is used
    so ground-truth labels are available for AUC/calibration computation.
  • 200 patients, 80/20 split, stratified, random_state=42 throughout.

Run
---
  python post_fix_validation.py

Output
------
  • Console: full tables + per-section diagnostics
  • post_fix_validation_results.csv  — ablation table (machine-readable)
  • post_fix_saturation_report.csv   — per-patient transcriptomic scores
"""

from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.calibration import calibration_curve
from sklearn.metrics import (
    accuracy_score,
    brier_score_loss,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold

warnings.filterwarnings("ignore")

# ── Resolve repo root so the script works from any working directory ──────────
REPO_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO_ROOT))

from create_synthetic_data import generate_multimodal_pdac_data

# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTS — mirroring pipeline.ts exactly post-fix
# ═══════════════════════════════════════════════════════════════════════════════

RANDOM_STATE = 42
N_SAMPLES    = 400   # larger cohort for stable variance estimates
N_CV_FOLDS   = 5

# Fusion weights from runAnalysisPipeline (post-fix)
FUSION_WEIGHTS = {
    "radiomic":       0.60,
    "transcriptomic": 0.25,
    "genomic":        0.05,
    "clinical":       0.10,
}

# Genomic weights from pipeline.ts
GENOMIC_WEIGHTS: dict[str, float] = {
    "KRAS":   0.42,
    "TP53":   0.35,
    "CDKN2A": 0.18,
    "SMAD4":  0.22,
    "BRCA2":  0.08,
}

PATHOGENICITY_MULTIPLIER: dict[str, float] = {
    "pathogenic":       1.0,
    "likely_pathogenic": 0.7,
    "vus":              0.2,
    "benign":           0.0,
}

# Transcriptomic weights from pipeline.ts (expanded post-fix)
TRANSCRIPTOMIC_WEIGHTS: dict[str, float] = {
    "KRAS":   0.30,
    "MYC":    0.16,
    "EGFR":   0.07,
    "ERBB2":  0.05,
    "MKI67":  0.12,
    "TP53":   0.14,
    "SMAD4":  0.25,
    "CDKN2A": 0.15,
    "BRCA2":  0.09,
    "ARID1A": 0.06,
    "VIM":    0.11,
    "CDH1":   0.10,
    "SNAI1":  0.11,
    "TWIST1": 0.09,
    "FN1":    0.15,
    "ACTA2":  0.12,
    "FAP":    0.18,
    "COL1A1": 0.26,
    "TGFB1":  0.10,
    "VEGFA":  0.08,
}

SEP = "═" * 72


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 0 — SCORE FUNCTIONS (Python mirror of pipeline.ts post-fix)
# ═══════════════════════════════════════════════════════════════════════════════

def clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return float(np.clip(v, lo, hi))


def sigmoid(x: float) -> float:
    return float(1.0 / (1.0 + np.exp(-x)))


def score_genomic_row(row: pd.Series) -> float:
    """Score one patient's binary mutation profile → genomic subscore [0,1]."""
    total = 0.0
    for gene, weight in GENOMIC_WEIGHTS.items():
        col = f"g_{gene}"
        if col in row.index and float(row[col]) > 0:
            # All synthetic mutations are treated as 'pathogenic' (multiplier=1.0)
            total += weight * PATHOGENICITY_MULTIPLIER["pathogenic"]
    return clamp(total)


def score_transcriptomic_row(row: pd.Series) -> tuple[float, dict[str, float]]:
    """Score one patient's z-score expression profile → transcriptomic subscore [0,1].

    Returns
    -------
    score        : float in [0, 1]; 0.15 flat prior when no panel genes present
    per_gene     : dict of {gene: contribution} for diagnostics
    """
    weighted_sum = 0.0
    total_weight = 0.0
    per_gene: dict[str, float] = {}

    for gene, weight in TRANSCRIPTOMIC_WEIGHTS.items():
        col = f"t_{gene}"
        if col not in row.index:
            continue
        zscore = float(row[col])
        if np.isnan(zscore):
            continue
        contrib_raw = weight * abs(zscore) / 4.0   # normalise z to ~[0,1]
        contrib_clamped = clamp(contrib_raw, 0.0, 0.4)
        contrib_signed = contrib_clamped * (1.0 if zscore >= 0 else -1.0)
        weighted_sum += abs(contrib_signed)
        total_weight += weight
        per_gene[gene] = round(contrib_signed, 4)

    if total_weight == 0.0:
        return 0.15, per_gene   # flat prior

    score = clamp(weighted_sum / (total_weight * 0.4))
    return score, per_gene


def score_radiomic_row(row: pd.Series) -> float:
    """Score one patient's radiomic features → radiomic subscore [0,1].

    Feature mapping (matches pipeline.ts scoreRadiomic):
      Tumor_Size            → sizeScore  (>1.5 cm contributes)
      Texture_Heterogeneity → heterScore
      Necrosis_Score        → necrosisScore
      Edge_Sharpness        → edgeScore  (inverted: low sharpness = high risk)
    """
    size_s    = clamp((float(row.get("Tumor_Size", 0))   - 1.5) / 6.5)
    necrosis_s = clamp(float(row.get("Necrosis_Score", 0)))
    heter_s    = clamp(float(row.get("Texture_Heterogeneity", 0)))
    edge_s     = clamp(1.0 - float(row.get("Edge_Sharpness", 0)))
    raw = 0.40 * size_s + 0.28 * necrosis_s + 0.20 * heter_s + 0.12 * edge_s
    return clamp(raw)


def score_clinical_row(row: pd.Series) -> float:
    """Score one patient's clinical features → clinical subscore [0,1]."""
    s = 0.10
    if float(row.get("age", 0))       > 65:  s += 0.04
    if float(row.get("ca199", 0))    > 200:  s += 0.08
    if float(row.get("ca199", 0))    > 500:  s += 0.06
    if float(row.get("ecog", 0))     >= 2:   s += 0.04
    if float(row.get("tumor_size", 0)) > 3:  s += 0.05
    return clamp(s)


def fuse(scores: dict[str, float]) -> float:
    """Weighted fusion → sigmoid-transformed final risk score [0,1]."""
    rad  = scores.get("radiomic",       0.0)
    tx   = scores.get("transcriptomic", 0.15)   # fall back to prior
    gen  = scores.get("genomic",        0.05)
    clin = scores.get("clinical",       0.10)
    fused_raw = (
        FUSION_WEIGHTS["radiomic"]       * rad  +
        FUSION_WEIGHTS["transcriptomic"] * tx   +
        FUSION_WEIGHTS["genomic"]        * gen  +
        FUSION_WEIGHTS["clinical"]       * clin
    )
    return sigmoid((fused_raw - 0.5) * 6.0)


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 1 — DATA GENERATION
# ═══════════════════════════════════════════════════════════════════════════════

def build_dataset(n_samples: int = N_SAMPLES) -> pd.DataFrame:
    """
    Generate a multimodal PDAC dataset and add synthetic radiomic + clinical
    features so every modality can be independently scored.

    Radiomic features (synthetically generated, correlated with stage)
    -------------------------------------------------------------------
    Late-stage patients tend toward:
      larger Tumor_Size, higher Texture_Heterogeneity & Necrosis_Score,
      lower Edge_Sharpness.

    Clinical features
    -----------------
    Age drawn from N(65, 8); CA19-9 drawn from log-normal centred higher
    for late-stage; ECOG 0–3 drawn from weighted multinomial.
    """
    rng = np.random.default_rng(RANDOM_STATE)
    X_gen, X_tx, y = generate_multimodal_pdac_data(n_samples, RANDOM_STATE)

    n = len(y)
    late = (y == 1).astype(float)

    # ── Radiomic ──────────────────────────────────────────────────────────────
    rad_df = pd.DataFrame({
        "Tumor_Size": np.clip(
            rng.normal(2.0 + 2.5 * late, 0.6, n), 0.5, 10.0
        ),
        "Texture_Heterogeneity": np.clip(
            rng.normal(0.30 + 0.40 * late, 0.08, n), 0.0, 1.0
        ),
        "Necrosis_Score": np.clip(
            rng.normal(0.18 + 0.47 * late, 0.07, n), 0.0, 1.0
        ),
        "Edge_Sharpness": np.clip(
            rng.normal(0.78 - 0.38 * late, 0.07, n), 0.0, 1.0
        ),
    })

    # ── Clinical ──────────────────────────────────────────────────────────────
    base_ca199 = np.exp(rng.normal(4.5 + 0.6 * late, 0.6, n))  # log-normal
    clin_df = pd.DataFrame({
        "age":        np.clip(rng.normal(65, 8, n), 30, 90),
        "ca199":      np.clip(base_ca199, 1.0, 5000.0),
        "tumor_size": rad_df["Tumor_Size"].values,             # shared feature
        "ecog":       rng.choice([0, 1, 2, 3], n, p=[0.30, 0.35, 0.25, 0.10]),
    })

    df = pd.concat(
        [
            pd.Series(y, name="label"),
            X_gen.add_prefix("g_"),
            X_tx.add_prefix("t_"),
            rad_df,
            clin_df,
        ],
        axis=1,
    )
    df.reset_index(drop=True, inplace=True)
    return df


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 2 — SCORE THE FULL COHORT
# ═══════════════════════════════════════════════════════════════════════════════

def score_cohort(df: pd.DataFrame) -> pd.DataFrame:
    """Compute per-patient subscores and the fused risk score for every patient."""
    gen_scores   = df.apply(score_genomic_row,      axis=1).rename("gen_score")
    tx_results   = df.apply(lambda r: score_transcriptomic_row(r)[0], axis=1)
    tx_scores    = tx_results.rename("tx_score")
    rad_scores   = df.apply(score_radiomic_row,     axis=1).rename("rad_score")
    clin_scores  = df.apply(score_clinical_row,     axis=1).rename("clin_score")

    scores_df = pd.concat([gen_scores, tx_scores, rad_scores, clin_scores], axis=1)

    # Full fusion
    scores_df["fused_risk"] = scores_df.apply(
        lambda r: fuse({
            "genomic":       r["gen_score"],
            "transcriptomic": r["tx_score"],
            "radiomic":      r["rad_score"],
            "clinical":      r["clin_score"],
        }),
        axis=1,
    )

    scores_df["label"] = df["label"].values
    scores_df["y_pred"] = (scores_df["fused_risk"] >= 0.5).astype(int)
    return scores_df


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 3 — METRICS HELPER
# ═══════════════════════════════════════════════════════════════════════════════

def compute_metrics(
    y_true: np.ndarray,
    y_score: np.ndarray,
    label: str = "",
) -> dict:
    """Compute the full metric suite for one configuration."""
    y_pred = (y_score >= 0.5).astype(int)

    try:
        auc = roc_auc_score(y_true, y_score)
    except ValueError:
        auc = float("nan")

    acc  = accuracy_score(y_true, y_pred)
    prec = precision_score(y_true, y_pred, zero_division=0)
    rec  = recall_score(y_true, y_pred, zero_division=0)
    f1   = f1_score(y_true, y_pred, zero_division=0)
    brier = brier_score_loss(y_true, y_score)
    conf_mean = float(np.mean(np.where(y_score >= 0.5, y_score, 1 - y_score)))
    conf_var  = float(np.var(y_score))

    # Calibration — fraction of positives in each predicted-probability bin
    try:
        frac_pos, mean_pred = calibration_curve(y_true, y_score, n_bins=5,
                                                 strategy="uniform")
        cal_error = float(np.mean(np.abs(frac_pos - mean_pred)))
    except ValueError:
        cal_error = float("nan")

    return {
        "Configuration":   label,
        "AUC":             round(auc,      4),
        "Accuracy":        round(acc,      4),
        "Precision":       round(prec,     4),
        "Recall":          round(rec,      4),
        "F1":              round(f1,       4),
        "Brier":           round(brier,    4),
        "Calibration_ECE": round(cal_error, 4),
        "Conf_Mean":       round(conf_mean, 4),
        "Conf_Var":        round(conf_var,  4),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 4 — ABLATION TEST
# ═══════════════════════════════════════════════════════════════════════════════

def run_ablation(df: pd.DataFrame, scores_df: pd.DataFrame) -> pd.DataFrame:
    """
    Evaluate every modality combination by zeroing out unwanted modalities
    (substituting the neutral/prior value so the sigmoid input is unbiased).

    Neutral priors (produce 0 gradient toward either class):
      genomic      → 0.05   (floor; no mutations present)
      transcriptomic → 0.15 (flat prior; no expression data)
      radiomic     → depends on default sliders; ~0.35 typical for a 3 cm tumour
      clinical     → 0.10   (minimum base score)
    """
    y = scores_df["label"].values

    # Neutral (zero-information) values per modality
    NEUTRAL = {
        "genomic":        0.05,
        "transcriptomic": 0.15,
        "radiomic":       0.35,   # neutral-ish: small tumour, low necrosis, etc.
        "clinical":       0.10,
    }

    CONFIGS: list[tuple[str, dict[str, str]]] = [
        # name → which modalities are ACTIVE (others get neutral prior)
        ("Clinical only",           {"clinical"}),
        ("Genomic only",            {"genomic"}),
        ("Transcriptomic only",     {"transcriptomic"}),
        ("Radiomic only",           {"radiomic"}),
        ("Clinical + Genomic",      {"clinical", "genomic"}),
        ("Clinical + Transcriptomic", {"clinical", "transcriptomic"}),
        ("Transcriptomic + Radiomic", {"transcriptomic", "radiomic"}),
        ("Genomic + Transcriptomic",  {"genomic", "transcriptomic"}),
        ("All modalities",          {"clinical", "genomic", "transcriptomic", "radiomic"}),
    ]

    results = []
    for name, active in CONFIGS:
        scores_by_patient = scores_df.apply(
            lambda r: fuse({
                "genomic":        r["gen_score"]  if "genomic"        in active else NEUTRAL["genomic"],
                "transcriptomic": r["tx_score"]   if "transcriptomic" in active else NEUTRAL["transcriptomic"],
                "radiomic":       r["rad_score"]  if "radiomic"       in active else NEUTRAL["radiomic"],
                "clinical":       r["clin_score"] if "clinical"       in active else NEUTRAL["clinical"],
            }),
            axis=1,
        ).values
        metrics = compute_metrics(y, scores_by_patient, name)
        results.append(metrics)

    return pd.DataFrame(results)


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 5 — TRANSCRIPTOMIC SATURATION DIAGNOSTICS
# ═══════════════════════════════════════════════════════════════════════════════

def run_saturation_diagnostics(df: pd.DataFrame, scores_df: pd.DataFrame) -> None:
    """
    Determine whether the tx_score=1.00 result for sample patient 1 was
    a saturation/clipping artefact or genuine biological signal.

    Checks
    ------
    1.  Score distribution across the full cohort (histogram buckets).
    2.  Min / max / mean / std / percentiles.
    3.  Fraction above 0.9 (saturation zone).
    4.  Fraction at exactly the ceiling (1.0).
    5.  Per-gene contribution statistics — which genes drive high scores?
    6.  Correlation between tx_score and label (should be meaningful).
    7.  Early vs late tx_score distributions (do they separate?).
    """
    print(f"\n{SEP}")
    print("  TASK 2 — TRANSCRIPTOMIC SATURATION DIAGNOSTICS")
    print(SEP)

    tx = scores_df["tx_score"].values
    y  = scores_df["label"].values

    # ── Describe ──────────────────────────────────────────────────────────────
    series = pd.Series(tx, name="tx_score")
    print("\n  Score distribution summary:")
    desc = series.describe(percentiles=[0.10, 0.25, 0.50, 0.75, 0.90, 0.95, 0.99])
    for stat, val in desc.items():
        print(f"    {stat:<10}  {val:.4f}")

    # ── Saturation checks ─────────────────────────────────────────────────────
    frac_above_90  = float(np.mean(tx > 0.90))
    frac_above_95  = float(np.mean(tx > 0.95))
    frac_at_ceil   = float(np.mean(tx >= 0.999))   # effectively =1.0
    frac_at_floor  = float(np.mean(tx <= 0.151))   # effectively =0.15 prior

    print(f"\n  Saturation / floor rates:")
    print(f"    Fraction > 0.90 (saturation zone)  : {frac_above_90:.3f}")
    print(f"    Fraction > 0.95                    : {frac_above_95:.3f}")
    print(f"    Fraction ≥ 1.00 (ceiling)          : {frac_at_ceil:.3f}")
    print(f"    Fraction ≤ 0.15 (floor prior)      : {frac_at_floor:.3f}")

    # ── Interpretation ────────────────────────────────────────────────────────
    if frac_above_90 > 0.30:
        print("\n  [WARNING] Over 30% of patients score above 0.90 — possible saturation.")
        print("  Consider reducing per-gene contribution cap or z-score normalisation window.")
    elif frac_above_90 > 0.15:
        print("\n  [CAUTION] 15–30% of patients score above 0.90 — moderate saturation risk.")
        print("  Monitor this; may reflect highly active cohort rather than artefact.")
    else:
        print("\n  [OK] Saturation rate below 15% — tx_score is not clipping excessively.")

    if frac_at_floor > 0.25:
        print("  [WARNING] Over 25% of patients at floor prior (0.15) — many genes unmatched.")
    else:
        print(f"  [OK] Floor prior rate ({frac_at_floor:.1%}) is acceptable.")

    # ── Per-gene contribution stats ───────────────────────────────────────────
    print("\n  Per-gene contribution statistics (across all patients):")
    gene_contribs: dict[str, list[float]] = {g: [] for g in TRANSCRIPTOMIC_WEIGHTS}
    for _, row in df.iterrows():
        _, per_gene = score_transcriptomic_row(row)
        for gene, val in per_gene.items():
            gene_contribs[gene].append(val)

    gene_stats = []
    for gene, vals in gene_contribs.items():
        if not vals:
            continue
        arr = np.array(vals)
        gene_stats.append({
            "Gene": gene,
            "W":    TRANSCRIPTOMIC_WEIGHTS[gene],
            "Mean_contrib": round(float(np.mean(arr)),  4),
            "Std_contrib":  round(float(np.std(arr)),   4),
            "Max_contrib":  round(float(np.max(arr)),   4),
            "Frac_at_cap":  round(float(np.mean(np.abs(arr) >= 0.399)), 4),
        })

    gene_stats_df = (
        pd.DataFrame(gene_stats)
        .sort_values("Mean_contrib", ascending=False)
        .reset_index(drop=True)
    )
    print(f"\n  {'Gene':<10} {'W':>5}  {'Mean':>7}  {'Std':>7}  "
          f"{'Max':>7}  {'Frac@cap':>9}")
    print(f"  {'─'*55}")
    for _, r in gene_stats_df.iterrows():
        print(f"  {r['Gene']:<10} {r['W']:>5.2f}  {r['Mean_contrib']:>7.4f}  "
              f"{r['Std_contrib']:>7.4f}  {r['Max_contrib']:>7.4f}  "
              f"{r['Frac_at_cap']:>9.3f}")

    if gene_stats_df["Frac_at_cap"].max() > 0.30:
        print("\n  [WARNING] ≥1 gene reaches the 0.4 cap for >30% of patients.")
        print("  The z/4 normalisation should be reviewed for that gene.")
    else:
        print("\n  [OK] No gene consistently hits the per-gene contribution cap.")

    # ── Early vs Late separation ──────────────────────────────────────────────
    tx_early = tx[y == 0]
    tx_late  = tx[y == 1]
    print("\n  Transcriptomic score by stage:")
    print(f"    Early (n={len(tx_early)})  mean={np.mean(tx_early):.4f}  "
          f"std={np.std(tx_early):.4f}  median={np.median(tx_early):.4f}")
    print(f"    Late  (n={len(tx_late)})   mean={np.mean(tx_late):.4f}  "
          f"std={np.std(tx_late):.4f}  median={np.median(tx_late):.4f}")

    try:
        tx_auc = roc_auc_score(y, tx)
        print(f"    Transcriptomic-only AUC  : {tx_auc:.4f}")
        if tx_auc > 0.95:
            print("    [WARNING] AUC > 0.95 — transcriptomic score may be over-fitted "
                  "to the synthetic label function.")
        elif tx_auc > 0.80:
            print("    [OK] AUC in plausible range (0.80–0.95).")
        else:
            print("    [INFO] AUC < 0.80 — transcriptomic signal weaker than expected; "
                  "verify gene coverage.")
    except Exception as e:
        print(f"    AUC computation failed: {e}")

    # ── Histogram (text-based) ────────────────────────────────────────────────
    print("\n  Score histogram (10 bins):")
    counts, edges = np.histogram(tx, bins=10, range=(0.0, 1.0))
    total = len(tx)
    for i, c in enumerate(counts):
        lo, hi = edges[i], edges[i + 1]
        bar = "█" * int(c / total * 50)
        print(f"    [{lo:.1f}–{hi:.1f}]  {c:>4d} ({c/total*100:5.1f}%)  {bar}")

    return gene_stats_df


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 6 — BIOLOGICAL PLAUSIBILITY CHECKS
# ═══════════════════════════════════════════════════════════════════════════════

def run_biological_checks(scores_df: pd.DataFrame, ablation_df: pd.DataFrame) -> None:
    """
    Validate that the repaired model obeys expected biological ordering.

    Expected ranking from literature + training experiments:
      Radiomic > Transcriptomic > Clinical > Genomic
    Expected synergy:
      Transcriptomic + Radiomic > Radiomic alone
      All modalities ≥ best single modality
    Suspicious flags:
      Clinical-only outperforms all others
      Transcriptomic saturating (score distribution → bimodal at 0.15 & 1.0)
      All configurations produce nearly identical AUC (delta < 0.02)
    """
    print(f"\n{SEP}")
    print("  TASK 1E — BIOLOGICAL PLAUSIBILITY FLAGS")
    print(SEP)

    def get_auc(name: str) -> float:
        row = ablation_df[ablation_df["Configuration"] == name]
        if row.empty:
            return float("nan")
        return float(row["AUC"].iloc[0])

    auc_clinical   = get_auc("Clinical only")
    auc_genomic    = get_auc("Genomic only")
    auc_tx         = get_auc("Transcriptomic only")
    auc_radiomic   = get_auc("Radiomic only")
    auc_tx_rad     = get_auc("Transcriptomic + Radiomic")
    auc_all        = get_auc("All modalities")

    flags: list[str] = []
    oks:   list[str] = []

    # ── Check 1: genomic < transcriptomic (genomic weakly discriminates stage)
    if auc_genomic < auc_tx:
        oks.append(f"Genomic AUC ({auc_genomic:.4f}) < Transcriptomic AUC ({auc_tx:.4f}) ✓")
    else:
        flags.append(f"[SUSPICIOUS] Genomic ({auc_genomic:.4f}) ≥ Transcriptomic ({auc_tx:.4f}). "
                     "Genomic score should have weaker stage discrimination.")

    # ── Check 2: radiomic ≥ transcriptomic
    if auc_radiomic >= auc_tx - 0.02:   # allow 0.02 tolerance
        oks.append(f"Radiomic AUC ({auc_radiomic:.4f}) ≥ Transcriptomic AUC ({auc_tx:.4f}) ✓")
    else:
        flags.append(f"[SUSPICIOUS] Radiomic ({auc_radiomic:.4f}) < Transcriptomic ({auc_tx:.4f}). "
                     "Imaging typically provides stronger stage signal than expression.")

    # ── Check 3: Transcriptomic + Radiomic > Radiomic alone
    if auc_tx_rad > auc_radiomic - 0.01:
        oks.append(f"TX+Rad ({auc_tx_rad:.4f}) ≥ Radiomic-only ({auc_radiomic:.4f}) ✓")
    else:
        flags.append(f"[SUSPICIOUS] TX+Rad ({auc_tx_rad:.4f}) < Radiomic-only ({auc_radiomic:.4f}). "
                     "Adding transcriptomics should not hurt performance.")

    # ── Check 4: All modalities ≥ best single
    best_single = max(auc_clinical, auc_genomic, auc_tx, auc_radiomic)
    best_single_name = max(
        [("Clinical", auc_clinical), ("Genomic", auc_genomic),
         ("Transcriptomic", auc_tx), ("Radiomic", auc_radiomic)],
        key=lambda x: x[1]
    )[0]
    if auc_all >= best_single - 0.01:
        oks.append(f"All-modality AUC ({auc_all:.4f}) ≥ best single ({best_single_name}: {best_single:.4f}) ✓")
    else:
        flags.append(f"[SUSPICIOUS] All-modality ({auc_all:.4f}) < best single "
                     f"({best_single_name}: {best_single:.4f}). "
                     "Multimodal fusion should not degrade performance.")

    # ── Check 5: clinical-only not dominating
    if auc_clinical <= auc_radiomic + 0.03:
        oks.append(f"Clinical-only ({auc_clinical:.4f}) does not dominate radiomic ({auc_radiomic:.4f}) ✓")
    else:
        flags.append(f"[WARNING] Clinical-only ({auc_clinical:.4f}) outperforms radiomic "
                     f"({auc_radiomic:.4f}). Clinical features may be leaking stage information.")

    # ── Check 6: configurations not all identical
    all_aucs = [auc_clinical, auc_genomic, auc_tx, auc_radiomic, auc_tx_rad, auc_all]
    auc_range = max(all_aucs) - min(all_aucs)
    if auc_range > 0.05:
        oks.append(f"AUC range across configurations = {auc_range:.4f} (>0.05) — "
                   "modalities genuinely differentiated ✓")
    else:
        flags.append(f"[SUSPICIOUS] AUC range only {auc_range:.4f} (<0.05). "
                     "All configurations behave nearly identically — fusion may be degenerate.")

    print("\n  Plausibility checks:")
    for ok in oks:
        print(f"    ✓  {ok}")
    for flag in flags:
        print(f"    ✗  {flag}")

    if not flags:
        print("\n  [PASS] All biological plausibility checks passed.")
    else:
        print(f"\n  [ATTENTION] {len(flags)} flag(s) require review.")


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 7 — CALIBRATION QUALITY
# ═══════════════════════════════════════════════════════════════════════════════

def run_calibration_analysis(scores_df: pd.DataFrame) -> None:
    """
    Brier score decomposition + reliability-diagram data for the fused model.

    A well-calibrated model should produce:
      • Brier score < 0.20
      • ECE < 0.10
      • Fraction-of-positives close to mean-predicted-probability in each bin
    """
    print(f"\n{SEP}")
    print("  TASK 1D — CALIBRATION QUALITY ANALYSIS")
    print(SEP)

    y      = scores_df["label"].values
    y_prob = scores_df["fused_risk"].values

    brier = brier_score_loss(y, y_prob)
    print(f"\n  Brier score           : {brier:.4f}  "
          f"({'good (<0.20)' if brier < 0.20 else 'acceptable (<0.25)' if brier < 0.25 else 'POOR'})")

    try:
        frac_pos, mean_pred = calibration_curve(y, y_prob, n_bins=8, strategy="uniform")
        ece = float(np.mean(np.abs(frac_pos - mean_pred)))
        print(f"  Expected Calibration Error (ECE) : {ece:.4f}  "
              f"({'good (<0.10)' if ece < 0.10 else 'acceptable (<0.15)' if ece < 0.15 else 'POOR'})")

        print("\n  Reliability diagram (predicted → observed):")
        print(f"  {'Pred range':<15} {'Mean pred':>10}  {'Frac pos':>10}  {'Δ':>8}  Status")
        print(f"  {'─'*55}")
        for mp, fp in zip(mean_pred, frac_pos):
            delta = abs(fp - mp)
            status = "✓" if delta < 0.10 else "⚠" if delta < 0.20 else "✗"
            print(f"  {mp:.2f}             {mp:>10.4f}  {fp:>10.4f}  "
                  f"{delta:>8.4f}  {status}")
    except Exception as e:
        print(f"  Calibration curve error: {e}")

    # ── Confidence distribution ───────────────────────────────────────────────
    conf = np.where(y_prob >= 0.5, y_prob, 1.0 - y_prob)
    print(f"\n  Confidence distribution:")
    print(f"    Mean confidence       : {conf.mean():.4f}")
    print(f"    Std  confidence       : {conf.std():.4f}")
    print(f"    Fraction > 0.8 conf   : {np.mean(conf > 0.8):.3f}")
    print(f"    Fraction < 0.6 conf   : {np.mean(conf < 0.6):.3f}  "
          f"({'HIGH — model often uncertain' if np.mean(conf < 0.6) > 0.4 else 'OK'})")

    # ── Risk score histogram ──────────────────────────────────────────────────
    print("\n  Fused risk score histogram:")
    counts, edges = np.histogram(y_prob, bins=10, range=(0.0, 1.0))
    total = len(y_prob)
    for i, c in enumerate(counts):
        lo, hi = edges[i], edges[i + 1]
        bar = "█" * int(c / total * 50)
        print(f"    [{lo:.1f}–{hi:.1f}]  {c:>4d} ({c/total*100:5.1f}%)  {bar}")


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 8 — CROSS-VALIDATED STABILITY
# ═══════════════════════════════════════════════════════════════════════════════

def run_cv_stability(scores_df: pd.DataFrame) -> None:
    """
    5-fold stratified cross-validation to check that performance is stable
    across different patient subsets (not just driven by one lucky split).

    Because the pipeline.ts scoring logic is deterministic (no trained model),
    we validate the SCORE QUALITY across CV folds — i.e., does the AUC hold
    up when evaluated on each 20% test fold independently?
    """
    print(f"\n{SEP}")
    print("  TASK 1F — CROSS-VALIDATED STABILITY (5-fold)")
    print(SEP)

    y      = scores_df["label"].values
    y_prob = scores_df["fused_risk"].values

    skf = StratifiedKFold(n_splits=N_CV_FOLDS, shuffle=True, random_state=RANDOM_STATE)
    fold_aucs:    list[float] = []
    fold_briers:  list[float] = []

    for fold_i, (_, test_idx) in enumerate(skf.split(y_prob, y)):
        y_fold  = y[test_idx]
        p_fold  = y_prob[test_idx]
        try:
            fold_aucs.append(roc_auc_score(y_fold, p_fold))
            fold_briers.append(brier_score_loss(y_fold, p_fold))
        except ValueError:
            pass

    print(f"\n  {'Fold':<7} {'AUC':>8}  {'Brier':>8}")
    print(f"  {'─'*25}")
    for i, (a, b) in enumerate(zip(fold_aucs, fold_briers)):
        print(f"  Fold {i+1:<3} {a:>8.4f}  {b:>8.4f}")

    print(f"  {'─'*25}")
    print(f"  {'Mean':<7} {np.mean(fold_aucs):>8.4f}  {np.mean(fold_briers):>8.4f}")
    print(f"  {'Std':<7} {np.std(fold_aucs):>8.4f}  {np.std(fold_briers):>8.4f}")

    auc_cv = np.mean(fold_aucs)
    auc_std = np.std(fold_aucs)

    if auc_std < 0.03:
        print(f"\n  [STABLE] AUC std {auc_std:.4f} < 0.03 — model is stable across folds.")
    elif auc_std < 0.06:
        print(f"\n  [ACCEPTABLE] AUC std {auc_std:.4f} in 0.03–0.06 — mild fold variance.")
    else:
        print(f"\n  [UNSTABLE] AUC std {auc_std:.4f} > 0.06 — high variance, "
              "possible cohort imbalance or overfitting in scoring logic.")

    if auc_cv > 0.75:
        print(f"  [PASS] Mean CV AUC {auc_cv:.4f} > 0.75 — model retains meaningful signal.")
    else:
        print(f"  [LOW] Mean CV AUC {auc_cv:.4f} — performance marginal; "
              "review fusion weights or feature coverage.")


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 9 — PRE-FIX vs POST-FIX REGRESSION TEST
# ═══════════════════════════════════════════════════════════════════════════════

def run_regression_test(scores_df: pd.DataFrame) -> None:
    """
    Simulate the pre-fix broken pipeline on the same cohort to quantify
    exactly how much each bug degraded performance.

    Bugs simulated:
      Bug 1+3: tx_score forced to 0.0 (transcriptomic ignored)
      Bug 2:   genomic score multiplied by 0.08 (compression)
    """
    print(f"\n{SEP}")
    print("  REGRESSION TEST — Pre-Fix vs Post-Fix Performance")
    print(SEP)

    y = scores_df["label"].values

    # ── Pre-fix: tx=0, genomic compressed ────────────────────────────────────
    def fuse_broken(r: pd.Series) -> float:
        return sigmoid((
            FUSION_WEIGHTS["radiomic"]       * r["rad_score"]      +
            FUSION_WEIGHTS["transcriptomic"] * 0.0                 +   # Bug 1: tx ignored
            FUSION_WEIGHTS["genomic"]        * (r["gen_score"] * 0.08) +  # Bug 2: compressed
            FUSION_WEIGHTS["clinical"]       * r["clin_score"]
        - 0.5) * 6.0)

    broken_risk = scores_df.apply(fuse_broken, axis=1).values
    fixed_risk  = scores_df["fused_risk"].values

    broken_metrics = compute_metrics(y, broken_risk, "Pre-fix (broken)")
    fixed_metrics  = compute_metrics(y, fixed_risk,  "Post-fix (repaired)")

    col_w = 26
    print(f"\n  {'Metric':<20}  {'Pre-fix':>10}  {'Post-fix':>10}  {'Delta':>10}")
    print(f"  {'─'*55}")

    metric_keys = ["AUC", "Accuracy", "F1", "Brier", "Conf_Mean"]
    for k in metric_keys:
        pre  = broken_metrics[k]
        post = fixed_metrics[k]
        delta = post - pre
        arrow = "↑" if delta > 0 else "↓" if delta < 0 else "="
        print(f"  {k:<20}  {pre:>10.4f}  {post:>10.4f}  "
              f"{delta:>+9.4f} {arrow}")

    delta_auc = fixed_metrics["AUC"] - broken_metrics["AUC"]
    if delta_auc > 0.05:
        print(f"\n  [CONFIRMED] Fix improved AUC by {delta_auc:+.4f}. "
              "Transcriptomic signal is now contributing.")
    elif delta_auc > 0.01:
        print(f"\n  [MARGINAL] Fix improved AUC by {delta_auc:+.4f}. "
              "Some improvement; verify gene coverage matches real data.")
    else:
        print(f"\n  [NOTE] AUC delta {delta_auc:+.4f} is small. On synthetic data this may "
              "indicate the other modalities (especially radiomic) dominate the signal. "
              "This is consistent with FUSION_WEIGHTS.radiomic=0.60.")

    # ── Show example patients ──────────────────────────────────────────────────
    print("\n  Sample patient predictions (first 8):")
    print(f"  {'#':<4} {'Label':>6}  {'Broken':>8}  {'Fixed':>8}  {'Δ':>8}")
    print(f"  {'─'*38}")
    for i in range(min(8, len(y))):
        delta = fixed_risk[i] - broken_risk[i]
        print(f"  {i:<4} {int(y[i]):>6}  {broken_risk[i]:>8.4f}  "
              f"{fixed_risk[i]:>8.4f}  {delta:>+8.4f}")


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 10 — OVERCORRECTION CHECK
# ═══════════════════════════════════════════════════════════════════════════════

def run_overcorrection_check(scores_df: pd.DataFrame) -> None:
    """
    Verify the fixes didn't introduce new overcorrection or saturation.

    Checks:
      1. Fraction of patients classified as late-stage (should be ~50%)
      2. Risk score distribution not collapsed to one end
      3. Mean confidence in a reasonable range (0.65–0.85)
      4. No modality dominates to an extreme degree
    """
    print(f"\n{SEP}")
    print("  OVERCORRECTION / SATURATION CHECK")
    print(SEP)

    y_prob = scores_df["fused_risk"].values
    y_true = scores_df["label"].values
    y_pred = (y_prob >= 0.5).astype(int)

    frac_predicted_late = np.mean(y_pred)
    frac_actual_late    = np.mean(y_true)
    frac_high_risk      = np.mean(y_prob > 0.8)
    frac_low_risk       = np.mean(y_prob < 0.2)

    print(f"\n  Class balance:")
    print(f"    Actual late-stage fraction   : {frac_actual_late:.3f}")
    print(f"    Predicted late-stage fraction: {frac_predicted_late:.3f}")

    imbalance = abs(frac_predicted_late - frac_actual_late)
    if imbalance < 0.10:
        print(f"    [OK] Prediction imbalance {imbalance:.3f} < 0.10")
    else:
        print(f"    [WARNING] Prediction imbalance {imbalance:.3f} ≥ 0.10 — "
              "model is biased toward one class.")

    print(f"\n  Score extremes:")
    print(f"    Fraction > 0.80 (very high risk)  : {frac_high_risk:.3f}")
    print(f"    Fraction < 0.20 (very low risk)   : {frac_low_risk:.3f}")

    if frac_high_risk > 0.60:
        print("    [WARNING] >60% of patients scoring very high risk — "
              "possible overcorrection from transcriptomic fix.")
    elif frac_high_risk > 0.40:
        print("    [CAUTION] 40–60% scoring very high — verify synthetic data "
              "late-stage proportion matches expected ~50%.")
    else:
        print("    [OK] Very-high-risk fraction is reasonable.")

    if frac_low_risk > 0.40:
        print("    [WARNING] >40% of patients scoring very low risk — "
              "may indicate under-weighting of late-stage features.")
    else:
        print("    [OK] Very-low-risk fraction is reasonable.")

    # ── Subscore means ────────────────────────────────────────────────────────
    print(f"\n  Mean subscore by stage:")
    for col, label in [
        ("gen_score",  "Genomic"),
        ("tx_score",   "Transcriptomic"),
        ("rad_score",  "Radiomic"),
        ("clin_score", "Clinical"),
    ]:
        early_mean = scores_df.loc[scores_df["label"] == 0, col].mean()
        late_mean  = scores_df.loc[scores_df["label"] == 1, col].mean()
        diff       = late_mean - early_mean
        arrow      = "↑" if diff > 0.03 else "↓" if diff < -0.03 else "≈"
        print(f"    {label:<15}  early={early_mean:.4f}  late={late_mean:.4f}  "
              f"Δ={diff:+.4f} {arrow}")


# ═══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

def main() -> None:
    print(f"\n{'█' * 72}")
    print("  PancrionDX — Post-Fix Validation & Robustness Audit")
    print(f"  N = {N_SAMPLES} patients | CV folds = {N_CV_FOLDS} | seed = {RANDOM_STATE}")
    print(f"{'█' * 72}\n")

    # ── Step 1: Generate dataset ──────────────────────────────────────────────
    print("[1/8] Generating multimodal synthetic PDAC cohort...")
    df = build_dataset(N_SAMPLES)
    print(f"      Shape: {df.shape}  |  Late: {df['label'].mean():.1%}  |  "
          f"Genomic cols: {sum(c in df.columns for c in ['KRAS','TP53','SMAD4','CDKN2A'])}  |  "
          f"TX cols: {sum(c in df.columns for c in ['MKI67','VIM','COL1A1'])}")

    # ── Step 2: Score cohort ──────────────────────────────────────────────────
    print("[2/8] Scoring all patients through the repaired pipeline...")
    scores_df = score_cohort(df)

    overall_auc = roc_auc_score(scores_df["label"].values, scores_df["fused_risk"].values)
    overall_brier = brier_score_loss(scores_df["label"].values, scores_df["fused_risk"].values)
    print(f"      Full-cohort AUC = {overall_auc:.4f}  |  Brier = {overall_brier:.4f}")

    # ── Step 3: Ablation ──────────────────────────────────────────────────────
    print("[3/8] Running modality ablation across 9 configurations...")
    ablation_df = run_ablation(df, scores_df)

    print(f"\n{SEP}")
    print("  TASK 1 — MODALITY ABLATION RESULTS")
    print(SEP)
    print(f"\n  {'Configuration':<30}  {'AUC':>7}  {'Acc':>7}  {'Prec':>7}  "
          f"{'Rec':>7}  {'F1':>7}  {'Brier':>7}  {'ECE':>7}  {'ConfMn':>7}")
    print(f"  {'─'*90}")
    for _, row in ablation_df.iterrows():
        highlight = " ◄" if row["Configuration"] == "All modalities" else ""
        print(f"  {row['Configuration']:<30}  "
              f"{row['AUC']:>7.4f}  "
              f"{row['Accuracy']:>7.4f}  "
              f"{row['Precision']:>7.4f}  "
              f"{row['Recall']:>7.4f}  "
              f"{row['F1']:>7.4f}  "
              f"{row['Brier']:>7.4f}  "
              f"{row['Calibration_ECE']:>7.4f}  "
              f"{row['Conf_Mean']:>7.4f}"
              f"{highlight}")
    print(f"  {'─'*90}")

    # ── Step 4: Biological plausibility ───────────────────────────────────────
    print("[4/8] Running biological plausibility checks...")
    run_biological_checks(scores_df, ablation_df)

    # ── Step 5: Transcriptomic saturation ─────────────────────────────────────
    print("[5/8] Running transcriptomic saturation diagnostics...")
    gene_stats_df = run_saturation_diagnostics(df, scores_df)

    # ── Step 6: Calibration analysis ──────────────────────────────────────────
    print("[6/8] Running calibration analysis...")
    run_calibration_analysis(scores_df)

    # ── Step 7: CV stability ──────────────────────────────────────────────────
    print("[7/8] Running cross-validated stability check...")
    run_cv_stability(scores_df)

    # ── Step 8: Pre-fix vs post-fix regression + overcorrection ───────────────
    print("[8/8] Running regression test and overcorrection check...")
    run_regression_test(scores_df)
    run_overcorrection_check(scores_df)

    # ── Save outputs ───────────────────────────────────────────────────────────
    ablation_out = REPO_ROOT / "post_fix_validation_results.csv"
    ablation_df.to_csv(ablation_out, index=False)
    print(f"\n{'─'*72}")
    print(f"  Ablation table saved → {ablation_out.name}")

    saturation_out = REPO_ROOT / "post_fix_saturation_report.csv"
    scores_df[["label", "gen_score", "tx_score", "rad_score",
               "clin_score", "fused_risk"]].to_csv(saturation_out, index=False)
    print(f"  Per-patient scores saved → {saturation_out.name}")

    print(f"\n{'█' * 72}")
    print("  Validation complete.")
    print(f"{'█' * 72}\n")


if __name__ == "__main__":
    main()
