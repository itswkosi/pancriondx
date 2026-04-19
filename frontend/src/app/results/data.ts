// ─── Shared types ─────────────────────────────────────────────────────────────

export type Classification = "Late-stage likely" | "Early-stage likely"

export type ModalityKey = "Radiomic" | "Transcriptomic" | "Genomic" | "Clinical"

export interface ResultData {
  sampleId: string
  dateAnalyzed: string
  modalities: ModalityKey[]
  riskScore: number
  classification: Classification
  confidence: number
  brierScore: number
  modalityContributions: { modality: ModalityKey; value: number }[]
  featureDrivers: FeatureDriver[]
  genomicVariants: GenomicVariant[]
  transcriptomicGenes: TranscriptomicGene[]
  radiomicFeatures: RadiomicFeature[]
  clinicalData: ClinicalRecord
  calibrationPoints: { predicted: number; actual: number }[]
}

export interface FeatureDriver {
  name: string
  modality: ModalityKey
  direction: "up" | "down"
  score: number
  explanation: string
}

export interface GenomicVariant {
  gene: string
  variant: string
  pathogenicity: "pathogenic" | "likely_pathogenic" | "vus" | "benign"
  weight: number
}

export interface TranscriptomicGene {
  gene: string
  zscore: number
  group: "stromal" | "dna_damage" | "other"
  direction: "up" | "down"
}

export interface RadiomicFeature {
  name: string
  value: number
  unit: string
  interpretation: string
  contribution: number
}

export interface ClinicalRecord {
  age: number
  sex: string
  tumorLocation: string
  tumorSize: number
  ca199: number
  ecog: number
  stage: string
}

// ─── Dummy data ───────────────────────────────────────────────────────────────

export const RESULT: ResultData = {
  sampleId: "PAAD-SAMPLE-001",
  dateAnalyzed: "April 19, 2026",
  modalities: ["Genomic", "Transcriptomic", "Radiomic", "Clinical"],
  riskScore: 0.87,
  classification: "Late-stage likely",
  confidence: 0.91,
  brierScore: 0.118,
  modalityContributions: [
    { modality: "Radiomic", value: 0.83 },
    { modality: "Transcriptomic", value: 0.11 },
    { modality: "Clinical", value: 0.04 },
    { modality: "Genomic", value: 0.02 },
  ],
  featureDrivers: [
    {
      name: "KRAS mutation",
      modality: "Genomic",
      direction: "up",
      score: 0.42,
      explanation: "Ubiquitous in PDAC; presence consistent with late-stage genomic landscape.",
    },
    {
      name: "TP53 mutation",
      modality: "Genomic",
      direction: "up",
      score: 0.35,
      explanation: "Increases late-stage probability via genomic instability and p53 pathway loss.",
    },
    {
      name: "CDKN2A loss",
      modality: "Genomic",
      direction: "down",
      score: -0.18,
      explanation: "Cell-cycle regulator loss weakly associated with progression stage.",
    },
    {
      name: "COL1A1 expression",
      modality: "Transcriptomic",
      direction: "up",
      score: 0.26,
      explanation: "Elevated stromal collagen expression characteristic of desmoplastic late-stage PDAC.",
    },
    {
      name: "FAP expression",
      modality: "Transcriptomic",
      direction: "up",
      score: 0.18,
      explanation: "Fibroblast activation protein upregulation marks dense stroma in advanced disease.",
    },
    {
      name: "VIM expression",
      modality: "Transcriptomic",
      direction: "down",
      score: -0.11,
      explanation: "Vimentin reduction may reflect mesenchymal-to-epithelial reversion in late stage.",
    },
    {
      name: "Tumor size",
      modality: "Radiomic",
      direction: "up",
      score: 0.38,
      explanation: "Larger tumour diameter strongly predicts advanced local extension.",
    },
    {
      name: "Necrosis score",
      modality: "Radiomic",
      direction: "up",
      score: 0.32,
      explanation: "Central necrosis on imaging is a hallmark of aggressive, late-stage PDAC.",
    },
    {
      name: "Edge sharpness",
      modality: "Radiomic",
      direction: "down",
      score: -0.26,
      explanation: "Loss of tumour margin definition indicates local infiltration.",
    },
  ],
  genomicVariants: [
    { gene: "KRAS", variant: "G12D", pathogenicity: "pathogenic", weight: 0.42 },
    { gene: "TP53", variant: "R175H", pathogenicity: "pathogenic", weight: 0.35 },
    { gene: "CDKN2A", variant: "deletion", pathogenicity: "pathogenic", weight: 0.18 },
    { gene: "SMAD4", variant: "Q311*", pathogenicity: "likely_pathogenic", weight: 0.12 },
    { gene: "BRCA2", variant: "V1736A", pathogenicity: "vus", weight: 0.05 },
  ],
  transcriptomicGenes: [
    { gene: "COL1A1", zscore: 3.14, group: "stromal", direction: "up" },
    { gene: "FAP", zscore: 2.87, group: "stromal", direction: "up" },
    { gene: "FN1", zscore: 2.44, group: "stromal", direction: "up" },
    { gene: "ACTA2", zscore: 1.92, group: "stromal", direction: "up" },
    { gene: "TP53", zscore: 1.61, group: "dna_damage", direction: "up" },
    { gene: "BRCA2", zscore: -0.88, group: "dna_damage", direction: "down" },
    { gene: "VIM", zscore: -1.23, group: "other", direction: "down" },
    { gene: "CDH1", zscore: -1.78, group: "other", direction: "down" },
  ],
  radiomicFeatures: [
    {
      name: "Tumor Size",
      value: 3.2,
      unit: "cm",
      interpretation: "Above median threshold (2.5 cm) for late-stage PDAC in this cohort.",
      contribution: 0.38,
    },
    {
      name: "Necrosis Score",
      value: 0.62,
      unit: "",
      interpretation: "Elevated central necrosis fraction consistent with aggressive phenotype.",
      contribution: 0.32,
    },
    {
      name: "Texture Heterogeneity",
      value: 0.75,
      unit: "",
      interpretation: "High heterogeneity reflects tumour microenvironment complexity.",
      contribution: 0.21,
    },
    {
      name: "Edge Sharpness",
      value: 0.45,
      unit: "",
      interpretation: "Low margin definition suggests local infiltration and invasion.",
      contribution: -0.26,
    },
  ],
  clinicalData: {
    age: 67,
    sex: "Female",
    tumorLocation: "Head of pancreas",
    tumorSize: 3.2,
    ca199: 302,
    ecog: 1,
    stage: "Unknown (model inferred: Stage III–IV)",
  },
  calibrationPoints: [
    { predicted: 0.1, actual: 0.08 },
    { predicted: 0.2, actual: 0.19 },
    { predicted: 0.35, actual: 0.37 },
    { predicted: 0.5, actual: 0.52 },
    { predicted: 0.65, actual: 0.63 },
    { predicted: 0.75, actual: 0.78 },
    { predicted: 0.87, actual: 0.91 },
  ],
}
