"use client"

import Link from "next/link"
import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { useResultsStore } from "@/lib/store/useResultsStore"
import type { ResultData } from "./data"
import { RiskCard } from "./RiskCard"
import { ContributionChart } from "./ContributionChart"
import { FeatureBreakdown } from "./FeatureCard"
import { ModalityTabs } from "./ModalityTabs"
import { CalibrationChart } from "./CalibrationChart"

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

function DownloadIcon() {
  return (
    <svg width={15} height={15} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
      <polyline points="7 10 12 15 17 10" />
      <line x1="12" y1="15" x2="12" y2="3" />
    </svg>
  )
}

function FileTextIcon() {
  return (
    <svg width={15} height={15} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
      <polyline points="14 2 14 8 20 8" />
      <line x1="16" y1="13" x2="8" y2="13" />
      <line x1="16" y1="17" x2="8" y2="17" />
      <polyline points="10 9 9 9 8 9" />
    </svg>
  )
}

function ArrowRightIcon() {
  return (
    <svg width={13} height={13} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.2} strokeLinecap="round" strokeLinejoin="round">
      <path d="M5 12h14M12 5l7 7-7 7" />
    </svg>
  )
}

// ─── Background ───────────────────────────────────────────────────────────────

function BgLines() {
  return (
    <div className="fixed inset-0 z-0 pointer-events-none overflow-hidden" aria-hidden>
      <svg viewBox="0 0 1440 900" preserveAspectRatio="xMidYMid slice" className="w-full h-full opacity-[0.06]">
        <defs>
          <linearGradient id="rl1" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#8B7CBF" stopOpacity={0} />
            <stop offset="50%" stopColor="#8B7CBF" stopOpacity={1} />
            <stop offset="100%" stopColor="#8B7CBF" stopOpacity={0} />
          </linearGradient>
        </defs>
        <path d="M -100 500 Q 360 320 720 480 T 1540 400" fill="none" stroke="url(#rl1)" strokeWidth="1.5" />
        <path d="M -100 540 Q 400 340 720 520 T 1540 440" fill="none" stroke="url(#rl1)" strokeWidth="0.8" />
        <path d="M 200 200 Q 520 180 840 210 T 1400 195" fill="none" stroke="url(#rl1)" strokeWidth="0.7" />
      </svg>
    </div>
  )
}

// ─── Navbar ───────────────────────────────────────────────────────────────────

function Navbar() {
  const links = [
    { label: "Home", href: "/" },
    { label: "Analysis", href: "/analysis" },
    { label: "Results", href: "/results" },
    { label: "Sample Data", href: "/sample-data" },
    { label: "About", href: "/about" },
  ]
  return (
    <nav className="sticky top-0 z-50 h-[68px] flex items-center justify-between px-12 bg-[#F8F5F2]/90 backdrop-blur-md border-b border-[#E5E5E5]/60">
      <Link href="/" className="font-playfair font-medium text-[1.2rem] tracking-[0.01em] text-[#2E2A2A] no-underline">
        PancrionDX
      </Link>
      <ul className="flex gap-9 list-none">
        {links.map(({ label, href }) => (
          <li key={label}>
            <Link
              href={href}
              className={`text-[0.85rem] font-normal no-underline tracking-[0.02em] relative transition-colors duration-200
                hover:text-[#2E2A2A] after:content-[''] after:absolute after:bottom-[-3px] after:left-0
                after:h-px after:bg-[#8B7CBF] after:transition-[width] after:duration-200 hover:after:w-full
                ${label === "Results" ? "text-[#2E2A2A] after:w-full" : "text-[#6B6B6B] after:w-0"}`}
            >
              {label}
            </Link>
          </li>
        ))}
      </ul>
      <div className="flex gap-[18px] items-center">
        {[
          { href: "https://github.com/itswkosi", label: "GitHub", Icon: GitHubIcon },
          { href: "https://medium.com/@semilogooketola", label: "Medium", Icon: MediumIcon },
          { href: "https://www.linkedin.com/in/semilogo-oketola/", label: "LinkedIn", Icon: LinkedInIcon },
        ].map(({ href, label, Icon }) => (
          <a key={label} href={href} target="_blank" rel="noopener noreferrer" aria-label={label}
            className="text-[#AAAAAA] transition-colors hover:text-[#2E2A2A] flex items-center">
            <Icon />
          </a>
        ))}
      </div>
    </nav>
  )
}

// ─── Perturbation panel ───────────────────────────────────────────────────────

const PERTURBATIONS = [
  { label: "Remove KRAS mutation", delta: -0.03 },
  { label: "Reduce tumor size", delta: -0.12 },
  { label: "Normalize FAP expression", delta: -0.07 },
]

