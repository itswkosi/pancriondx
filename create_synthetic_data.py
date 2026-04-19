"""
Generate biologically realistic PDAC synthetic datasets for ML model testing.

Module overview
---------------
This module provides two independent but complementary data generators:

1.  generate_pdac_dataset()          — legacy single-modal mutation matrix
    ─────────────────────────────────────────────────────────────────────
    Kept for backward compatibility with bio_aligned_pdac.py and the
    mutation_matrix.csv workflow.  Intentionally reproduces the "biological
    misalignment" problem (BRCA genes dominate ML importances over KRAS/TP53)
    that bio_aligned_pdac.py is designed to expose and correct.

2.  generate_multimodal_pdac_data()  — new biologically realistic generator
    ─────────────────────────────────────────────────────────────────────────
    Returns three aligned objects: X_genomic, X_transcriptomic, y.

    Biological design principles
    ----------------------------
    • Mutation frequencies reflect published PDAC prevalence (KRAS ~90 %,
      TP53 ~70 %, SMAD4 ~50 %, CDKN2A ~40 %, BRCA1/2 ~10 %, ATM ~15 %,
      PALB2 ~10 %).
    • Co-mutation structure: KRAS mutation boosts TP53 co-occurrence;
      BRCA1/2 mutations boost ATM and PALB2 co-occurrence.
    • Labels are probabilistic (derived from mutation burden + driver genes)
      with ~7.5 % random noise so no feature perfectly predicts stage.
    • Transcriptomic expression reflects stage-specific biology:
        – Late: MKI67↑, VIM/SNAI1/TWIST1↑ (EMT), CDH1↓, COL1A1/FAP/FN1↑
    • Cross-modal linkage ties mutations to expression:
        – KRAS → MKI67↑     TP53 → TP53 transcript↑
        – SMAD4 → COL1A1↑ / FN1↑   BRCA1/2 → DNA-repair transcripts↑
    • Patient-level Gaussian noise (σ = 0.3) ensures realistic class overlap.

Labels
------
  0 = early-stage PDAC  (lower grade, fewer accumulated driver mutations)
  1 = late-stage  PDAC  (higher grade, broader mutational landscape)
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

# ── Reproducibility ────────────────────────────────────────────────────────────
RANDOM_STATE: int = 42
N_SAMPLES: int    = 200   # larger cohort → more stable ML evaluation

# ── Per-gene mutation probabilities: (early_rate, late_rate) ──────────────────
#
# Biological design rationale
# ---------------------------
# KRAS:   Near-universal PDAC driver (>90 % of cases). Its mutation is already
#         present in pre-malignant PanIN lesions, so it appears in BOTH early
#         and late patients at high rates. Low fold-change → ML underweights it.
#
# TP53, SMAD4, CDKN2A:  Important but not universal; moderate enrichment in
#         late-stage. Lower fold-change than the DNA-repair genes below.
#
# BRCA1, BRCA2, PALB2:  In this synthetic dataset they are made rare in
#         early-stage but substantially enriched in late-stage (mirroring
#         an aggressive hereditary PDAC subtype). High fold-change → baseline
#         model greedily picks them over the more biologically relevant drivers.
#
# This mismatch (high-fold-change non-core vs low-fold-change core) is exactly
# the problem bio_aligned_pdac.py was written to expose and correct.
#
GENE_MUTATION_RATES: dict[str, tuple[float, float]] = {
    # ── Core PDAC driver genes ─────────────────────────────────────────────────
    # KRAS — near-universal; present in early AND late → fold-change ~1.3×
    "KRAS":   (0.65, 0.85),   # high in both stages       ← ML underweights this
    # TP53 — accumulated in late-stage tumours; fold-change ~1.75×
    "TP53":   (0.40, 0.70),
    # CDKN2A — cell-cycle brake; moderate late-stage enrichment; fold-change ~3×
    "CDKN2A": (0.15, 0.45),
    # SMAD4 — TGF-β tumour suppressor; less frequent but specific; fold-change ~4×
    "SMAD4":  (0.10, 0.40),

    # ── Secondary pathway genes ────────────────────────────────────────────────
    "ARID1A": (0.10, 0.25),   # chromatin remodelling; fold-change ~2.5×
    "TGFBR2": (0.08, 0.20),   # TGF-β receptor; fold-change ~2.5×
    "RNF43":  (0.06, 0.18),   # WNT-pathway tumour suppressor
    "KDM6A":  (0.06, 0.15),   # epigenetic regulator (histone demethylase)
    "PIK3CA": (0.08, 0.22),   # PI3K/AKT oncogene
    "PTEN":   (0.05, 0.20),   # PI3K/AKT tumour suppressor; fold-change ~4×

    # ── DNA-repair genes — HIGH fold-change (the "dominant non-core" problem) ──
    # These are intentionally designed with very low early-stage rates but
    # elevated late-stage rates to simulate the ML misalignment problem.
    # In real sporadic PDAC these rates would be much lower (~5 %).
    "BRCA1":  (0.02, 0.35),   # fold-change ~17×            ← ML overweights this
    "BRCA2":  (0.03, 0.40),   # fold-change ~13×            ← ML overweights this
    "ATM":    (0.10, 0.22),   # moderate enrichment; fold-change ~2.2×
    "PALB2":  (0.02, 0.25),   # fold-change ~12.5×          ← ML overweights this
}


def generate_pdac_dataset(
    n_samples: int = N_SAMPLES,
    random_state: int = RANDOM_STATE,
) -> pd.DataFrame:
    """Generate a synthetic PDAC mutation matrix with biologically motivated rates.

    Genes are loaded from src/data/gene_panel.json to ensure the feature columns
    are aligned with the rest of the PancrionDX pipeline.

    Returns
    -------
    pd.DataFrame
        Columns : 'label' + one binary column per gene (0 = wild-type, 1 = mutated).
        Labels  : 0 = early-stage, 1 = late-stage PDAC.
    """
    rng = np.random.default_rng(random_state)

    # Load gene order from the official panel so the mutation matrix is aligned
    # with train_pdac_classifier.py and full_pdac_experiment.py.
    panel_path  = Path(__file__).parent / "src" / "data" / "gene_panel.json"
    panel       = json.loads(panel_path.read_text())
    panel_genes = [g["gene_symbol"] for g in panel["genes"]]

    # Keep only genes that have defined mutation rates; preserve panel order.
    genes = [g for g in panel_genes if g in GENE_MUTATION_RATES]

    # ── Assign class labels ────────────────────────────────────────────────────
    # ~52 % late-stage (slight majority, mirrors clinical cohort distributions).
    n_late  = int(n_samples * 0.52)
    n_early = n_samples - n_late
    labels  = np.array([0] * n_early + [1] * n_late)

    # ── Generate binary mutation features (0 = WT, 1 = mutated) ───────────────
    rows: list[dict] = []
    for stage in labels:
        row: dict = {}
        for gene in genes:
            early_rate, late_rate = GENE_MUTATION_RATES[gene]
            p = late_rate if stage == 1 else early_rate
            row[gene] = int(rng.binomial(1, p))   # binary: 0 or 1
        rows.append(row)

    df = pd.DataFrame(rows, columns=genes)
    df.insert(0, "label", labels)

    # Shuffle rows to interleave early and late samples.
    df = df.sample(frac=1, random_state=random_state).reset_index(drop=True)
    return df


# ══════════════════════════════════════════════════════════════════════════════
# PART 1–4 : Biologically realistic multi-modal data generation
# ══════════════════════════════════════════════════════════════════════════════

# ── Gene lists ─────────────────────────────────────────────────────────────────
GENOMIC_GENES: list[str] = [
    "KRAS", "TP53", "SMAD4", "CDKN2A",
    "BRCA1", "BRCA2", "ATM", "PALB2",
]

TRANSCRIPTOMIC_PANEL: list[str] = [
    "KRAS",   "TP53",   "SMAD4",  "CDKN2A",
    "BRCA1",  "BRCA2",  "ATM",    "PALB2",
    "MKI67",  "VIM",    "SNAI1",  "TWIST1",
    "CDH1",   "COL1A1", "FAP",    "FN1",
]

# ── Published PDAC marginal mutation probabilities ────────────────────────────
# Pooled-stage baseline probabilities; conditional boosts are applied inside
# generate_genomic_data() to model co-mutation structure.
BASE_MUT_PROBS: dict[str, float] = {
    "KRAS":   0.90,   # near-universal PDAC driver
    "TP53":   0.70,   # accumulated in advanced disease
    "SMAD4":  0.50,   # TGF-β suppressor; correlates with metastasis
    "CDKN2A": 0.40,   # cell-cycle brake
    "BRCA1":  0.10,   # DNA-repair; ~10 % in sporadic PDAC
    "BRCA2":  0.10,   # DNA-repair
    "ATM":    0.15,   # moderate prevalence
    "PALB2":  0.10,   # BRCA2 partner; ~10 %
}


# ── PART 1 ─────────────────────────────────────────────────────────────────────

def generate_genomic_data(
    n_samples: int = 200,
    random_state: int = RANDOM_STATE,
) -> tuple[pd.DataFrame, np.ndarray]:
    """Generate biologically realistic PDAC mutation matrix with co-mutation structure.

    Mutation probabilities reflect published PDAC prevalence.  Co-mutation
    relationships (KRAS → TP53, BRCA1/2 → ATM/PALB2) are modelled as
    conditional probability boosts applied after the independent draw to
    mimic real tumour clonal evolution.

    Label assignment is probabilistic — derived from a continuous score
    that weighs mutation burden plus key driver mutations (TP53, SMAD4).
    An additional ~7.5 % random label noise prevents any feature from
    being a perfect predictor.

    Returns
    -------
    X_genomic : pd.DataFrame  shape (n_samples, 8) — binary mutation columns
    y         : np.ndarray    shape (n_samples,)   — 0 = early, 1 = late
    """
    rng = np.random.default_rng(random_state)

    rows: list[dict[str, int]] = []
    for _ in range(n_samples):
        mut: dict[str, int] = {}

        # ── Step 1: Independent marginal draws ───────────────────────────────
        for gene, p in BASE_MUT_PROBS.items():
            mut[gene] = int(rng.binomial(1, p))

        # ── Step 2: Co-mutation conditional boosts ───────────────────────────
        # KRAS+ → elevated TP53 co-occurrence (~+15 pp conditional boost)
        if mut["KRAS"] == 1 and mut["TP53"] == 0:
            mut["TP53"] = int(rng.binomial(1, 0.15))

        # BRCA1/2+ → elevated ATM and PALB2 co-occurrence
        if mut["BRCA1"] == 1 or mut["BRCA2"] == 1:
            if mut["ATM"] == 0:
                mut["ATM"]   = int(rng.binomial(1, 0.25))
            if mut["PALB2"] == 0:
                mut["PALB2"] = int(rng.binomial(1, 0.20))

        rows.append(mut)

    X_genomic = pd.DataFrame(rows, columns=GENOMIC_GENES)

    # ── Step 3: Probabilistic label assignment ────────────────────────────────
    # Continuous score [0, ~0.55]; no single gene is deterministic.
    burden = X_genomic.sum(axis=1)
    late_score = (
        0.20 * X_genomic["TP53"]          +   # strong stage driver
        0.20 * X_genomic["SMAD4"]         +   # metastasis correlate
        0.10 * X_genomic["KRAS"]          +   # near-universal but contributes
        0.05 * X_genomic["CDKN2A"]        +   # cell-cycle progression
        0.10 * (burden / burden.max())         # total mutation burden
    )
    # Map to probability in [0.20, 0.80] — prevents floor/ceiling determinism
    max_score = late_score.max() if late_score.max() > 0 else 1.0
    late_prob  = 0.20 + 0.60 * (late_score / max_score)
    y = np.array([int(rng.binomial(1, p)) for p in late_prob], dtype=int)

    # ── Step 4: Label noise (~7.5 % flip rate) ────────────────────────────────
    noise_mask = rng.random(n_samples) < 0.075
    y[noise_mask] = 1 - y[noise_mask]

    return X_genomic, y


# ── PARTS 2 & 3 ────────────────────────────────────────────────────────────────

def generate_transcriptomic_data(
    X_genomic: pd.DataFrame,
    y: np.ndarray,
    random_state: int = RANDOM_STATE,
) -> pd.DataFrame:
    """Generate biologically realistic transcriptomic expression data.

    Expression values are continuous (z-score-like).  Two sources of signal
    are layered additively so that no single effect is deterministic:

    Stage-level shifts (PART 2)
    ---------------------------
    Late-stage tumours receive mean-shifted expression for markers of:
      • Proliferation : MKI67  (+1.2)
      • EMT           : VIM, SNAI1, TWIST1  (+0.9 each)
      • Loss of epithelial identity : CDH1  (−0.8)
      • Stromal activation : COL1A1, FAP, FN1  (+1.0 each)
    Base std = 1.0 ensures early/late distributions overlap realistically.

    Cross-modal linkage (PART 3)
    ----------------------------
    Mutation status additively shifts expression:
      KRAS+   → MKI67 ↑ (+0.5)
      TP53+   → TP53 transcript ↑ (+0.4, mutant-p53 accumulation)
      SMAD4+  → COL1A1 ↑ (+0.5), FN1 ↑ (+0.4)
      BRCA1/2+ → BRCA1, BRCA2, ATM transcripts ↑ (+0.3 each)

    Patient-level noise N(0, 0.3) is added last to all genes.

    Parameters
    ----------
    X_genomic : pd.DataFrame  Binary mutation matrix (from generate_genomic_data).
    y         : np.ndarray    Stage labels (0 = early, 1 = late).

    Returns
    -------
    X_transcriptomic : pd.DataFrame  shape (n_samples, 16) — continuous expression
    """
    rng = np.random.default_rng(random_state)
    n   = len(y)
    late = (y == 1).astype(float)   # 1.0 for late-stage, 0.0 for early

    # ── Base expression: early ~ N(0, 1), late ~ N(0.75, 1) ──────────────────
    base_mean = 0.75 * late                      # per-patient scalar
    expr: dict[str, np.ndarray] = {
        gene: base_mean + rng.normal(0.0, 1.0, n)
        for gene in TRANSCRIPTOMIC_PANEL
    }

    # ── Stage-level biological shifts ─────────────────────────────────────────
    # Proliferation marker
    expr["MKI67"]  += late * rng.normal(1.2, 0.3, n)

    # EMT markers ↑
    for emt_gene in ("VIM", "SNAI1", "TWIST1"):
        expr[emt_gene] += late * rng.normal(0.9, 0.3, n)

    # Epithelial marker ↓ (loss of CDH1 hallmarks EMT)
    expr["CDH1"]   -= late * rng.normal(0.8, 0.3, n)

    # Stromal activation ↑
    for stromal in ("COL1A1", "FAP", "FN1"):
        expr[stromal]  += late * rng.normal(1.0, 0.3, n)

    # ── Cross-modal linkage: mutations → expression ───────────────────────────
    kras_mut  = X_genomic["KRAS"].values.astype(float)
    tp53_mut  = X_genomic["TP53"].values.astype(float)
    smad4_mut = X_genomic["SMAD4"].values.astype(float)
    brca_mut  = np.clip(
        X_genomic["BRCA1"].values + X_genomic["BRCA2"].values, 0, 1
    ).astype(float)

    # KRAS mutation → oncogenic proliferation signal → MKI67 ↑
    expr["MKI67"]  += kras_mut  * rng.normal(0.50, 0.20, n)

    # TP53 mutation → mutant-p53 protein accumulation → TP53 transcript ↑
    expr["TP53"]   += tp53_mut  * rng.normal(0.40, 0.15, n)

    # SMAD4 loss → dysregulated TGF-β signalling → COL1A1 ↑, FN1 ↑
    expr["COL1A1"] += smad4_mut * rng.normal(0.50, 0.20, n)
    expr["FN1"]    += smad4_mut * rng.normal(0.40, 0.20, n)

    # BRCA1/2 mutation → DNA-damage response transcript upregulation
    expr["BRCA1"]  += brca_mut  * rng.normal(0.30, 0.15, n)
    expr["BRCA2"]  += brca_mut  * rng.normal(0.30, 0.15, n)
    expr["ATM"]    += brca_mut  * rng.normal(0.25, 0.15, n)

    # ── Patient-level global noise ─────────────────────────────────────────────
    for gene in TRANSCRIPTOMIC_PANEL:
        expr[gene] += rng.normal(0.0, 0.3, n)

    return pd.DataFrame(expr, columns=TRANSCRIPTOMIC_PANEL)


# ── PART 4 : Public multi-modal entry-point ────────────────────────────────────

def generate_multimodal_pdac_data(
    n_samples: int = 200,
    random_state: int = RANDOM_STATE,
) -> tuple[pd.DataFrame, pd.DataFrame, np.ndarray]:
    """Generate fully aligned genomic + transcriptomic PDAC datasets.

    Calls generate_genomic_data then generate_transcriptomic_data, ensuring
    both DataFrames and the label vector share the same patient index.

    Returns
    -------
    X_genomic        : pd.DataFrame  shape (n_samples, 8)  — binary mutations
    X_transcriptomic : pd.DataFrame  shape (n_samples, 16) — expression values
    y                : np.ndarray    shape (n_samples,)    — 0=early, 1=late
    """
    X_genomic, y         = generate_genomic_data(n_samples, random_state)
    X_transcriptomic     = generate_transcriptomic_data(X_genomic, y, random_state)
    return X_genomic, X_transcriptomic, y


# ── PART 5 : Sanity checks ─────────────────────────────────────────────────────

def run_sanity_checks(
    X_genomic: pd.DataFrame,
    X_transcriptomic: pd.DataFrame,
    y: np.ndarray,
) -> None:
    """Validate the generated dataset against biological expectations.

    Checks
    ------
    1. Observed mutation frequencies vs. expected PDAC prevalence (±0.15 tol.)
    2. Mean expression per class for each transcriptomic gene.
    3. Confirm no feature achieves perfect class separation (distributions
       must overlap).
    """
    _SEP = "═" * 62

    # ── Check 1: Mutation frequencies ─────────────────────────────────────────
    print(f"\n{_SEP}")
    print("  SANITY CHECK 1 — Genomic Mutation Frequencies")
    print(_SEP)
    expected_freq = {
        "KRAS": 0.90, "TP53": 0.70, "SMAD4": 0.50, "CDKN2A": 0.40,
        "BRCA1": 0.10, "BRCA2": 0.10, "ATM": 0.15, "PALB2": 0.10,
    }
    print(f"  {'Gene':<10}  {'Observed':>8}  {'Expected':>9}  Status")
    print(f"  {'─' * 46}")
    for gene in GENOMIC_GENES:
        obs  = X_genomic[gene].mean()
        exp  = expected_freq[gene]
        ok   = "✓" if abs(obs - exp) < 0.15 else "⚠  out of expected range"
        print(f"  {gene:<10}  {obs:>8.3f}  {exp:>9.3f}  {ok}")
    n0, n1 = int((y == 0).sum()), int((y == 1).sum())
    print(f"\n  Label balance → early(0) = {n0}   late(1) = {n1}   "
          f"late% = {n1 / len(y):.1%}")

    # ── Check 2: Expression by stage ──────────────────────────────────────────
    print(f"\n{_SEP}")
    print("  SANITY CHECK 2 — Mean Expression by Stage (Early vs Late)")
    print(_SEP)
    print(f"  {'Gene':<12}  {'Early μ':>9}  {'Late μ':>8}  {'Δ (late−early)':>15}")
    print(f"  {'─' * 52}")
    for gene in TRANSCRIPTOMIC_PANEL:
        e_mu = X_transcriptomic.loc[y == 0, gene].mean()
        l_mu = X_transcriptomic.loc[y == 1, gene].mean()
        delta = l_mu - e_mu
        direction = "↑" if delta > 0.1 else ("↓" if delta < -0.1 else "~")
        print(f"  {gene:<12}  {e_mu:>9.3f}  {l_mu:>8.3f}  "
              f"{delta:>+9.3f}  {direction}")

    # ── Check 3: No perfect separation ────────────────────────────────────────
    print(f"\n{_SEP}")
    print("  SANITY CHECK 3 — Feature Separation (no perfect predictor allowed)")
    print(_SEP)
    all_X   = pd.concat([X_genomic, X_transcriptomic], axis=1)
    early_idx = (y == 0)
    late_idx  = (y == 1)
    perfect = []
    for col in all_X.columns:
        e_vals = all_X[col].values[early_idx]
        l_vals = all_X[col].values[late_idx]
        if len(e_vals) > 0 and len(l_vals) > 0:
            if e_vals.max() < l_vals.min() or l_vals.max() < e_vals.min():
                perfect.append(col)
    if perfect:
        print(f"  ⚠  Perfectly separating features: {perfect}")
    else:
        print("  ✓  No feature has perfect class separation — "
              "distributions overlap realistically.")
    print(f"{_SEP}\n")


if __name__ == "__main__":
    # ── Legacy: regenerate mutation_matrix.csv (used by bio_aligned_pdac.py) ──
    df          = generate_pdac_dataset()
    output_path = Path("mutation_matrix.csv")
    df.to_csv(output_path, index=False)

    dist = df["label"].value_counts().sort_index()
    print(f"✓ PDAC mutation matrix created: {output_path}")
    print(f"  Samples  : {len(df)}")
    print(f"  Features : {df.shape[1] - 1}  {list(df.columns[1:])}")
    print(f"  Labels   : early(0) = {int(dist.get(0, 0))},  "
          f"late(1) = {int(dist.get(1, 0))}")

    print("\n  Observed mutation rates by stage:")
    print(f"  {'Gene':<12}  {'early':>6}  {'late':>6}  {'fold-change':>12}")
    print(f"  {'─' * 42}")
    for gene in df.columns[1:]:
        e_rate = df[df["label"] == 0][gene].mean()
        l_rate = df[df["label"] == 1][gene].mean()
        fold   = l_rate / e_rate if e_rate > 0 else float("inf")
        marker = "  ← ML overweights" if gene in ("BRCA1", "BRCA2", "PALB2") else ""
        marker = "  ← underweighted"  if gene == "KRAS" else marker
        print(f"  {gene:<12}  {e_rate:>6.2f}  {l_rate:>6.2f}  "
              f"{fold:>10.1f}×{marker}")

    # ── New: biologically realistic multi-modal dataset ───────────────────────
    print("\n" + "═" * 62)
    print("  BIOLOGICALLY REALISTIC MULTI-MODAL DATASET GENERATION")
    print("═" * 62)
    X_gen, X_trx, y_mm = generate_multimodal_pdac_data(n_samples=200)
    print(f"  ✓ X_genomic        : {X_gen.shape}  (binary mutation matrix)")
    print(f"  ✓ X_transcriptomic : {X_trx.shape}  (continuous expression)")
    print(f"  ✓ y                : {y_mm.shape}  (0=early, 1=late)")
    run_sanity_checks(X_gen, X_trx, y_mm)
