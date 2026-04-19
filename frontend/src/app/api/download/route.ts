import { NextRequest, NextResponse } from "next/server"
import archiver from "archiver"
import path from "path"
import fs from "fs"
import { PassThrough } from "stream"

// Root of the project (two levels up from frontend/)
const PROJECT_ROOT = path.resolve(process.cwd(), "..")

const DATA_DIRS: Record<string, { dir: string; filename: string }> = {
  genomic: {
    dir: path.join(PROJECT_ROOT, "genomic sample data"),
    filename: "pancrionDX_genomic_sample.zip",
  },
  transcriptomic: {
    dir: path.join(PROJECT_ROOT, "transcriptomic sample data"),
    filename: "pancrionDX_transcriptomic_sample.zip",
  },
  radiomic: {
    dir: path.join(PROJECT_ROOT, "ct-sample data"),
    filename: "pancrionDX_radiomic_ct_sample.zip",
  },
}

export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url)
  const type = searchParams.get("type") ?? ""

  // ── Individual file download ────────────────────────────────────────────────
  if (type === "file") {
    const file = searchParams.get("file") ?? ""
    // Only allow files inside public/sample-data
    const safeName = path.basename(file)
    const category = searchParams.get("category") ?? ""
    if (!["genomic", "transcriptomic", "radiomic"].includes(category)) {
      return new NextResponse("Invalid category", { status: 400 })
    }
    const filePath = path.join(process.cwd(), "public", "sample-data", category, safeName)
    if (!fs.existsSync(filePath)) {
      return new NextResponse("File not found", { status: 404 })
    }
    const fileBuffer = fs.readFileSync(filePath)
    return new NextResponse(fileBuffer, {
      headers: {
        "Content-Type": "application/octet-stream",
        "Content-Disposition": `attachment; filename="${safeName}"`,
      },
    })
  }

  // ── Zip bundle download ─────────────────────────────────────────────────────
  if (type === "full") {
    // Zip all three data dirs together (excluding CT DICOM to keep size sane;
    // include the radiomic summary CSV and all genomic + transcriptomic TSVs)
    const passThrough = new PassThrough()
    const archive = archiver("zip", { zlib: { level: 6 } })
    archive.on("error", (err) => { throw err })
    archive.pipe(passThrough)

    for (const key of ["genomic", "transcriptomic"]) {
      const { dir } = DATA_DIRS[key]
      if (fs.existsSync(dir)) {
        archive.directory(dir, key)
      }
    }
    // Add just the radiomic summary CSV (not the 646MB DICOM folder)
    const radiomicCsv = path.join(process.cwd(), "public", "sample-data", "radiomic", "ct_sample_selection_summary.csv")
    if (fs.existsSync(radiomicCsv)) {
      archive.file(radiomicCsv, { name: "radiomic/ct_sample_selection_summary.csv" })
    }
    archive.finalize()

    const chunks: Buffer[] = []
    for await (const chunk of passThrough) {
      chunks.push(chunk as Buffer)
    }
    const buf = Buffer.concat(chunks)
    return new NextResponse(buf, {
      headers: {
        "Content-Type": "application/zip",
        "Content-Disposition": `attachment; filename="pancrionDX_sample_dataset.zip"`,
      },
    })
  }

  // ── Per-type zip ────────────────────────────────────────────────────────────
  const entry = DATA_DIRS[type]
  if (!entry) {
    return new NextResponse("Unknown type. Use ?type=genomic|transcriptomic|radiomic|full", {
      status: 400,
    })
  }

  // For radiomic / DICOM, only zip the summary CSV to keep it lightweight
  if (type === "radiomic") {
    const summaryPath = path.join(process.cwd(), "public", "sample-data", "radiomic", "ct_sample_selection_summary.csv")
    if (!fs.existsSync(summaryPath)) {
      return new NextResponse("Radiomic summary not found", { status: 404 })
    }
    const buf = fs.readFileSync(summaryPath)
    return new NextResponse(buf, {
      headers: {
        "Content-Type": "text/csv",
        "Content-Disposition": `attachment; filename="ct_sample_selection_summary.csv"`,
      },
    })
  }

  if (!fs.existsSync(entry.dir)) {
    return new NextResponse(`Source directory not found: ${entry.dir}`, { status: 404 })
  }

  const passThrough = new PassThrough()
  const archive = archiver("zip", { zlib: { level: 6 } })
  archive.on("error", (err) => { throw err })
  archive.pipe(passThrough)
  archive.directory(entry.dir, false)
  archive.finalize()

  const chunks: Buffer[] = []
  for await (const chunk of passThrough) {
    chunks.push(chunk as Buffer)
  }
  const buf = Buffer.concat(chunks)

  return new NextResponse(buf, {
    headers: {
      "Content-Type": "application/zip",
      "Content-Disposition": `attachment; filename="${entry.filename}"`,
    },
  })
}
