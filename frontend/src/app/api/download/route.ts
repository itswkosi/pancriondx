import { NextRequest, NextResponse } from "next/server"

const ALLOWED_FILES: Record<string, string[]> = {
  genomic: [
    "PAAD-SAMPLE-001_clinical.tsv",
    "PAAD-SAMPLE-001_CNV.tsv",
    "PAAD-SAMPLE-001_mutations.tsv",
    "PAAD-SAMPLE-002_clinical.tsv",
    "PAAD-SAMPLE-002_CNV.tsv",
    "PAAD-SAMPLE-002_mutations.tsv",
    "PAAD-SAMPLE-003_clinical.tsv",
    "PAAD-SAMPLE-003_CNV.tsv",
    "PAAD-SAMPLE-003_mutations.tsv",
    "PAAD-SAMPLE-004_clinical.tsv",
    "PAAD-SAMPLE-004_CNV.tsv",
    "PAAD-SAMPLE-004_mutations.tsv",
  ],
  transcriptomic: [
    "PAAD-SAMPLE-001_transcriptomics.tsv",
    "PAAD-SAMPLE-001_transcriptomics_summary.tsv",
    "PAAD-SAMPLE-002_transcriptomics.tsv",
    "PAAD-SAMPLE-002_transcriptomics_summary.tsv",
    "PAAD-SAMPLE-003_transcriptomics.tsv",
    "PAAD-SAMPLE-003_transcriptomics_summary.tsv",
    "PAAD-SAMPLE-004_transcriptomics.tsv",
    "PAAD-SAMPLE-004_transcriptomics_summary.tsv",
  ],
  radiomic: ["ct_sample_selection_summary.csv"],
}

export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url)
  const type = searchParams.get("type") ?? ""
  const file = searchParams.get("file") ?? ""

  const allowed = ALLOWED_FILES[type]
  if (!allowed) {
    return new NextResponse("Invalid type", { status: 400 })
  }

  if (!file) {
    return NextResponse.json({ type, files: allowed })
  }

  if (!allowed.includes(file)) {
    return new NextResponse("File not found", { status: 404 })
  }

  const origin = req.headers.get("x-forwarded-host")
    ? `https://${req.headers.get("x-forwarded-host")}`
    : new URL(req.url).origin

  return NextResponse.redirect(`${origin}/sample-data/${type}/${file}`)
}
