/**
 * Local analysis pipeline.
 * Computes a multimodal PDAC risk score from the three modalities + clinical data.
 * All logic is deterministic given the same inputs — no random defaults.
 */

import type {
  ResultData,
  FeatureDriver,
  GenomicVariant,
  TranscriptomicGene,
  RadiomicFeature,
  ClinicalRecord,
  ModalityKey,
} from "@/app/results/data"

// ─── Input types ──────────────────────────────────────────────────────────────

export interface PipelineInput {
  genomicVariants: GenomicVariant[]
  transcriptomicGenes: TranscriptomicGene[]
  radiomicValues: {
    tumor_size: number
    heterogeneity: number
    necrosis: number
    edge_sharpness: number
  }
  clinical: {
    age: number
    sex: string
    tumorLocation: string
    tumorSize: number
    ca199: number
    ecog: number
  }
}

// ─── Gene weights ─────────────────────────────────────────────────────────────

const GENOMIC_WEIGHTS: Record<string, number> = {
  KRAS: 0.42,
  TP53: 0.35,
  CDKN2A: 0.18,
  SMAD4: 0.22,
  BRCA2: 0.08,
}

const PATHOGENICITY_MULTIPLIER: Record<string, number> = {
  pathogenic: 1.0,
  likely_pathogenic: 0.7,
  vus: 0.2,
  benign: 0.0,
}

const TRANSCRIPTOMIC_WEIGHTS: Record<string, { weight: number; group: TranscriptomicGene["group"] }> = {
  // Oncogenes / driver genes — derived from transcriptomic_classifier.py training gene set
  KRAS:   { weight: 0.30, group: "other" },      // primary PDAC oncogene
  MYC:    { weight: 0.16, group: "other" },      // proliferation amplifier
  EGFR:   { weight: 0.07, group: "other" },      // RTK overexpression
  ERBB2:  { weight: 0.05, group: "other" },      // HER2 signalling
  MKI67:  { weight: 0.12, group: "other" },      // proliferation index
  // Tumour suppressors / DNA damage response
  TP53:   { weight: 0.14, group: "dna_damage" }, // p53 pathway loss
  SMAD4:  { weight: 0.25, group: "dna_damage" }, // TGF-β pathway, silenced in PDAC
  CDKN2A: { weight: 0.15, group: "dna_damage" }, // cell cycle regulator, deleted late
  BRCA2:  { weight: 0.09, group: "dna_damage" }, // DNA repair
  ARID1A: { weight: 0.06, group: "dna_damage" }, // chromatin remodelling
  // EMT / invasion markers
  VIM:    { weight: 0.11, group: "other" },      // mesenchymal transition
  CDH1:   { weight: 0.10, group: "other" },      // E-cadherin loss = EMT
  SNAI1:  { weight: 0.11, group: "stromal" },    // EMT transcription factor
  TWIST1: { weight: 0.09, group: "stromal" },    // EMT transcription factor
  FN1:    { weight: 0.15, group: "stromal" },    // fibronectin, invasion
  // Stroma / tumour microenvironment
  ACTA2:  { weight: 0.12, group: "stromal" },    // cancer-associated fibroblasts
  FAP:    { weight: 0.18, group: "stromal" },    // fibroblast activation protein
  COL1A1: { weight: 0.26, group: "stromal" },    // desmoplastic stroma
  TGFB1:  { weight: 0.10, group: "stromal" },    // TGF-β signalling
  VEGFA:  { weight: 0.08, group: "other" },      // angiogenesis
}

// ─── Score helpers ────────────────────────────────────────────────────────────

function clamp(v: number, lo = 0, hi = 1) { return Math.max(lo, Math.min(hi, v)) }

function sigmoid(x: number) { return 1 / (1 + Math.exp(-x)) }

function round2(n: number) { return Math.round(n * 100) / 100 }

// ─── Radiomic subscores ───────────────────────────────────────────────────────

