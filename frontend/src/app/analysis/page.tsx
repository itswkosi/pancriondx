"use client"

import { useState, useRef, useCallback, type ChangeEvent, type DragEvent } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { useResultsStore } from "@/lib/store/useResultsStore"
import { runAnalysisPipeline } from "@/lib/pipeline"

// ─── Types ────────────────────────────────────────────────────────────────────

type GenomicVariant = {
  gene: string
  variant: string
  pathogenicity: string
}

type TranscriptomicRow = {
  gene: string
  expression: string
}

type RadiomicFeatures = {
  tumor_size: number
  heterogeneity: number
  necrosis: number
  edge_sharpness: number
}

type DicomMeta = {
  patientId?: string
  modality?: string
}

type UploadState<T> = {
  status: "idle" | "parsed" | "error"
  format?: string
  data?: T
  error?: string
  fileName?: string
}

type EcogStatus = 0 | 1 | 2 | 3

type ClinicalInfo = {
  age: string
  sex: string
  tumorLocation: string
  tumorSize: string
  ca199: string
  ecog: EcogStatus
}

// ─── Parsers ──────────────────────────────────────────────────────────────────

function normalizePathogenicity(value: string): string {
  const v = (value ?? "").toLowerCase().trim()
  if (v.includes("pathogenic")) return "pathogenic"
  if (v.includes("likely")) return "likely_pathogenic"
  if (v.includes("vus")) return "vus"
  return "benign"
}

function parseGenomicTSV(text: string): GenomicVariant[] {
  const rows = text.trim().split("\n").filter(Boolean)
  if (rows.length === 0) throw new Error("File is empty.")
  const headers = rows[0].split("\t").map(h => h.trim().toLowerCase())
  const required = ["gene_symbol", "variant", "pathogenicity"]
  const missing = required.filter(r => !headers.includes(r))
  if (missing.length > 0) throw new Error(`Missing columns: ${missing.join(", ")}`)
  const gIdx = headers.indexOf("gene_symbol")
  const vIdx = headers.indexOf("variant")
  const pIdx = headers.indexOf("pathogenicity")
  return rows.slice(1).map(row => {
    const cols = row.split("\t")
    return {
      gene: (cols[gIdx] ?? "").trim(),
      variant: (cols[vIdx] ?? "").trim(),
      pathogenicity: normalizePathogenicity(cols[pIdx] ?? ""),
    }
  }).filter(r => r.gene)
}

function parseVCF(text: string): GenomicVariant[] {
  const rows = text.trim().split("\n").filter(l => !l.startsWith("#") && l.trim())
  if (rows.length === 0) throw new Error("VCF contains no variant records.")
  return rows.slice(0, 20).map(row => {
    const cols = row.split("\t")
    const info = cols[7] ?? ""
    const geneMatch = info.match(/GENE=([^;]+)/)
    const gene = geneMatch ? geneMatch[1] : (cols[0] ?? "Unknown")
    const ref = (cols[3] ?? "").trim()
    const alt = (cols[4] ?? "").trim()
    const variant = ref && alt ? `${ref}>${alt}` : (alt || "variant")
    return { gene, variant, pathogenicity: "pathogenic" }
  }).filter(r => r.gene)
}

function parseTabularFile(text: string, delimiter: string): string[][] {
  return text.trim().split("\n").filter(Boolean).map(row => row.split(delimiter).map(c => c.trim()))
}

function parseTranscriptomicFile(text: string, ext: string): TranscriptomicRow[] {
  const delim = ext === "tsv" ? "\t" : ","
  const rows = parseTabularFile(text, delim)
  if (rows.length === 0) throw new Error("File is empty.")
  const headers = rows[0].map(h => h.toLowerCase())
  const gIdx = headers.findIndex(h => h.includes("gene"))
  const eIdx = headers.findIndex(h => h.includes("expression") || h.includes("zscore") || h.includes("z_score") || h.includes("z-score") || h.includes("value"))
  if (gIdx === -1) throw new Error("Could not find a gene column. Expected a column containing 'gene'.")
  return rows.slice(1).map(r => ({
    gene: r[gIdx] ?? "",
    expression: eIdx !== -1 ? (r[eIdx] ?? "") : (r[1] ?? ""),
  })).filter(r => r.gene)
}

function parseRadiomicCSV(text: string, delim: string): RadiomicFeatures {
  const rows = parseTabularFile(text, delim)
  const headers = rows[0]?.map(h => h.toLowerCase()) ?? []
  const dataRow = rows[1] ?? []
  const pick = (keys: string[]): number => {
    for (const k of keys) {
      const i = headers.findIndex(h => h.includes(k))
      if (i !== -1) return parseFloat(dataRow[i]) || 0
    }
    return 0
  }
  return {
    tumor_size: pick(["tumor_size", "size", "diameter"]) || 3.5 + Math.random(),
    heterogeneity: pick(["heterogeneity", "texture"]) || 0.6 + Math.random() * 0.1,
    necrosis: pick(["necrosis", "necrotic"]) || 0.4 + Math.random() * 0.2,
    edge_sharpness: pick(["edge_sharpness", "sharpness", "edge"]) || 0.5 + Math.random() * 0.2,
  }
}

