import { NextRequest, NextResponse } from "next/server"
import { readFile } from "fs/promises"
import path from "path"

// Maps category -> allowed filenames (filename only, no subdirectory)
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
    "PAAD-SAMPLE-002_transcriptomics.tsv",
    "PAAD-SAMPLE-003_transcriptomics.tsv",
    "PAAD-SAMPLE-004_transcriptomics.tsv",
  ],
  // radiomic DCM files live in patient subfolders: radiomic/<patientId>/<file>
  radiomic: [
    "C3L-02118/1-001.dcm",
    "C3L-02118/1-002.dcm",
    "C3L-02118/1-003.dcm",
    "C3L-03743/1-001.dcm",
    "C3L-03743/1-002.dcm",
    "C3L-03743/1-003.dcm",
    "C3L-05754/1-01.dcm",
    "C3L-05754/1-02.dcm",
    "C3L-05754/1-03.dcm",
    "C3N-03039/1-001.dcm",
    "C3N-03039/1-002.dcm",
    "C3N-03039/1-003.dcm",
    "C3N-03670/1-001.dcm",
    "C3N-03670/1-002.dcm",
    "C3N-03670/1-003.dcm",
  ],
}

const MIME: Record<string, string> = {
  tsv: "text/tab-separated-values",
  csv: "text/csv",
  dcm: "application/dicom",
}

function mimeFor(filename: string): string {
  const ext = filename.split(".").pop()?.toLowerCase() ?? ""
  return MIME[ext] ?? "application/octet-stream"
}

export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url)
  const type     = searchParams.get("type")     ?? ""
  const category = searchParams.get("category") ?? type  // support ?type=file&category=genomic
  const file     = searchParams.get("file")     ?? ""

  // ?type=full — not yet implemented, return 501
  if (type === "full") {
    return new NextResponse("Full ZIP download not yet available", { status: 501 })
  }

  const allowed = ALLOWED_FILES[category]
  if (!allowed) {
    return new NextResponse("Invalid category", { status: 400 })
  }

  // No file specified — return list
  if (!file) {
    return NextResponse.json({ category, files: allowed })
  }

  // For radiomic, file may include subfolder e.g. "C3L-02118/1-001.dcm"
  if (!allowed.includes(file)) {
    return new NextResponse("File not found", { status: 404 })
  }

  // Resolve absolute path inside public/sample-data
  const publicDir = path.join(process.cwd(), "public", "sample-data")
  const filePath  = path.join(publicDir, category, file)

  // Guard against path traversal
  if (!filePath.startsWith(publicDir)) {
    return new NextResponse("Forbidden", { status: 403 })
  }

  try {
    const buf      = await readFile(filePath)
    const filename = path.basename(file)   // strip any subfolder from Content-Disposition
    return new NextResponse(buf, {
      status: 200,
      headers: {
        "Content-Type":        mimeFor(filename),
        "Content-Disposition": `attachment; filename="${filename}"`,
        "Cache-Control":       "public, max-age=86400",
      },
    })
  } catch {
    return new NextResponse("File not found", { status: 404 })
  }
}