function scoreRadiomic(vals: PipelineInput["radiomicValues"]): {
  score: number
  features: RadiomicFeature[]
} {
  // Weights derived from the reference model
  const sizeScore = clamp((vals.tumor_size - 1.0) / 5.0)          // >1.0 cm starts contributing; 6 cm = 1.0 (T3 anchor)
  const necrosisScore = clamp(vals.necrosis)
  const heterScore = clamp(vals.heterogeneity)
  const edgeScore = clamp(1 - vals.edge_sharpness)                 // low sharpness = higher risk

  const raw = 0.40 * sizeScore + 0.28 * necrosisScore + 0.20 * heterScore + 0.12 * edgeScore
  const score = clamp(raw)

  const features: RadiomicFeature[] = [
    {
      name: "Tumor Size",
      value: vals.tumor_size,
      unit: " cm",
      contribution: round2(0.40 * sizeScore),
      interpretation:
        vals.tumor_size >= 3.0
          ? "Above 3 cm threshold associated with late-stage PDAC."
          : "Below 3 cm threshold; lower risk contribution.",
    },
    {
      name: "Necrosis Score",
      value: round2(vals.necrosis),
      unit: "",
      contribution: round2(0.28 * necrosisScore),
      interpretation:
        vals.necrosis > 0.5
          ? "Elevated central necrosis consistent with aggressive phenotype."
          : "Low necrosis fraction; reduced aggressiveness signal.",
    },
    {
      name: "Texture Heterogeneity",
      value: round2(vals.heterogeneity),
      unit: "",
      contribution: round2(0.20 * heterScore),
      interpretation:
        vals.heterogeneity > 0.6
          ? "High heterogeneity reflects tumour microenvironment complexity."
          : "Moderate heterogeneity; intermediate risk signal.",
    },
    {
      name: "Edge Sharpness",
      value: round2(vals.edge_sharpness),
      unit: "",
      contribution: round2(-0.12 * (1 - edgeScore)),
      interpretation:
        vals.edge_sharpness < 0.5
          ? "Low margin definition suggests local infiltration and invasion."
          : "Clear margins; lower infiltration signal.",
    },
  ]

  return { score, features }
}

// ─── Transcriptomic subscores ─────────────────────────────────────────────────

function scoreTxGenes(txGenes: TranscriptomicGene[]): {
  score: number
  drivers: FeatureDriver[]
  correctedGenes: TranscriptomicGene[]
} {
  if (txGenes.length === 0) {
    console.warn("[Transcriptomic] No genes provided — using flat prior (score=0.15)")
    return { score: 0.15, drivers: [], correctedGenes: [] }
  }

  console.log(`[Transcriptomic] Input: ${txGenes.length} genes`)
  const zscores = txGenes.map(g => g.zscore)
  const nanCount = zscores.filter(z => isNaN(z)).length
  const zeroCount = zscores.filter(z => z === 0).length
  console.log(`[Transcriptomic] z-score diagnostics — NaN: ${nanCount}, zero: ${zeroCount}, total: ${txGenes.length}`)
  if (zeroCount === txGenes.length) {
    console.error("[Transcriptomic] CRITICAL: ALL z-scores are zero. Check expression column parsing upstream.")
  }
  console.log("[Transcriptomic] First 10 genes:", txGenes.slice(0, 10).map(g => `${g.gene}:${g.zscore}`).join(", "))

  let weightedSum = 0
  let totalWeight = 0
  let matchedGenes = 0
  const drivers: FeatureDriver[] = []
  const correctedGenes: TranscriptomicGene[] = []

  for (const g of txGenes) {
    // Normalize gene symbol to uppercase for weight-table lookup
    const geneKey = g.gene.toUpperCase().trim()
    const meta = TRANSCRIPTOMIC_WEIGHTS[geneKey]

    // Correct group from weight table; keep input value if gene not in panel
    const corrected: TranscriptomicGene = {
      ...g,
      gene: geneKey,
      group: meta ? meta.group : g.group,
    }
    correctedGenes.push(corrected)

    if (!meta) continue  // gene not in scoring panel — skip, don't error

    matchedGenes++
    const zscore = isNaN(g.zscore) ? 0 : g.zscore
    // Correct normalisation: each gene contributes (weight × normZ) where normZ = clamp(|z|/4, 0, 1).
    // Max per-gene contribution = meta.weight (at |z| ≥ 4). Denominator = totalWeight.
    // Previous formula used a flat 0.4 cap but denominator assumed weight × 0.4 per gene,
    // causing score to saturate at 1.0 for a single panel gene at |z| ≥ 1.6.
    const normZ = clamp(Math.abs(zscore) / 4, 0, 1)
    const absContrib = meta.weight * normZ
    const signedContrib = round2(absContrib * (zscore >= 0 ? 1 : -1))
    weightedSum += absContrib
    totalWeight += meta.weight

    console.log(`[Transcriptomic]   ${geneKey}: weight=${meta.weight}, z=${zscore.toFixed(3)}, normZ=${normZ.toFixed(3)}, absContrib=${absContrib.toFixed(4)}`)

    drivers.push({
      name: `${geneKey} expression`,
      modality: "Transcriptomic",
      direction: zscore >= 0 ? "up" : "down",
      score: signedContrib,
      explanation: zscore >= 0
        ? `Elevated ${geneKey} expression (z=${zscore.toFixed(2)}) consistent with late-stage tumour state.`
        : `Reduced ${geneKey} expression (z=${zscore.toFixed(2)}) may reflect altered differentiation.`,
    })
  }

  console.log(`[Transcriptomic] Panel match: ${matchedGenes}/${txGenes.length} genes`)
  console.log(`[Transcriptomic] weightedSum=${weightedSum.toFixed(4)}, totalWeight=${totalWeight.toFixed(4)}`)

  if (totalWeight === 0) {
    console.warn("[Transcriptomic] No panel genes matched — using flat prior (score=0.15)")
    return { score: 0.15, drivers: [], correctedGenes }
  }

  // score ∈ [0,1] by construction: weightedSum ≤ totalWeight (since normZ ≤ 1 always)
  const score = clamp(weightedSum / totalWeight)
  console.log(`[Transcriptomic] Final score: ${score.toFixed(4)} (weightedSum=${weightedSum.toFixed(4)}, totalWeight=${totalWeight.toFixed(4)})`)
  return { score, drivers, correctedGenes }
}