function PerturbationPanel({ baseScore }: { baseScore: number }) {
  const [applied, setApplied] = useState<string | null>(null)
  const delta = PERTURBATIONS.find(p => p.label === applied)?.delta ?? 0
  const adjusted = Math.max(0, Math.min(1, baseScore + delta))

  return (
    <section>
      <h2 className="font-playfair font-medium text-[1.6rem] text-[#2E2A2A] mb-2 tracking-[-0.01em]">
        Test Model Sensitivity
      </h2>
      <p className="text-[0.82rem] text-[#6B6B6B] mb-5">
        See how adjustments to key inputs impact the prediction.
      </p>

      <div className="bg-white rounded-2xl border border-[#E5E5E5] shadow-[0_2px_12px_rgba(0,0,0,0.04)] p-6">
        <div className="flex flex-wrap gap-2 mb-5">
          {PERTURBATIONS.map(p => (
            <button
              key={p.label}
              onClick={() => setApplied(applied === p.label ? null : p.label)}
              className={`text-[0.8rem] px-4 py-2 rounded-lg border transition-all duration-150 flex items-center gap-1.5
                ${applied === p.label
                  ? "bg-[#8B7CBF] text-white border-[#8B7CBF]"
                  : "bg-white text-[#2E2A2A] border-[#E5E5E5] hover:border-[#8B7CBF] hover:text-[#8B7CBF]"
                }`}
            >
              {p.label}
              {applied !== p.label && <ArrowRightIcon />}
            </button>
          ))}
        </div>

        {applied && (
          <div className="bg-[#F8F5F2] rounded-xl border border-[#EDE7F6] px-5 py-4">
            <div className="flex items-center justify-between mb-3">
              <span className="text-[0.78rem] text-[#6B6B6B]">Adjusted risk score</span>
              <span className="font-playfair font-medium text-[1.4rem] text-[#2E2A2A]">
                {Math.round(adjusted * 100)}%
                <span className="text-[0.78rem] font-sans font-normal text-[#8B7CBF] ml-2">
                  ({delta > 0 ? "+" : ""}{Math.round(delta * 100)}pp)
                </span>
              </span>
            </div>
            <div className="h-2 rounded-full bg-[#EDE7F6] overflow-hidden">
              <div
                className="h-full rounded-full transition-all duration-500"
                style={{
                  width: `${Math.round(adjusted * 100)}%`,
                  background: "linear-gradient(90deg, #C4B8E2 0%, #8B7CBF 100%)",
                }}
              />
            </div>
          </div>
        )}
      </div>
    </section>
  )
}

// ─── Data summary + actions ───────────────────────────────────────────────────