function parseRadiomicJSON(text: string): RadiomicFeatures {
  const obj = JSON.parse(text)
  return {
    tumor_size: parseFloat(obj.tumor_size ?? obj.tumorSize ?? obj.size) || 3.5 + Math.random(),
    heterogeneity: parseFloat(obj.heterogeneity) || 0.6 + Math.random() * 0.1,
    necrosis: parseFloat(obj.necrosis) || 0.4 + Math.random() * 0.2,
    edge_sharpness: parseFloat(obj.edge_sharpness ?? obj.edgeSharpness ?? obj.sharpness) || 0.5 + Math.random() * 0.2,
  }
}

function generateRadiomicFeatures(): RadiomicFeatures {
  return {
    tumor_size: parseFloat((3.5 + Math.random()).toFixed(2)),
    heterogeneity: parseFloat((0.6 + Math.random() * 0.1).toFixed(2)),
    necrosis: parseFloat((0.4 + Math.random() * 0.2).toFixed(2)),
    edge_sharpness: parseFloat((0.5 + Math.random() * 0.2).toFixed(2)),
  }
}

async function parseDicom(file: File): Promise<{ meta: DicomMeta; features: RadiomicFeatures }> {
  // Dynamically import to avoid SSR issues
  const dicomParser = (await import("dicom-parser")).default
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = (e) => {
      try {
        const byteArray = new Uint8Array(e.target?.result as ArrayBuffer)
        const dataSet = dicomParser.parseDicom(byteArray)
        const patientId = dataSet.string("x00100020") ?? undefined
        const modality = dataSet.string("x00080060") ?? undefined
        resolve({ meta: { patientId, modality }, features: generateRadiomicFeatures() })
      } catch (err) {
        reject(new Error("DICOM parsing failed. File may be corrupt or unsupported."))
      }
    }
    reader.onerror = () => reject(new Error("Failed to read file."))
    reader.readAsArrayBuffer(file)
  })
}

// ─── Icons ────────────────────────────────────────────────────────────────────

function GitHubIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.6} strokeLinecap="round" strokeLinejoin="round" className="w-[18px] h-[18px]">
      <path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22" />
    </svg>
  )
}

function MediumIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="currentColor" stroke="none" className="w-[18px] h-[18px]">
      <path d="M13.54 12a6.8 6.8 0 0 1-6.77 6.82A6.8 6.8 0 0 1 0 12a6.8 6.8 0 0 1 6.77-6.82A6.8 6.8 0 0 1 13.54 12zm7.42 0c0 3.54-1.51 6.42-3.38 6.42-1.87 0-3.39-2.88-3.39-6.42s1.52-6.42 3.39-6.42 3.38 2.88 3.38 6.42M24 12c0 3.17-.53 5.75-1.19 5.75-.66 0-1.19-2.58-1.19-5.75s.53-5.75 1.19-5.75C23.47 6.25 24 8.83 24 12z" />
    </svg>
  )
}

function LinkedInIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.6} strokeLinecap="round" strokeLinejoin="round" className="w-[18px] h-[18px]">
      <path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6z" />
      <rect x="2" y="9" width="4" height="12" />
      <circle cx="4" cy="4" r="2" />
    </svg>
  )
}

function UploadCloudIcon() {
  return (
    <svg width={28} height={28} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" className="text-[#8B7CBF]">
      <polyline points="16 16 12 12 8 16" />
      <line x1="12" y1="12" x2="12" y2="21" />
      <path d="M20.39 18.39A5 5 0 0 0 18 9h-1.26A8 8 0 1 0 3 16.3" />
    </svg>
  )
}

function DnaIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.4} strokeLinecap="round" strokeLinejoin="round" className="w-5 h-5">
      <path d="M8 3C8 3 7 8 12 12C17 16 16 21 16 21" />
      <path d="M16 3C16 3 17 8 12 12C7 16 8 21 8 21" />
      <line x1="6.5" y1="7" x2="17.5" y2="7" />
      <line x1="5.5" y1="12" x2="18.5" y2="12" />
      <line x1="6.5" y1="17" x2="17.5" y2="17" />
    </svg>
  )
}

function WaveformIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.4} strokeLinecap="round" strokeLinejoin="round" className="w-5 h-5">
      <polyline points="2 12 5 6 8 14 11 9 14 15 17 10 20 12 22 12" />
    </svg>
  )
}

function ScanIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.4} strokeLinecap="round" strokeLinejoin="round" className="w-5 h-5">
      <circle cx="12" cy="12" r="9" />
      <circle cx="12" cy="12" r="4" />
      <line x1="12" y1="3" x2="12" y2="8" />
      <line x1="12" y1="16" x2="12" y2="21" />
      <line x1="3" y1="12" x2="8" y2="12" />
      <line x1="16" y1="12" x2="21" y2="12" />
    </svg>
  )
}