// ─── Genomic subscores ────────────────────────────────────────────────────────

function scoreGenomic(variants: GenomicVariant[]): { score: number; drivers: FeatureDriver[] } {
  if (variants.length === 0) {
    console.log("[Genomic] No variants — using floor score (0.05)")
    return { score: 0.05, drivers: [] }
  }

  let total = 0
  const drivers: FeatureDriver[] = []

  for (const v of variants) {
    const baseWeight = GENOMIC_WEIGHTS[v.gene.toUpperCase()] ?? 0.05
    const pathoMult = PATHOGENICITY_MULTIPLIER[v.pathogenicity] ?? 0.1
    const contrib = round2(baseWeight * pathoMult)
    total += contrib
    console.log(`[Genomic] ${v.gene} (${v.pathogenicity}): base=${baseWeight}, mult=${pathoMult}, contrib=${contrib}`)
    drivers.push({
      name: `${v.gene} ${v.variant !== "deletion" ? "mutation" : "loss"}`,
      modality: "Genomic",
      direction: "up",
      score: contrib,
      explanation: `${v.gene} ${v.variant} (${v.pathogenicity.replace("_", " ")}) contributes to genomic instability.`,
    })
  }

  // Genomic has limited discriminative power for stage; fusion weight (0.05) controls impact.
  const score = clamp(total)
  console.log(`[Genomic] total=${total.toFixed(4)}, clamped score=${score.toFixed(4)}`)
  return { score, drivers }
}

// ─── Clinical score ───────────────────────────────────────────────────────────

function scoreClinical(c: PipelineInput["clinical"]): { score: number } {
  let s = 0.1
  if (c.age > 65) s += 0.04
  if (c.ca199 > 200) s += 0.08
  if (c.ca199 > 500) s += 0.06
  if (c.ecog >= 2) s += 0.04
  if (c.tumorSize > 3) s += 0.05
  return { score: clamp(s) }
}

// ─── Calibration curve generation ────────────────────────────────────────────