function DataSummary({ data }: { data: ResultData }) {
  function downloadJSON() {
    const payload = {
      sampleId: data.sampleId,
      dateAnalyzed: data.dateAnalyzed,
      riskScore: data.riskScore,
      classification: data.classification,
      confidence: data.confidence,
      brierScore: data.brierScore,
      modalityContributions: data.modalityContributions,
      featureDrivers: data.featureDrivers,
    }
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = `${data.sampleId}-prediction.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <section>
      <div className="bg-white rounded-2xl border border-[#E5E5E5] shadow-[0_2px_12px_rgba(0,0,0,0.04)] p-6">
        <div className="flex items-center justify-between mb-5">
          <h3 className="font-playfair font-medium text-[1.1rem] text-[#2E2A2A]">Data Summary</h3>
          <button
            onClick={downloadJSON}
            className="flex items-center gap-2 text-[0.78rem] font-medium text-[#8B7CBF] px-4 py-2 rounded-lg
                       border border-[#D6CDEA] hover:bg-[#F0ECF9] transition-colors duration-150"
          >
            <DownloadIcon />
            Download JSON
            <ArrowRightIcon />
          </button>
        </div>

        <div className="grid grid-cols-3 gap-4 mb-5">
          {[
            { value: data.genomicVariants.length, label: "Genomic variants", icon: "⬡" },
            { value: data.transcriptomicGenes.length, label: "Transcriptomic genes", icon: "⟿" },
            { value: data.radiomicFeatures.length, label: "Radiomic features", icon: "◉" },
          ].map(item => (
            <div key={item.label} className="bg-[#FDFCFF] rounded-xl border border-[#EDE7F6] px-4 py-3 flex items-start gap-2">
              <span className="text-[#8B7CBF] text-sm mt-0.5">{item.icon}</span>
              <div>
                <span className="font-playfair font-medium text-[1.4rem] text-[#2E2A2A]">{item.value}</span>
                <p className="text-[0.73rem] text-[#6B6B6B]">{item.label}</p>
              </div>
            </div>
          ))}
        </div>

        {/* Clinical row */}
        <div className="flex items-center gap-3 py-3 border-t border-[#F0EDF8]">
          <span className="text-[#8B7CBF] text-[11px]">▣</span>
          <div className="flex gap-4 text-[0.75rem] text-[#6B6B6B]">
            <span>Clinical</span>
            <span className="text-[#AAAAAA]">·</span>
            <span>Age: <strong className="text-[#2E2A2A]">{data.clinicalData.age}</strong></span>
            <span className="text-[#AAAAAA]">·</span>
            <span>CA19-0: <strong className="text-[#2E2A2A]">{data.clinicalData.ca199} u/mL</strong></span>
          </div>
        </div>
        <div className="flex items-center gap-3 py-3 border-t border-[#F0EDF8]">
          <span className="text-[#B3A8D8] text-[11px]">⚠</span>
          <div className="flex gap-4 text-[0.75rem] text-[#6B6B6B]">
            <span>Age: <strong className="text-[#2E2A2A]">{data.clinicalData.age}</strong></span>
            <span className="text-[#AAAAAA]">·</span>
            <span>CA19-0: <strong className="text-[#2E2A2A]">{data.clinicalData.ca199} u/mL</strong></span>
          </div>
        </div>
      </div>

      {/* Action buttons */}
      <div className="grid grid-cols-2 gap-3 mt-3">
        <button
          onClick={downloadJSON}
          className="flex items-center justify-center gap-2 text-[0.82rem] font-medium
                     px-5 py-3 rounded-xl border border-[#E5E5E5] text-[#2E2A2A] bg-white
                     transition-all duration-150 hover:border-[#D6CDEA] hover:text-[#8B7CBF]"
        >
          <DownloadIcon />
          Download JSON
        </button>
        <button
          onClick={() => window.print()}
          className="flex items-center justify-center gap-2 text-[0.82rem] font-medium
                     px-5 py-3 rounded-xl bg-[#8B7CBF] text-white border border-[#8B7CBF]
                     transition-all duration-150 hover:bg-[#7A6BAE] hover:-translate-y-px
                     hover:shadow-[0_6px_20px_rgba(139,124,191,0.3)]"
        >
          <FileTextIcon />
          Generate PDF Report
          <ArrowRightIcon />
        </button>
      </div>
    </section>
  )
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function ResultsPage() {
  const router = useRouter()
  const { results, loadFromStorage } = useResultsStore()

  useEffect(() => {
    loadFromStorage()
  }, [loadFromStorage])

  if (!results) {
    return (
      <div className="min-h-screen bg-[#F8F5F2] flex flex-col items-center justify-center gap-6">
        <p className="font-playfair text-[1.5rem] text-[#2E2A2A]">No analysis results yet.</p>
        <p className="text-[0.88rem] text-[#6B6B6B]">Run an analysis to see your results here.</p>
        <button
          onClick={() => router.push("/analysis")}
          className="px-6 py-3 rounded-xl bg-[#8B7CBF] text-white text-[0.88rem] font-medium
                     hover:bg-[#7A6BAE] transition-colors"
        >
          Go to Analysis
        </button>
      </div>
    )
  }

  const data = results

  return (
    <div className="min-h-screen bg-[#F8F5F2]">
      <BgLines />
      <div className="relative z-10">
        <Navbar />

        <main className="max-w-6xl mx-auto px-8 py-10">

          {/* ── Page header ──────────────────────────────────────────────── */}
          <div className="mb-8">
            <p className="text-[0.72rem] font-medium tracking-[0.22em] uppercase text-[#8B7CBF] mb-2">
              Results
            </p>
            <h1 className="font-playfair font-medium text-[2rem] text-[#2E2A2A] tracking-[-0.02em] mb-1">
              Analysis Results
            </h1>
            <p className="text-[0.88rem] text-[#6B6B6B] mb-4">
              Multimodal PDAC Risk Assessment
            </p>

            {/* Metadata row */}
            <div className="flex flex-wrap gap-4 items-center">
              <span className="text-[0.75rem] text-[#6B6B6B]">
                Sample ID: <strong className="text-[#2E2A2A] font-mono">{data.sampleId}</strong>
              </span>
              <span className="text-[#E5E5E5]">·</span>
              <span className="text-[0.75rem] text-[#6B6B6B]">
                Date: <strong className="text-[#2E2A2A]">{data.dateAnalyzed}</strong>
              </span>
              <span className="text-[#E5E5E5]">·</span>
              <div className="flex gap-1.5">
                {data.modalities.map(m => (
                  <span key={m} className="text-[0.68rem] font-medium tracking-[0.04em] px-2.5 py-1
                                            rounded-full bg-[#F0ECF9] text-[#8B7CBF] border border-[#D6CDEA]">
                    {m}
                  </span>
                ))}
              </div>
            </div>
          </div>

          {/* ── Content grid ──────────────────────────────────────────────── */}
          <div className="flex flex-col gap-8">

            {/* 1. Risk hero */}
            <RiskCard data={data} />

            {/* 2. Contribution chart + calibration side by side */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <ContributionChart data={data} />
              <CalibrationChart data={data} />
            </div>

            {/* 3. Feature breakdown */}
            <FeatureBreakdown features={data.featureDrivers} />

            {/* 4. Modality tabs */}
            <ModalityTabs data={data} />

            {/* 5. Perturbation panel */}
            <PerturbationPanel baseScore={data.riskScore} />

            {/* 6. Data summary + downloads */}
            <DataSummary data={data} />

            {/* Disclaimer */}
            <p className="text-center text-[0.73rem] text-[#AAAAAA] pb-4">
              Proof-of-concept model. Not for clinical use — includes synthetic and public data.
            </p>
          </div>
        </main>
      </div>
    </div>
  )
}