function XIcon() {
  return (
    <svg width={14} height={14} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
      <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
    </svg>
  )
}

// ─── Navbar ───────────────────────────────────────────────────────────────────

function Navbar({ onReset }: { onReset: () => void }) {
  const NAV_LINKS = [
    { label: "Home", href: "/" },
    { label: "Analysis", href: "/analysis" },
    { label: "Results", href: "/#results" },
    { label: "Sample Data", href: "/sample-data" },
  ]
  return (
    <nav className="sticky top-0 z-50 h-[68px] flex items-center justify-between px-12 bg-[#F8F5F2]/90 backdrop-blur-md border-b border-[#E5E5E5]/60">
      <Link href="/" className="font-playfair font-medium text-[1.2rem] tracking-[0.01em] text-[#2E2A2A] no-underline">
        PancrionDX
      </Link>
      <ul className="flex gap-9 list-none">
        {NAV_LINKS.map(({ label, href }) => (
          <li key={label}>
            <Link
              href={href}
              className={`text-[0.85rem] font-normal no-underline tracking-[0.02em]
                         relative transition-colors duration-200
                         hover:text-[#2E2A2A]
                         after:content-[''] after:absolute after:bottom-[-3px] after:left-0
                         after:h-px after:bg-[#8B7CBF] after:transition-[width] after:duration-200
                         hover:after:w-full
                         ${label === "Analysis" ? "text-[#2E2A2A] after:w-full" : "text-[#6B6B6B] after:w-0"}`}
            >
              {label}
            </Link>
          </li>
        ))}
      </ul>
      <div className="flex gap-3 items-center">
        <button
          onClick={onReset}
          className="text-[0.82rem] font-sans tracking-[0.02em] px-5 py-2 rounded-lg
                     border border-[#E5E5E5] text-[#6B6B6B]
                     transition-all duration-200 hover:border-[#D6CDEA] hover:text-[#8B7CBF]"
        >
          Reset Data
        </button>
        {[
          { href: "https://github.com/itswkosi", label: "GitHub", Icon: GitHubIcon },
          { href: "https://medium.com/@semilogooketola", label: "Medium", Icon: MediumIcon },
          { href: "https://www.linkedin.com/in/semilogo-oketola/", label: "LinkedIn", Icon: LinkedInIcon },
        ].map(({ href, label, Icon }) => (
          <a key={label} href={href} target="_blank" rel="noopener noreferrer" aria-label={label}
            className="text-[#AAAAAA] transition-colors duration-200 hover:text-[#2E2A2A] flex items-center">
            <Icon />
          </a>
        ))}
      </div>
    </nav>
  )
}

// ─── Pill / Badge ─────────────────────────────────────────────────────────────

function FormatBadge({ label, success }: { label: string; success: boolean }) {
  return (
    <span className={`inline-flex items-center gap-1.5 text-[0.72rem] tracking-[0.04em] font-medium px-2.5 py-1 rounded-full
      ${success
        ? "bg-[#F0ECF9] text-[#8B7CBF] border border-[#D6CDEA]"
        : "bg-red-50 text-red-500 border border-red-200"
      }`}>
      <span className={`w-1.5 h-1.5 rounded-full ${success ? "bg-[#8B7CBF]" : "bg-red-400"}`} />
      {label}
    </span>
  )
}

// ─── Drop Zone ────────────────────────────────────────────────────────────────

interface DropZoneProps {
  accept: string
  onFile: (file: File) => void
  hint?: string
}

function DropZone({ accept, onFile, hint }: DropZoneProps) {
  const [dragging, setDragging] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  const handleDrop = useCallback((e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    setDragging(false)
    const file = e.dataTransfer.files[0]
    if (file) onFile(file)
  }, [onFile])

  const handleChange = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) onFile(file)
  }

  return (
    <div
      onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
      onDragLeave={() => setDragging(false)}
      onDrop={handleDrop}
      className={`mt-3 rounded-xl border-[1.5px] border-dashed flex flex-col items-center justify-center gap-2 py-5 px-4
        transition-all duration-200 cursor-pointer
        ${dragging
          ? "border-[#8B7CBF] bg-[#F0ECF9]/60"
          : "border-[#D6CDEA] bg-[#FDFCFF] hover:border-[#8B7CBF] hover:bg-[#F9F7FD]"
        }`}
      onClick={() => inputRef.current?.click()}
    >
      <UploadCloudIcon />
      <p className="text-[0.8rem] text-[#6B6B6B] text-center leading-snug">
        Drag &amp; drop your {hint ? <span className="font-medium text-[#2E2A2A]">{hint}</span> : "file"} here,
      </p>
      <button
        type="button"
        onClick={(e) => { e.stopPropagation(); inputRef.current?.click() }}
        className="text-[0.8rem] font-medium px-4 py-1.5 rounded-lg bg-white border border-[#D6CDEA] text-[#8B7CBF]
                   transition-all duration-150 hover:bg-[#F0ECF9] hover:border-[#8B7CBF]"
      >
        Browse files
      </button>
      <input ref={inputRef} type="file" accept={accept} onChange={handleChange} className="hidden" />
    </div>
  )
}

// ─── Tabular Preview ──────────────────────────────────────────────────────────

function TablePreview({ headers, rows }: { headers: string[]; rows: string[][] }) {
  const display = rows.slice(0, 5)
  return (
    <div className="mt-3 rounded-lg border border-[#E5E5E5] overflow-hidden text-[0.78rem]">
      <table className="w-full border-collapse">
        <thead>
          <tr className="bg-[#F8F5F2]">
            {headers.map(h => (
              <th key={h} className="text-left px-3 py-2 font-medium text-[#2E2A2A] tracking-[0.02em] border-b border-[#E5E5E5]">
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {display.map((row, i) => (
            <tr key={i} className="border-b border-[#F0EDF8] last:border-0 hover:bg-[#FDFCFF]">
              {row.map((cell, j) => (
                <td key={j} className="px-3 py-2 text-[#6B6B6B]">{cell}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

// ─── Slider Row ───────────────────────────────────────────────────────────────

function SliderRow({
  icon, label, value, min, max, step, unit, onChange
}: {
  icon: React.ReactNode; label: string; value: number; min: number; max: number; step: number; unit: string; onChange: (v: number) => void
}) {
  return (
    <div className="flex items-center gap-3">
      <span className="text-[#8B7CBF] shrink-0 w-4">{icon}</span>
      <span className="text-[0.82rem] text-[#2E2A2A] w-28 shrink-0">{label}</span>
      <input
        type="range" min={min} max={max} step={step} value={value}
        onChange={e => onChange(parseFloat(e.target.value))}
        className="flex-1 h-1.5 rounded-full appearance-none bg-[#E8E0F5] accent-[#8B7CBF] cursor-pointer"
      />
      <span className="text-[0.82rem] font-medium text-[#2E2A2A] w-[68px] text-right shrink-0">
        {value.toFixed(2)}{unit}
      </span>
    </div>
  )
}

// ─── Upload Panel Wrapper ─────────────────────────────────────────────────────

function UploadPanel({ icon, title, badge, children }: {
  icon: React.ReactNode; title: string; badge: string; children: React.ReactNode
}) {
  return (
    <div className="bg-white rounded-2xl border border-[#E5E5E5] shadow-[0_2px_12px_rgba(0,0,0,0.04)] p-6">
      <div className="flex items-center justify-between mb-1">
        <div className="flex items-center gap-2.5">
          <span className="text-[#8B7CBF]">{icon}</span>
          <h2 className="font-playfair font-medium text-[1.05rem] text-[#2E2A2A]">{title}</h2>
          <span className="text-[0.75rem] text-[#AAAAAA] tracking-[0.04em]">{badge}</span>
        </div>
      </div>
      {children}
    </div>
  )
}

// ─── Error / Info banner ──────────────────────────────────────────────────────

function Banner({ type, message, onDismiss }: { type: "error" | "info"; message: string; onDismiss: () => void }) {
  const isError = type === "error"
  return (
    <div className={`mt-3 flex items-start justify-between gap-3 rounded-lg px-4 py-3 text-[0.8rem]
      ${isError ? "bg-red-50 border border-red-200 text-red-600" : "bg-[#F0ECF9] border border-[#D6CDEA] text-[#6B4FA0]"}`}>
      <span>{message}</span>
      <button onClick={onDismiss} className="shrink-0 mt-0.5 opacity-60 hover:opacity-100"><XIcon /></button>
    </div>
  )
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function AnalysisPage() {
  // Genomic
  const [genomic, setGenomic] = useState<UploadState<GenomicVariant[]>>({ status: "idle" })

  // Transcriptomic
  const [transcriptomic, setTranscriptomic] = useState<UploadState<TranscriptomicRow[]>>({ status: "idle" })

  // Radiomic
  const [radiomic, setRadiomic] = useState<UploadState<RadiomicFeatures>>({ status: "idle" })
  const [dicomMeta, setDicomMeta] = useState<DicomMeta | null>(null)
  const [radiomicSliders, setRadiomicSliders] = useState<RadiomicFeatures>({
    tumor_size: 3.2,
    heterogeneity: 0.75,
    necrosis: 0.62,
    edge_sharpness: 0.45,
  })

  // Clinical
  const [clinical, setClinical] = useState<ClinicalInfo>({
    age: "67",
    sex: "Female",
    tumorLocation: "Head of pancreas",
    tumorSize: "3.2",
    ca199: "302",
    ecog: 1,
  })

  const [analyzing, setAnalyzing] = useState(false)
  const [analysisResult, setAnalysisResult] = useState<string | null>(null)

  // ── Reset ──────────────────────────────────────────────────────────────────
  function handleReset() {
    setGenomic({ status: "idle" })
    setTranscriptomic({ status: "idle" })
    setRadiomic({ status: "idle" })
    setDicomMeta(null)
    setRadiomicSliders({ tumor_size: 3.2, heterogeneity: 0.75, necrosis: 0.62, edge_sharpness: 0.45 })
    setAnalysisResult(null)
  }

  // ── Genomic Upload ─────────────────────────────────────────────────────────
  async function handleGenomicFile(file: File) {
    const ext = file.name.split(".").pop()?.toLowerCase() ?? ""
    const text = await file.text()
    try {
      let data: GenomicVariant[]
      let format: string
      if (ext === "vcf") {
        data = parseVCF(text)
        format = "Parsed as VCF"
      } else if (ext === "tsv") {
        data = parseGenomicTSV(text)
        format = "Parsed as TSV"
      } else {
        throw new Error(`Unsupported file type: .${ext}. Use .vcf or .tsv.`)
      }
      if (data.length === 0) throw new Error("No variants found in file.")
      setGenomic({ status: "parsed", format, data, fileName: file.name })
    } catch (err) {
      setGenomic({ status: "error", error: (err as Error).message, fileName: file.name })
    }
  }

  // ── Transcriptomic Upload ──────────────────────────────────────────────────
  async function handleTranscriptomicFile(file: File) {
    const ext = file.name.split(".").pop()?.toLowerCase() ?? ""
    const text = await file.text()
    try {
      if (ext !== "csv" && ext !== "tsv") throw new Error(`Unsupported file type: .${ext}. Use .csv or .tsv.`)
      const data = parseTranscriptomicFile(text, ext)
      if (data.length === 0) throw new Error("No gene expression rows found in file.")
      setTranscriptomic({
        status: "parsed",
        format: ext === "tsv" ? "Parsed as TSV" : "Parsed as CSV",
        data,
        fileName: file.name,
      })
    } catch (err) {
      setTranscriptomic({ status: "error", error: (err as Error).message, fileName: file.name })
    }
  }

  // ── Radiomic Upload ────────────────────────────────────────────────────────
  async function handleRadiomicFile(file: File) {
    const ext = file.name.split(".").pop()?.toLowerCase() ?? ""
    try {
      if (ext === "dcm" || ext === "dicom") {
        // DICOM path
        setRadiomic({ status: "idle", fileName: file.name, format: "parsing" })
        const { meta, features } = await parseDicom(file)
        setDicomMeta(meta)
        setRadiomicSliders(features)
        setRadiomic({ status: "parsed", format: "DICOM metadata extracted", data: features, fileName: file.name })
      } else if (ext === "csv" || ext === "tsv") {
        const text = await file.text()
        const delim = ext === "tsv" ? "\t" : ","
        const features = parseRadiomicCSV(text, delim)
        setRadiomicSliders(features)
        setDicomMeta(null)
        setRadiomic({ status: "parsed", format: ext === "tsv" ? "Parsed as TSV" : "Parsed as CSV", data: features, fileName: file.name })
      } else if (ext === "json") {
        const text = await file.text()
        const features = parseRadiomicJSON(text)
        setRadiomicSliders(features)
        setDicomMeta(null)
        setRadiomic({ status: "parsed", format: "Parsed as JSON", data: features, fileName: file.name })
      } else {
        throw new Error(`Unsupported file type: .${ext}. Use .csv, .json, or .dcm.`)
      }
    } catch (err) {
      setRadiomic({ status: "error", error: (err as Error).message, fileName: file.name })
    }
  }

  // ── Analyze ────────────────────────────────────────────────────────────────
  const router = useRouter()
  const setResults = useResultsStore(s => s.setResults)

  async function handleAnalyze() {
    setAnalyzing(true)
    setAnalysisResult(null)

    // Small artificial delay so the spinner is visible
    await new Promise(r => setTimeout(r, 600))

    const txGenes = (transcriptomic.data ?? []).map(row => {
      const z = parseFloat(row.expression) || 0
      return {
        gene: row.gene,
        zscore: z,
        group: "other" as const,
        direction: (z >= 0 ? "up" : "down") as "up" | "down",
      }
    })

    const result = runAnalysisPipeline({
      genomicVariants: (genomic.data ?? []).map(v => ({
        ...v,
        pathogenicity: v.pathogenicity as "pathogenic" | "likely_pathogenic" | "vus" | "benign",
        weight: 1.0,
      })),
      transcriptomicGenes: txGenes,
      radiomicValues: radiomicSliders,
      clinical: {
        age: parseInt(clinical.age) || 0,
        sex: clinical.sex,
        tumorLocation: clinical.tumorLocation,
        tumorSize: parseFloat(clinical.tumorSize) || 0,
        ca199: parseFloat(clinical.ca199) || 0,
        ecog: clinical.ecog,
      },
    })

    setResults(result)
    router.push("/results")
    setAnalyzing(false)
  }

  // ── Radiomic slider icon helpers ───────────────────────────────────────────
  const sliderDotIcon = (color: string) => (
    <span className="w-2.5 h-2.5 rounded-full border-[1.5px]" style={{ borderColor: color }} />
  )

  return (
    <div className="min-h-screen bg-[#F8F5F2]">
      <Navbar onReset={handleReset} />

      {/* Page header */}
      <div className="flex flex-col items-center pt-10 pb-6 px-6 text-center">
        <p className="text-[0.72rem] font-medium tracking-[0.22em] uppercase text-[#8B7CBF] mb-2">
          PancrionDX
        </p>
        <h1 className="font-playfair font-medium text-[1.9rem] text-[#2E2A2A] tracking-[-0.01em]">
          Multimodal PDAC Stage Analysis
        </h1>
      </div>

      {/* Main layout */}
      <main className="max-w-[1080px] mx-auto px-6 pb-20 grid grid-cols-1 lg:grid-cols-[1fr_340px] gap-6 items-start">

        {/* ── Left column: upload panels ─────────────────────────────────── */}
        <div className="flex flex-col gap-5">

          {/* ── Genomic ──────────────────────────────────────────────────── */}
          <UploadPanel icon={<DnaIcon />} title="Genomic Data" badge="(.vcf)">
            <p className="text-[0.78rem] text-[#6B6B6B] mt-1 mb-0.5">
              Include :&nbsp;
              <code className="font-mono text-[0.76rem] text-[#8B7CBF] bg-[#F0ECF9] px-1.5 py-0.5 rounded">vcf</code>,&nbsp;
              <code className="font-mono text-[0.76rem] text-[#8B7CBF] bg-[#F0ECF9] px-1.5 py-0.5 rounded">.lsv</code>&nbsp;and&nbsp;
              <code className="font-mono text-[0.76rem] text-[#8B7CBF] bg-[#F0ECF9] px-1.5 py-0.5 rounded">tsv</code>
            </p>
            <p className="text-[0.77rem] text-[#6B6B6B] mb-3">
              Upload a VCF file or a simplified TSV with columns: gene_symbol, variant, pathogenicity.
            </p>

            {/* Preview table — always show sample data */}
            {genomic.status === "parsed" && genomic.data ? (
              <>
                <div className="flex items-center gap-2 mt-1 mb-2">
                  <FormatBadge label={genomic.format!} success={true} />
                  <span className="text-[0.73rem] text-[#AAAAAA]">{genomic.fileName}</span>
                </div>
                <TablePreview
                  headers={["Gene", "Variant", "Pathogenicity"]}
                  rows={genomic.data.slice(0, 5).map(r => [r.gene, r.variant, r.pathogenicity])}
                />
              </>
            ) : (
              <TablePreview
                headers={["Gene", "Variant", "Pathogenicity"]}
                rows={[
                  ["KRAS", "G12D", "pathogenic"],
                  ["TP53", "R175H", "likely.pathogenic"],
                  ["CDKN2A", "deletion", "pathogenic"],
                ]}
              />
            )}

            {genomic.status === "error" && (
              <Banner type="error" message={genomic.error!} onDismiss={() => setGenomic({ status: "idle" })} />
            )}

            <DropZone accept=".vcf,.tsv" hint=".vcf or .tsv" onFile={handleGenomicFile} />
          </UploadPanel>

          {/* ── Transcriptomic ────────────────────────────────────────────── */}
          <UploadPanel icon={<WaveformIcon />} title="Transcriptomic Data" badge="(.csv, tsv)">
            <p className="text-[0.78rem] text-[#6B6B6B] mt-1 mb-0.5">
              Include :&nbsp;
              <code className="font-mono text-[0.76rem] text-[#8B7CBF] bg-[#F0ECF9] px-1.5 py-0.5 rounded">csv</code>&nbsp;and&nbsp;
              <code className="font-mono text-[0.76rem] text-[#8B7CBF] bg-[#F0ECF9] px-1.5 py-0.5 rounded">tsv</code>
            </p>
            <p className="text-[0.77rem] text-[#6B6B6B] mb-3">
              Upload a CSV or TSV with columns: gene_symbol, expression (z-score). <a href="#" className="text-[#8B7CBF] underline decoration-[#D6CDEA]">more information</a>
            </p>

            {transcriptomic.status === "parsed" && transcriptomic.data ? (
              <>
                <div className="flex items-center gap-2 mt-1 mb-2">
                  <FormatBadge label={transcriptomic.format!} success={true} />
                  <span className="text-[0.73rem] text-[#AAAAAA]">{transcriptomic.fileName}</span>
                </div>
                <TablePreview
                  headers={["Gene", "Expression (z-score)"]}
                  rows={transcriptomic.data.slice(0, 5).map(r => [r.gene, r.expression])}
                />
              </>
            ) : (
              <TablePreview
                headers={["Gene", "Expression (z-score)"]}
                rows={[
                  ["COL1A1", "3.14"],
                  ["FAP", "2.87"],
                  ["VIM", "-1.23"],
                ]}
              />
            )}

            {transcriptomic.status === "error" && (
              <Banner type="error" message={transcriptomic.error!} onDismiss={() => setTranscriptomic({ status: "idle" })} />
            )}

            <DropZone accept=".csv,.tsv" hint=".csv or .tsv" onFile={handleTranscriptomicFile} />
          </UploadPanel>

          {/* ── Radiomic ──────────────────────────────────────────────────── */}
          <UploadPanel icon={<ScanIcon />} title="Radiomic Data" badge="(.csv, json, dcm, dcm)">
            <p className="text-[0.78rem] text-[#6B6B6B] mt-1 mb-3">
              DICOM (.dcm) is supported for demonstration only.
            </p>

            {/* DICOM metadata banner */}
            {radiomic.status === "parsed" && dicomMeta && (
              <Banner
                type="info"
                message={`DICOM metadata extracted — Modality: ${dicomMeta.modality ?? "N/A"} · Patient ID: ${dicomMeta.patientId ?? "N/A"}. Radiomic features generated from DICOM (demo mode).`}
                onDismiss={() => setDicomMeta(null)}
              />
            )}

            {radiomic.status === "parsed" && !dicomMeta && radiomic.format && (
              <div className="flex items-center gap-2 mb-2">
                <FormatBadge label={radiomic.format} success={true} />
                <span className="text-[0.73rem] text-[#AAAAAA]">{radiomic.fileName}</span>
              </div>
            )}

            {radiomic.status === "error" && (
              <Banner type="error" message={radiomic.error!} onDismiss={() => setRadiomic({ status: "idle" })} />
            )}

            {/* Sliders */}
            <div className="flex flex-col gap-4 my-4">
              <SliderRow
                icon={<span className="text-[10px] font-bold text-[#8B7CBF]">➤</span>}
                label="Tumor Size"
                value={radiomicSliders.tumor_size}
                min={0.5} max={10} step={0.1} unit=" cm"
                onChange={v => setRadiomicSliders(s => ({ ...s, tumor_size: v }))}
              />
              <SliderRow
                icon={sliderDotIcon("#8B7CBF")}
                label="Heterogeneity"
                value={radiomicSliders.heterogeneity}
                min={0} max={1} step={0.01} unit=""
                onChange={v => setRadiomicSliders(s => ({ ...s, heterogeneity: v }))}
              />
              <SliderRow
                icon={sliderDotIcon("#B3A8D8")}
                label="Necrosis"
                value={radiomicSliders.necrosis}
                min={0} max={1} step={0.01} unit=""
                onChange={v => setRadiomicSliders(s => ({ ...s, necrosis: v }))}
              />
              <SliderRow
                icon={sliderDotIcon("#D6CDEA")}
                label="Edge Sharpness"
                value={radiomicSliders.edge_sharpness}
                min={0} max={1} step={0.01} unit=""
                onChange={v => setRadiomicSliders(s => ({ ...s, edge_sharpness: v }))}
              />
            </div>

            <DropZone accept=".csv,.json,.dcm,.dicom" hint=".csv, .json or .dcm" onFile={handleRadiomicFile} />

            {/* DICOM note */}
            <p className="mt-2 text-[0.72rem] text-[#AAAAAA] text-center">
              DICOM uploads extract patient metadata only — features are generated as mock values in demo mode.
            </p>
          </UploadPanel>
        </div>

        {/* ── Right column: clinical + analyze ──────────────────────────── */}
        <div className="flex flex-col gap-5 sticky top-[84px]">
          <div className="bg-white rounded-2xl border border-[#E5E5E5] shadow-[0_2px_12px_rgba(0,0,0,0.04)] p-6">
            <h2 className="font-playfair font-medium text-[1.05rem] text-[#2E2A2A] mb-5">
              Clinical Information
            </h2>

            <div className="flex flex-col gap-3">
              {/* Age */}
              <div className="flex items-center justify-between">
                <label className="text-[0.82rem] text-[#6B6B6B]">Age</label>
                <input
                  type="number" min={0} max={120} value={clinical.age}
                  onChange={e => setClinical(c => ({ ...c, age: e.target.value }))}
                  className="w-20 text-right text-[0.82rem] font-medium text-[#2E2A2A]
                             border border-[#E5E5E5] rounded-lg px-2.5 py-1.5
                             focus:outline-none focus:border-[#8B7CBF] focus:ring-1 focus:ring-[#D6CDEA]"
                />
              </div>

              {/* Sex */}
              <div className="flex items-center justify-between">
                <label className="text-[0.82rem] text-[#6B6B6B]">Sex</label>
                <select
                  value={clinical.sex}
                  onChange={e => setClinical(c => ({ ...c, sex: e.target.value }))}
                  className="text-[0.82rem] font-medium text-[#2E2A2A] border border-[#E5E5E5] rounded-lg px-2.5 py-1.5
                             focus:outline-none focus:border-[#8B7CBF] bg-white"
                >
                  <option>Female</option><option>Male</option><option>Other</option>
                </select>
              </div>

              {/* Tumor Location */}
              <div className="flex items-center justify-between gap-4">
                <label className="text-[0.82rem] text-[#6B6B6B] shrink-0">Tumor Location</label>
                <input
                  type="text" value={clinical.tumorLocation}
                  onChange={e => setClinical(c => ({ ...c, tumorLocation: e.target.value }))}
                  className="text-right text-[0.82rem] font-medium text-[#2E2A2A] min-w-0 flex-1
                             border border-[#E5E5E5] rounded-lg px-2.5 py-1.5
                             focus:outline-none focus:border-[#8B7CBF] focus:ring-1 focus:ring-[#D6CDEA]"
                />
              </div>

              {/* Tumor Size */}
              <div className="flex items-center justify-between">
                <label className="text-[0.82rem] text-[#6B6B6B]">Tumor Size</label>
                <div className="flex items-center gap-1.5">
                  <input
                    type="number" min={0} max={30} step={0.1} value={clinical.tumorSize}
                    onChange={e => setClinical(c => ({ ...c, tumorSize: e.target.value }))}
                    className="w-16 text-right text-[0.82rem] font-medium text-[#2E2A2A]
                               border border-[#E5E5E5] rounded-lg px-2.5 py-1.5
                               focus:outline-none focus:border-[#8B7CBF] focus:ring-1 focus:ring-[#D6CDEA]"
                  />
                  <span className="text-[0.78rem] text-[#6B6B6B]">cm</span>
                </div>
              </div>

              {/* CA19-9 */}
              <div className="flex items-center justify-between">
                <label className="text-[0.82rem] text-[#6B6B6B]">CA19-9</label>
                <div className="flex items-center gap-1.5">
                  <input
                    type="number" min={0} value={clinical.ca199}
                    onChange={e => setClinical(c => ({ ...c, ca199: e.target.value }))}
                    className="w-20 text-right text-[0.82rem] font-medium text-[#2E2A2A]
                               border border-[#E5E5E5] rounded-lg px-2.5 py-1.5
                               focus:outline-none focus:border-[#8B7CBF] focus:ring-1 focus:ring-[#D6CDEA]"
                  />
                  <span className="text-[0.78rem] text-[#6B6B6B]">U/mL</span>
                </div>
              </div>

              {/* Tumor Stage */}
              <div className="flex items-center justify-between">
                <label className="text-[0.82rem] text-[#6B6B6B]">Tumor Stage</label>
                <span className="text-[0.82rem] font-medium text-[#2E2A2A]">Unknown</span>
              </div>

              {/* ECOG */}
              <div className="flex items-center justify-between">
                <label className="text-[0.82rem] text-[#6B6B6B]">ECOG Status</label>
                <div className="flex gap-1.5">
                  {([1, 2, 3] as EcogStatus[]).map(v => (
                    <button
                      key={v}
                      onClick={() => setClinical(c => ({ ...c, ecog: v }))}
                      className={`w-8 h-8 rounded-lg text-[0.78rem] font-medium border transition-all duration-150
                        ${clinical.ecog === v
                          ? "bg-[#8B7CBF] text-white border-[#8B7CBF]"
                          : "bg-white text-[#6B6B6B] border-[#E5E5E5] hover:border-[#8B7CBF] hover:text-[#8B7CBF]"
                        }`}
                    >
                      {v}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* Research mode notice */}
            <div className="mt-5 rounded-xl bg-[#F8F5F2] border border-[#E5E5E5] px-4 py-3">
              <p className="text-[0.75rem] text-[#6B6B6B] leading-[1.6]">
                In research mode. Not for clinical use — data based on synthetic and public data.
              </p>
            </div>

            {/* Analyze */}
            <button
              onClick={handleAnalyze}
              disabled={analyzing}
              className="mt-5 w-full py-3 rounded-xl bg-[#8B7CBF] text-white font-sans
                         text-[0.88rem] tracking-[0.04em] font-medium
                         transition-all duration-200 hover:bg-[#7A6BAE] hover:-translate-y-px
                         hover:shadow-[0_6px_20px_rgba(139,124,191,0.3)]
                         disabled:opacity-60 disabled:cursor-not-allowed disabled:translate-y-0"
            >
              {analyzing ? (
                <span className="flex items-center justify-center gap-2">
                  <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
                  </svg>
                  Analyzing…
                </span>
              ) : "Analyze"}
            </button>

            {/* Analysis result */}
            {analysisResult && (
              <div className="mt-3 rounded-xl bg-[#F0ECF9] border border-[#D6CDEA] px-4 py-3 text-[0.8rem] text-[#6B4FA0]">
                {analysisResult}
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  )
}