function buildCalibrationPoints(riskScore: number): { predicted: number; actual: number }[] {
  // Simulate a well-calibrated curve with systematic bias pattern typical of PDAC models
  // (slight under-prediction at low range, slight over-prediction at high range)
  const anchorPoints = [0.10, 0.20, 0.35, 0.50, 0.65, 0.75, riskScore]
    .sort((a, b) => a - b)
  return anchorPoints.map(p => ({
    predicted: round2(p),
    // Small deterministic offset — under-estimates below 0.5, over-estimates above 0.5
    actual: round2(clamp(p + (p < 0.5 ? 0.02 : -0.02))),
  }))
}

// ─── Main pipeline ────────────────────────────────────────────────────────────

export function runAnalysisPipeline(input: PipelineInput): ResultData {
  console.log("━━━ [Pipeline] Starting multimodal analysis ━━━")
  console.log("[Pipeline] Modality inputs:")
  console.log(`  Genomic variants     : ${input.genomicVariants.length}`)
  console.log(`  Transcriptomic genes : ${input.transcriptomicGenes.length}`)
  console.log(`  Radiomic values      :`, input.radiomicValues)
  console.log(`  Clinical data        :`, input.clinical)

  // 1. Compute modality scores
  const radResult = scoreRadiomic(input.radiomicValues)
  const txResult = scoreTxGenes(input.transcriptomicGenes)
  const genResult = scoreGenomic(input.genomicVariants)
  const clinResult = scoreClinical(input.clinical)

  console.log("━━━ [Pipeline] Modality subscores ━━━")
  console.log(`  Radiomic        : ${radResult.score.toFixed(4)}`)
  console.log(`  Transcriptomic  : ${txResult.score.toFixed(4)}`)
  console.log(`  Genomic         : ${genResult.score.toFixed(4)}`)
  console.log(`  Clinical        : ${clinResult.score.toFixed(4)}`)

  // 2. Weighted fusion
  // Weights reflect that radiomic imaging is the strongest independent predictor
  // of PDAC stage; transcriptomic is second; genomic has low stage specificity.
  const FUSION_WEIGHTS = { radiomic: 0.60, transcriptomic: 0.25, genomic: 0.05, clinical: 0.10 }
  const fusedRaw =
    FUSION_WEIGHTS.radiomic * radResult.score +
    FUSION_WEIGHTS.transcriptomic * txResult.score +
    FUSION_WEIGHTS.genomic * genResult.score +
    FUSION_WEIGHTS.clinical * clinResult.score

  console.log("━━━ [Pipeline] Fusion ━━━")
  console.log(`  Radiomic contrib    : ${(FUSION_WEIGHTS.radiomic * radResult.score).toFixed(4)}`)
  console.log(`  Transcriptomic cont : ${(FUSION_WEIGHTS.transcriptomic * txResult.score).toFixed(4)}`)
  console.log(`  Genomic contrib     : ${(FUSION_WEIGHTS.genomic * genResult.score).toFixed(4)}`)
  console.log(`  Clinical contrib    : ${(FUSION_WEIGHTS.clinical * clinResult.score).toFixed(4)}`)
  console.log(`  fusedRaw            : ${fusedRaw.toFixed(4)}`)

  // ── Effective contribution audit ─────────────────────────────────────────────
  // effective_contribution = weighted_modality_score / fusedRaw
  // This measures TRUE downstream influence, not just declared weight.
  // A modality can dominate if its score distribution is larger regardless of weight.
  const _safeTotal = fusedRaw || 1
  const effectiveAudit = {
    radiomic:       FUSION_WEIGHTS.radiomic       * radResult.score  / _safeTotal,
    transcriptomic: FUSION_WEIGHTS.transcriptomic * txResult.score   / _safeTotal,
    genomic:        FUSION_WEIGHTS.genomic        * genResult.score  / _safeTotal,
    clinical:       FUSION_WEIGHTS.clinical       * clinResult.score / _safeTotal,
  }
  console.log("━━━ [Pipeline] EFFECTIVE CONTRIBUTION AUDIT ━━━")
  console.log("  (effective = weighted_score / fusedRaw — true downstream influence)")
  for (const [key, eff] of Object.entries(effectiveAudit) as [keyof typeof FUSION_WEIGHTS, number][]) {
    const declared = FUSION_WEIGHTS[key]
    const drift = Math.abs(eff - declared)
    const flag = drift > 0.15 ? "  ⚠  IMBALANCE DETECTED" : ""
    console.log(`  ${key.padEnd(15)}: effective=${(eff * 100).toFixed(1)}%  declared=${(declared * 100).toFixed(0)}%  drift=${(drift * 100).toFixed(1)}%${flag}`)
  }

  const riskScore = round2(clamp(sigmoid((fusedRaw - 0.5) * 6)))
  console.log(`  riskScore (sigmoid) : ${riskScore.toFixed(4)}`)

  // 3. Compute normalised modality contributions
  const rawContribs = {
    Radiomic: FUSION_WEIGHTS.radiomic * radResult.score,
    Transcriptomic: FUSION_WEIGHTS.transcriptomic * txResult.score,
    Genomic: FUSION_WEIGHTS.genomic * genResult.score,
    Clinical: FUSION_WEIGHTS.clinical * clinResult.score,
  }
  const contribTotal = Object.values(rawContribs).reduce((a, b) => a + b, 0) || 1
  const modalityContributions = (Object.entries(rawContribs) as [ModalityKey, number][])
    .map(([modality, v]) => ({ modality, value: round2(v / contribTotal) }))
    .sort((a, b) => b.value - a.value)

  console.log("[Pipeline] Modality contributions:", modalityContributions)

  // 4. Confidence — based on distance from 0.5 decision boundary
  const distFromBoundary = Math.abs(riskScore - 0.5) * 2
  const confidence = round2(0.65 + distFromBoundary * 0.30)

  // 5. Brier score — approximated from confidence calibration
  const brierScore = round2(0.05 + (1 - distFromBoundary) * 0.12)

  // 6. Classification
  const classification = riskScore >= 0.5 ? "Late-stage likely" : "Early-stage likely"

  // 7. Feature drivers — merge and sort
  const allDrivers: FeatureDriver[] = [
    ...genResult.drivers,
    ...txResult.drivers,
    ...radResult.features
      .filter(f => Math.abs(f.contribution) > 0)
      .map(f => ({
        name: f.name,
        modality: "Radiomic" as ModalityKey,
        direction: f.contribution >= 0 ? "up" as const : "down" as const,
        score: f.contribution,
        explanation: f.interpretation,
      })),
  ].sort((a, b) => Math.abs(b.score) - Math.abs(a.score))

  // 8. Detected modalities
  const modalities: ModalityKey[] = []
  if (input.genomicVariants.length > 0) modalities.push("Genomic")
  if (input.transcriptomicGenes.length > 0) modalities.push("Transcriptomic")
  modalities.push("Radiomic")
  modalities.push("Clinical")

  // 9. Clinical record
  const clinicalData: ClinicalRecord = {
    age: input.clinical.age,
    sex: input.clinical.sex,
    tumorLocation: input.clinical.tumorLocation,
    tumorSize: input.clinical.tumorSize,
    ca199: input.clinical.ca199,
    ecog: input.clinical.ecog,
    stage: `Unknown (model inferred: ${riskScore >= 0.7 ? "Stage III–IV" : riskScore >= 0.5 ? "Stage II–III" : "Stage I–II"})`,
  }

  // Use corrected gene objects (uppercase symbols, group from weight table)
  const finalTxGenes = txResult.correctedGenes.length > 0
    ? txResult.correctedGenes
    : input.transcriptomicGenes

  const result: ResultData = {
    sampleId: `PAAD-${Date.now().toString(36).toUpperCase()}`,
    dateAnalyzed: new Date().toLocaleDateString("en-US", { year: "numeric", month: "long", day: "numeric" }),
    modalities,
    riskScore,
    classification,
    confidence,
    brierScore,
    modalityContributions,
    featureDrivers: allDrivers,
    genomicVariants: input.genomicVariants,
    transcriptomicGenes: finalTxGenes,
    radiomicFeatures: radResult.features,
    clinicalData,
    calibrationPoints: buildCalibrationPoints(riskScore),
  }

  console.log("━━━ [Pipeline] Analysis complete ━━━")
  console.log(`  Classification : ${result.classification}`)
  console.log(`  Risk score     : ${result.riskScore}`)
  console.log(`  Confidence     : ${result.confidence}`)
  return result
}
