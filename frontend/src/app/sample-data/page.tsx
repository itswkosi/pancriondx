"use client"

import { useState } from "react"

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

function DownloadIcon({ size = 16 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
      <polyline points="7 10 12 15 17 10" />
      <line x1="12" y1="15" x2="12" y2="3" />
    </svg>
  )
}

function ArrowRightIcon() {
  return (
    <svg width={14} height={14} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
      <path d="M5 12h14M12 5l7 7-7 7" />
    </svg>
  )
}

function CheckIcon() {
  return (
    <svg width={13} height={13} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.2} strokeLinecap="round" strokeLinejoin="round">
      <polyline points="20 6 9 17 4 12" />
    </svg>
  )
}

function ZipIcon() {
  return (
    <svg width={16} height={16} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5z" />
      <polyline points="17 1 17 8 10 8" />
    </svg>
  )
}

// ─── Background lines ─────────────────────────────────────────────────────────

function BgLines() {
  return (
    <div className="fixed inset-0 z-0 pointer-events-none overflow-hidden" aria-hidden>
      <svg viewBox="0 0 1440 900" preserveAspectRatio="xMidYMid slice" xmlns="http://www.w3.org/2000/svg" className="w-full h-full opacity-[0.07]">
        <defs>
          <linearGradient id="bg-lg1" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#C8B6E2" stopOpacity={0} />
            <stop offset="50%" stopColor="#C8B6E2" stopOpacity={1} />
            <stop offset="100%" stopColor="#C8B6E2" stopOpacity={0} />
          </linearGradient>
        </defs>
        <path d="M -100 500 Q 360 320 720 480 T 1540 400" fill="none" stroke="url(#bg-lg1)" strokeWidth="1.5" />
        <path d="M -100 540 Q 400 340 720 520 T 1540 440" fill="none" stroke="url(#bg-lg1)" strokeWidth="0.8" />
        <path d="M -100 460 Q 320 300 720 440 T 1540 360" fill="none" stroke="url(#bg-lg1)" strokeWidth="1" />
        <path d="M 200 200 Q 520 180 840 210 T 1400 195" fill="none" stroke="url(#bg-lg1)" strokeWidth="0.7" />
        <path d="M 100 720 Q 460 700 820 730 T 1500 715" fill="none" stroke="url(#bg-lg1)" strokeWidth="0.7" />
      </svg>
    </div>
  )
}

// ─── Navbar ───────────────────────────────────────────────────────────────────

const NAV_LINKS = [
  { label: "Home", href: "/" },
  { label: "Analysis", href: "/#analysis" },
  { label: "Results", href: "/#results" },
  { label: "Sample Data", href: "/sample-data", active: true },
  { label: "About", href: "/about" },
]

function Navbar() {
  return (
    <nav className="sticky top-0 z-50 h-[68px] flex items-center justify-between px-12 bg-[#F8F5F2]/88 backdrop-blur-md border-b border-[#E5E5EB]/60">
      <a href="/" className="font-playfair font-medium text-[1.2rem] tracking-[0.01em] text-[#2D2A32] no-underline">
        PancrionDX
      </a>
      <ul className="hidden md:flex gap-9 list-none">
        {NAV_LINKS.map(({ label, href, active }) => (
          <li key={label}>
            <a
              href={href}
              className={`text-[0.85rem] font-normal no-underline tracking-[0.02em] relative transition-colors duration-200
                after:content-[''] after:absolute after:bottom-[-3px] after:left-0 after:h-px after:bg-[#8B7CBF] after:transition-[width] after:duration-200
                ${active
                  ? "text-[#2D2A32] after:w-full"
                  : "text-[#6B6B6B] after:w-0 hover:text-[#2D2A32] hover:after:w-full"
                }`}
            >
              {label}
            </a>
          </li>
        ))}
      </ul>
      <div className="flex gap-[18px] items-center">
        {[
          { href: "https://github.com/itswkosi", label: "GitHub", Icon: GitHubIcon },
          { href: "https://medium.com/@semilogooketola", label: "Medium", Icon: MediumIcon },
          { href: "https://www.linkedin.com/in/semilogo-oketola/", label: "LinkedIn", Icon: LinkedInIcon },
        ].map(({ href, label, Icon }) => (
          <a
            key={label}
            href={href}
            target="_blank"
            rel="noopener noreferrer"
            aria-label={label}
            className="text-[#AAAAAA] transition-colors duration-200 hover:text-[#2D2A32]"
          >
            <Icon />
          </a>
        ))}
      </div>
    </nav>
  )
}

// ─── Section wrapper ──────────────────────────────────────────────────────────

function Section({ id, children, className = "" }: { id?: string; children: React.ReactNode; className?: string }) {
  return (
    <section id={id} className={`px-6 py-20 ${className}`}>
      <div className="max-w-6xl mx-auto">{children}</div>
    </section>
  )
}

function Divider() {
  return (
    <div className="flex justify-center px-6">
      <hr className="w-full max-w-6xl border-none h-px bg-[#E5E0EB]" />
    </div>
  )
}

// ─── Hero Section ─────────────────────────────────────────────────────────────

function HeroCardMockup() {
  return (
    <div className="relative h-[340px] flex items-center justify-center select-none">
      {/* Back card — Radiomic */}
      <div
        className="absolute w-[300px] bg-white/60 backdrop-blur-sm border border-[#E5E0EB]
                   rounded-2xl shadow-sm px-6 py-5"
        style={{ transform: "rotate(6deg) translateY(16px) translateX(20px)", opacity: 0.55 }}
      >
        <p className="text-[0.65rem] tracking-[0.14em] uppercase text-[#C8B6E2] mb-3 font-medium">Radiomic Features</p>
        <div className="space-y-2">
          {["Tumor diameter", "Heterogeneity index", "Necrosis ratio"].map((f) => (
            <div key={f} className="flex items-center gap-2">
              <div className="w-1.5 h-1.5 rounded-full bg-[#C8B6E2]" />
              <span className="text-[0.78rem] text-[#6B6B6B]">{f}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Mid card — Transcriptomic */}
      <div
        className="absolute w-[300px] bg-white/75 backdrop-blur-sm border border-[#E5E0EB]
                   rounded-2xl shadow-sm px-6 py-5"
        style={{ transform: "rotate(-3deg) translateY(6px) translateX(-12px)", opacity: 0.72 }}
      >
        <p className="text-[0.65rem] tracking-[0.14em] uppercase text-[#A78BFA] mb-3 font-medium">Transcriptomic Data <span className="normal-case tracking-normal text-[#AAAAAA]">(.csv)</span></p>
        <div className="space-y-2">
          {["COL1A1 — high expression", "FAP — elevated", "KRAS pathway upregulated"].map((f) => (
            <div key={f} className="flex items-center gap-2">
              <div className="w-1.5 h-1.5 rounded-full bg-[#A78BFA]" />
              <span className="text-[0.78rem] text-[#6B6B6B]">{f}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Front card — Genomic */}
      <div
        className="relative w-[300px] bg-white border border-[#E5E0EB]
                   rounded-2xl shadow-[0_4px_24px_rgba(167,139,250,0.10)] px-6 py-5"
      >
        <p className="text-[0.65rem] tracking-[0.14em] uppercase text-[#8B7CBF] mb-3 font-medium">Genomic Data <span className="normal-case tracking-normal text-[#AAAAAA]">(.vcf)</span></p>
        <div className="space-y-2.5">
          {[
            { gene: "KRAS", mut: "G12D", color: "#A78BFA" },
            { gene: "TP53", mut: "R175H", color: "#C8B6E2" },
            { gene: "CDKN2A", mut: "Loss", color: "#D4C5F0" },
          ].map(({ gene, mut, color }) => (
            <div key={gene} className="flex items-center justify-between">
              <span className="text-[0.82rem] font-medium text-[#2D2A32]">{gene}</span>
              <span
                className="text-[0.72rem] px-2.5 py-0.5 rounded-full font-medium"
                style={{ backgroundColor: `${color}22`, color }}
              >
                {mut}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

function HeroSection() {
  return (
    <Section className="pt-24 pb-16">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-16 items-center">
        {/* Left */}
        <div>
          <p className="text-[0.72rem] font-medium tracking-[0.2em] uppercase text-[#8B7CBF] mb-5">
            Sample Dataset
          </p>
          <h1 className="font-playfair font-medium text-[2.6rem] leading-[1.18] tracking-[-0.015em] text-[#2D2A32] mb-6">
            Try PancrionDX with Sample Patient Data
          </h1>
          <p className="text-[0.95rem] text-[#6B6B6B] leading-[1.8] mb-10 max-w-[440px]">
            Download curated genomic, transcriptomic, and radiomic inputs designed to reflect real pancreatic cancer biology.
          </p>
          <div className="flex flex-wrap gap-3">
            <a
              href="/sample-data/genomic/PAAD-SAMPLE-001_mutations.tsv"
              download="PAAD-SAMPLE-001_mutations.tsv"
              className="inline-flex items-center gap-2 font-sans text-[0.875rem] tracking-[0.02em]
                         px-7 py-[13px] rounded-xl bg-[#8B7CBF] text-white border border-[#8B7CBF]
                         transition-all duration-200
                         hover:bg-[#7A6BAE] hover:border-[#7A6BAE] hover:-translate-y-px
                         hover:shadow-[0_6px_20px_rgba(139,124,191,0.22)]"
            >
              <DownloadIcon size={15} />
              Download Sample Dataset
            </a>
            <a
              href="/#analysis"
              className="inline-flex items-center gap-2 font-sans text-[0.875rem] tracking-[0.02em]
                         px-7 py-[13px] rounded-xl bg-transparent text-[#2D2A32]
                         border border-[#E5E0EB]
                         transition-all duration-200
                         hover:border-[#C8B6E2] hover:text-[#8B7CBF] hover:-translate-y-px"
            >
              Go to Analysis Page
              <ArrowRightIcon />
            </a>
          </div>
          <p className="mt-6 text-[0.75rem] text-[#AAAAAA] tracking-[0.03em]">
            All sample data is synthetic but biologically informed. No patient data is used.
          </p>
        </div>

        {/* Right */}
        <div className="flex justify-center md:justify-end">
          <HeroCardMockup />
        </div>
      </div>
    </Section>
  )
}

// ─── What's in the Sample ─────────────────────────────────────────────────────

const SAMPLE_CARDS = [
  {
    title: "Genomic Data",
    ext: ".vcf",
    color: "#8B7CBF",
    bg: "#F3F0FA",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.4} strokeLinecap="round" strokeLinejoin="round" className="w-[22px] h-[22px]">
        <path d="M8 3C8 3 7 8 12 12C17 16 16 21 16 21" />
        <path d="M16 3C16 3 17 8 12 12C7 16 8 21 8 21" />
        <line x1="6.5" y1="7" x2="17.5" y2="7" />
        <line x1="5.5" y1="12" x2="18.5" y2="12" />
        <line x1="6.5" y1="17" x2="17.5" y2="17" />
      </svg>
    ),
    points: [
      "Mutations in core PDAC genes (KRAS, TP53, CDKN2A)",
      "Reflects realistic mutation frequencies and co-occurrence patterns",
      "Formatted as a standard VCF with chromosome coordinates",
      "Includes silent and functional variant examples",
    ],
  },
  {
    title: "Transcriptomic Data",
    ext: ".csv",
    color: "#A78BFA",
    bg: "#F5F2FC",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.4} strokeLinecap="round" strokeLinejoin="round" className="w-[22px] h-[22px]">
        <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
      </svg>
    ),
    points: [
      "Expression values in TPM / log scale",
      "Includes stromal and tumor genes (COL1A1, FAP)",
      "Contains overlapping distributions and biological noise",
      "Simulated to mirror real patient-to-patient variability",
    ],
  },
  {
    title: "Radiomic Features",
    ext: ".csv",
    color: "#C8B6E2",
    bg: "#FAF8FD",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.4} strokeLinecap="round" strokeLinejoin="round" className="w-[22px] h-[22px]">
        <circle cx="12" cy="12" r="8" />
        <circle cx="12" cy="12" r="3" />
        <line x1="12" y1="2" x2="12" y2="5" />
        <line x1="12" y1="19" x2="12" y2="22" />
        <line x1="2" y1="12" x2="5" y2="12" />
        <line x1="19" y1="12" x2="22" y2="12" />
      </svg>
    ),
    points: [
      "Tumor size, heterogeneity index, necrosis ratio",
      "Simulated from known imaging trends in pancreatic tumors",
      "Includes both early-stage and late-stage feature profiles",
      "Normalized to match clinical imaging scale ranges",
    ],
  },
]

function WhatsinSection() {
  return (
    <Section id="whats-in">
      <div className="text-center mb-14">
        <p className="text-[0.72rem] font-medium tracking-[0.2em] uppercase text-[#8B7CBF] mb-4">Data contents</p>
        <h2 className="font-playfair font-medium text-[2rem] tracking-[-0.01em] text-[#2D2A32]">
          What&rsquo;s in the Sample?
        </h2>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {SAMPLE_CARDS.map(({ title, ext, color, bg, icon, points }) => (
          <div
            key={title}
            className="rounded-2xl border border-[#E5E0EB] bg-white px-7 py-7 shadow-sm
                       transition-all duration-200 hover:-translate-y-1 hover:shadow-[0_8px_28px_rgba(167,139,250,0.10)]"
          >
            {/* Header */}
            <div className="flex items-start gap-3 mb-5">
              <div
                className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0"
                style={{ backgroundColor: bg, color }}
              >
                {icon}
              </div>
              <div>
                <h3 className="font-playfair font-medium text-[1rem] text-[#2D2A32] leading-tight">{title}</h3>
                <span className="text-[0.72rem] tracking-[0.06em] text-[#AAAAAA]">{ext}</span>
              </div>
            </div>

            {/* Points */}
            <ul className="space-y-2.5">
              {points.map((pt) => (
                <li key={pt} className="flex items-start gap-2.5">
                  <span className="mt-[3px] flex-shrink-0" style={{ color }}>
                    <CheckIcon />
                  </span>
                  <span className="text-[0.83rem] text-[#6B6B6B] leading-[1.65]">{pt}</span>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
      <p className="text-center text-[0.78rem] text-[#AAAAAA] mt-10 tracking-[0.03em]">
        All sample data is synthetic but biologically informed. No patient data is used.
      </p>
    </Section>
  )
}

// ─── How to Use ───────────────────────────────────────────────────────────────

const STEPS = [
  { num: "01", label: "Download dataset", sub: "Get the full .zip or individual files" },
  { num: "02", label: "Go to analysis page", sub: "Navigate to the PancrionDX tool" },
  { num: "03", label: "Upload your files", sub: "Drop in genomic, transcriptomic, radiomic inputs" },
  { num: "04", label: "View prediction", sub: "Review stage classification and interpretation" },
]

const GENOMIC_ROWS = [
  { gene: "KRAS",   mutation: "p.G12V",    type: "Missense",      impact: "High",     vaf: "0.48", patient: "001" },
  { gene: "TP53",   mutation: "p.R248W",   type: "Missense",      impact: "High",     vaf: "0.44", patient: "001" },
  { gene: "SMAD4",  mutation: "p.R361*",   type: "Nonsense",      impact: "High",     vaf: "0.39", patient: "001" },
  { gene: "CDKN2A", mutation: "p.R58*",    type: "Missense",      impact: "High",     vaf: "0.35", patient: "001" },
  { gene: "RNF43",  mutation: "p.G659fs",  type: "Frameshift Del",impact: "High",     vaf: "0.21", patient: "001" },
  { gene: "BRAF",   mutation: "p.V600E",   type: "Missense",      impact: "High",     vaf: "0.51", patient: "002" },
  { gene: "GNAS",   mutation: "p.R201H",   type: "Missense",      impact: "Moderate", vaf: "0.38", patient: "002" },
  { gene: "KRAS",   mutation: "p.G12D",    type: "Missense",      impact: "High",     vaf: "0.52", patient: "003" },
]

const TRANSCRIPTOMIC_ROWS = [
  { patient: "PAAD-001", subtype: "Basal-like", rasScore: "8.7", emtScore: "7.4", purity: "0.74", risk: "High" },
  { patient: "PAAD-002", subtype: "Classical",  rasScore: "7.2", emtScore: "2.8", purity: "0.68", risk: "High" },
  { patient: "PAAD-003", subtype: "Classical",  rasScore: "3.4", emtScore: "1.2", purity: "0.51", risk: "Low-Mod" },
  { patient: "PAAD-004", subtype: "Basal-like", rasScore: "9.8", emtScore: "9.6", purity: "0.83", risk: "Very High" },
]

const RADIOMIC_ROWS = [
  { patientId: "C3N-03039", slices: "234", thickness: "1.25 mm", snr: "481.6",  score: "12.00" },
  { patientId: "C3L-02118", slices: "351", thickness: "1.25 mm", snr: "1153.0", score: "12.00" },
  { patientId: "C3N-03670", slices: "520", thickness: "1.00 mm", snr: "480.5",  score: "12.00" },
  { patientId: "C3L-03743", slices: "106", thickness: "2.50 mm", snr: "1173.1", score: "10.59" },
  { patientId: "C3L-05754", slices: "65",  thickness: "5.00 mm", snr: "1164.0", score: "9.97"  },
]

type TabKey = "genomic" | "transcriptomic" | "radiomic"

function HowToUseSection() {
  const [activeTab, setActiveTab] = useState<TabKey>("genomic")

  return (
    <Section id="how-to-use" className="bg-[#FDFBFF]/60">
      <div className="text-center mb-14">
        <p className="text-[0.72rem] font-medium tracking-[0.2em] uppercase text-[#8B7CBF] mb-4">Quickstart guide</p>
        <h2 className="font-playfair font-medium text-[2rem] tracking-[-0.01em] text-[#2D2A32]">
          How to Use the Sample Data
        </h2>
      </div>

      {/* Steps */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-16">
        {STEPS.map(({ num, label, sub }, i) => (
          <div key={num} className="relative">
            {/* Connector line */}
            {i < STEPS.length - 1 && (
              <div className="hidden md:block absolute top-5 left-[calc(100%-8px)] w-8 h-px bg-[#E5E0EB] z-10" />
            )}
            <div className="rounded-2xl border border-[#E5E0EB] bg-white px-5 py-5 shadow-sm">
              <span className="text-[0.65rem] font-semibold tracking-[0.18em] text-[#C8B6E2] mb-2 block">{num}</span>
              <p className="text-[0.88rem] font-medium text-[#2D2A32] leading-tight mb-1">{label}</p>
              <p className="text-[0.78rem] text-[#AAAAAA] leading-[1.5]">{sub}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Tabs */}
      <div className="rounded-2xl border border-[#E5E0EB] bg-white shadow-sm overflow-hidden">
        {/* Tab bar */}
        <div className="flex border-b border-[#E5E0EB] px-6 pt-2">
          {(["genomic", "transcriptomic", "radiomic"] as TabKey[]).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-5 py-3 text-[0.83rem] font-medium tracking-[0.02em] capitalize transition-all duration-150 border-b-2 mr-1
                ${activeTab === tab
                  ? "border-[#8B7CBF] text-[#8B7CBF]"
                  : "border-transparent text-[#AAAAAA] hover:text-[#6B6B6B]"
                }`}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </div>

        {/* Table */}
        <div className="overflow-x-auto px-6 py-5">
          {activeTab === "genomic" && (
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left">
                  <th className="pb-3 text-[0.72rem] tracking-[0.12em] uppercase text-[#AAAAAA] font-medium pr-6">Gene</th>
                  <th className="pb-3 text-[0.72rem] tracking-[0.12em] uppercase text-[#AAAAAA] font-medium pr-6">HGVSp</th>
                  <th className="pb-3 text-[0.72rem] tracking-[0.12em] uppercase text-[#AAAAAA] font-medium pr-6">Type</th>
                  <th className="pb-3 text-[0.72rem] tracking-[0.12em] uppercase text-[#AAAAAA] font-medium pr-6">VAF</th>
                  <th className="pb-3 text-[0.72rem] tracking-[0.12em] uppercase text-[#AAAAAA] font-medium">Patient</th>
                </tr>
              </thead>
              <tbody>
                {GENOMIC_ROWS.map((row, i) => (
                  <tr key={`${row.gene}-${row.patient}`} className={`border-t border-[#F0ECF9] ${i % 2 === 0 ? "bg-white" : "bg-[#FDFBFF]"}`}>
                    <td className="py-3 pr-6 text-[0.85rem] font-semibold text-[#2D2A32]">{row.gene}</td>
                    <td className="py-3 pr-6">
                      <span className="bg-[#A78BFA]/10 text-[#8B7CBF] px-2 py-0.5 rounded-md font-medium text-[0.8rem]">{row.mutation}</span>
                    </td>
                    <td className="py-3 pr-6 text-[0.82rem] text-[#6B6B6B]">{row.type}</td>
                    <td className="py-3 pr-6 text-[0.82rem] font-medium text-[#2D2A32]">{row.vaf}</td>
                    <td className="py-3">
                      <span className="bg-[#F3F0FA] text-[#8B7CBF] px-2 py-0.5 rounded-md text-[0.75rem] font-medium">PAAD-{row.patient}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          {activeTab === "transcriptomic" && (
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left">
                  <th className="pb-3 text-[0.72rem] tracking-[0.12em] uppercase text-[#AAAAAA] font-medium pr-6">Patient</th>
                  <th className="pb-3 text-[0.72rem] tracking-[0.12em] uppercase text-[#AAAAAA] font-medium pr-6">Subtype</th>
                  <th className="pb-3 text-[0.72rem] tracking-[0.12em] uppercase text-[#AAAAAA] font-medium pr-6">RAS Score</th>
                  <th className="pb-3 text-[0.72rem] tracking-[0.12em] uppercase text-[#AAAAAA] font-medium pr-6">EMT Score</th>
                  <th className="pb-3 text-[0.72rem] tracking-[0.12em] uppercase text-[#AAAAAA] font-medium pr-6">Purity</th>
                  <th className="pb-3 text-[0.72rem] tracking-[0.12em] uppercase text-[#AAAAAA] font-medium">Risk</th>
                </tr>
              </thead>
              <tbody>
                {TRANSCRIPTOMIC_ROWS.map((row, i) => (
                  <tr key={row.patient} className={`border-t border-[#F0ECF9] ${i % 2 === 0 ? "bg-white" : "bg-[#FDFBFF]"}`}>
                    <td className="py-3 pr-6 text-[0.82rem] font-semibold text-[#2D2A32]">{row.patient}</td>
                    <td className="py-3 pr-6">
                      <span className={`px-2 py-0.5 rounded-md text-[0.75rem] font-medium ${row.subtype === "Basal-like" ? "bg-[#FCE7F3] text-[#DB2777]" : "bg-[#EDE9FE] text-[#7C3AED]"}`}>{row.subtype}</span>
                    </td>
                    <td className="py-3 pr-6 text-[0.82rem] text-[#6B6B6B]">{row.rasScore}</td>
                    <td className="py-3 pr-6 text-[0.82rem] text-[#6B6B6B]">{row.emtScore}</td>
                    <td className="py-3 pr-6 text-[0.82rem] text-[#6B6B6B]">{row.purity}</td>
                    <td className="py-3">
                      <span className={`px-2 py-0.5 rounded-md text-[0.75rem] font-medium ${
                        row.risk === "Very High" ? "bg-red-50 text-red-600" :
                        row.risk === "High" ? "bg-[#FEF3C7] text-[#D97706]" :
                        "bg-green-50 text-green-700"
                      }`}>{row.risk}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          {activeTab === "radiomic" && (
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left">
                  <th className="pb-3 text-[0.72rem] tracking-[0.12em] uppercase text-[#AAAAAA] font-medium pr-6">Patient ID</th>
                  <th className="pb-3 text-[0.72rem] tracking-[0.12em] uppercase text-[#AAAAAA] font-medium pr-6">Slices</th>
                  <th className="pb-3 text-[0.72rem] tracking-[0.12em] uppercase text-[#AAAAAA] font-medium pr-6">Thickness</th>
                  <th className="pb-3 text-[0.72rem] tracking-[0.12em] uppercase text-[#AAAAAA] font-medium pr-6">SNR Proxy</th>
                  <th className="pb-3 text-[0.72rem] tracking-[0.12em] uppercase text-[#AAAAAA] font-medium">Quality Score</th>
                </tr>
              </thead>
              <tbody>
                {RADIOMIC_ROWS.map((row, i) => (
                  <tr key={row.patientId} className={`border-t border-[#F0ECF9] ${i % 2 === 0 ? "bg-white" : "bg-[#FDFBFF]"}`}>
                    <td className="py-3 pr-6 text-[0.82rem] font-semibold text-[#2D2A32]">{row.patientId}</td>
                    <td className="py-3 pr-6 text-[0.82rem] text-[#6B6B6B]">{row.slices}</td>
                    <td className="py-3 pr-6 text-[0.82rem] text-[#6B6B6B]">{row.thickness}</td>
                    <td className="py-3 pr-6 text-[0.82rem] font-medium text-[#8B7CBF]">{row.snr}</td>
                    <td className="py-3">
                      <span className={`px-2 py-0.5 rounded-md text-[0.75rem] font-medium ${parseFloat(row.score) >= 12 ? "bg-green-50 text-green-700" : "bg-[#FEF3C7] text-[#D97706]"}`}>{row.score}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        <div className="px-6 pb-5">
          <p className="text-[0.74rem] text-[#AAAAAA] tracking-[0.03em]">
            Showing a preview of the sample dataset. Download the full file for complete records.
          </p>
        </div>
      </div>
    </Section>
  )
}

// ─── Download Panel ───────────────────────────────────────────────────────────

const DOWNLOAD_FILES = [
  {
    label: "Download Genomic Data",
    ext: ".tsv — mutations · PAAD-SAMPLE-001",
    href: "/sample-data/genomic/PAAD-SAMPLE-001_mutations.tsv",
    download: "PAAD-SAMPLE-001_mutations.tsv",
    icon: <DownloadIcon />,
    primary: true,
  },
  {
    label: "Download Transcriptomic Data",
    ext: ".tsv — expression · PAAD-SAMPLE-001",
    href: "/sample-data/transcriptomic/PAAD-SAMPLE-001_transcriptomics.tsv",
    download: "PAAD-SAMPLE-001_transcriptomics.tsv",
    icon: <DownloadIcon />,
    primary: false,
  },
  {
    label: "Download Radiomic Sample",
    ext: ".dcm — CT scan DICOM slice · C3L-02118",
    href: "/sample-data/radiomic/C3L-02118/1-001.dcm",
    download: "1-001.dcm",
    icon: <DownloadIcon />,
    primary: false,
  },
]

const EXTRA_SAMPLES = [
  {
    label: "Early-stage sample (PAAD-003)",
    desc: "Stage IB · Classical subtype · Low-Moderate risk · best prognosis of cohort",
    href: "/sample-data/genomic/PAAD-SAMPLE-003_mutations.tsv",
    download: "PAAD-SAMPLE-003_mutations.tsv",
  },
  {
    label: "Late-stage sample (PAAD-004)",
    desc: "Stage IV · Basal-like · Very High risk · full EMT + immune evasion signature",
    href: "/sample-data/genomic/PAAD-SAMPLE-004_mutations.tsv",
    download: "PAAD-SAMPLE-004_mutations.tsv",
  },
]

function DownloadSection() {
  return (
    <Section id="download">
      <div className="text-center mb-14">
        <p className="text-[0.72rem] font-medium tracking-[0.2em] uppercase text-[#8B7CBF] mb-4">Files</p>
        <h2 className="font-playfair font-medium text-[2rem] tracking-[-0.01em] text-[#2D2A32]">
          Download the Dataset
        </h2>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-10 items-start">
        {/* LEFT — preview */}
        <div className="rounded-2xl border border-[#E5E0EB] bg-white shadow-sm overflow-hidden">
          <div className="px-6 pt-6 pb-3 border-b border-[#F0ECF9]">
            <p className="text-[0.72rem] tracking-[0.12em] uppercase text-[#AAAAAA] font-medium">Genomic preview</p>
          </div>
          <div className="overflow-x-auto px-6 py-4">
            <table className="w-full text-sm">
              <thead>
                <tr>
                  <th className="pb-3 text-left text-[0.72rem] tracking-[0.12em] uppercase text-[#AAAAAA] font-medium pr-6">Gene</th>
                  <th className="pb-3 text-left text-[0.72rem] tracking-[0.12em] uppercase text-[#AAAAAA] font-medium pr-6">Mutation</th>
                  <th className="pb-3 text-left text-[0.72rem] tracking-[0.12em] uppercase text-[#AAAAAA] font-medium">Pattern</th>
                </tr>
              </thead>
              <tbody>
                {[
                  { gene: "KRAS",   mutation: "p.G12V",  bars: [0.9, 0.8, 0.95] },
                  { gene: "TP53",   mutation: "p.R248W", bars: [0.7, 0.6, 0.75] },
                  { gene: "SMAD4",  mutation: "p.R361*", bars: [0.6, 0.55, 0.65] },
                  { gene: "CDKN2A", mutation: "p.R58*",  bars: [0.5, 0.55, 0.45] },
                ].map((row, i) => (
                  <tr key={row.gene} className={`border-t border-[#F0ECF9] ${i % 2 === 0 ? "" : "bg-[#FDFBFF]"}`}>
                    <td className="py-3 pr-6 text-[0.85rem] font-semibold text-[#2D2A32]">{row.gene}</td>
                    <td className="py-3 pr-6">
                      <span className="bg-[#A78BFA]/10 text-[#8B7CBF] px-2 py-0.5 rounded-md font-medium text-[0.8rem]">{row.mutation}</span>
                    </td>
                    <td className="py-3">
                      <div className="flex gap-1">
                        {row.bars.map((w, j) => (
                          <div key={j} className="h-4 rounded-sm bg-[#E5E0EB]" style={{ width: `${w * 20}px` }}>
                            <div className="h-full rounded-sm bg-[#C8B6E2]" style={{ width: `${w * 100}%` }} />
                          </div>
                        ))}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="px-6 pb-5 pt-2 border-t border-[#F0ECF9]">
            <p className="text-[0.73rem] text-[#AAAAAA]">
              Showing 4 of 30 variants across 4 patients · Last updated April 2024
            </p>
          </div>
        </div>

        {/* RIGHT — download buttons */}
        <div className="flex flex-col gap-4">
          {DOWNLOAD_FILES.map(({ label, ext, primary, icon, href, download }) => (
            <a
              key={label}
              href={href}
              download={download}
              className={`w-full flex items-center gap-4 px-6 py-4 rounded-2xl border transition-all duration-200 text-left no-underline
                ${primary
                  ? "bg-[#8B7CBF] border-[#8B7CBF] text-white hover:bg-[#7A6BAE] hover:border-[#7A6BAE] hover:-translate-y-px hover:shadow-[0_6px_20px_rgba(139,124,191,0.22)]"
                  : "bg-white border-[#E5E0EB] text-[#2D2A32] hover:border-[#C8B6E2] hover:-translate-y-px hover:shadow-sm"
                }`}
            >
              <span className={primary ? "text-white/80" : "text-[#8B7CBF]"}>{icon}</span>
              <div className="flex-1">
                <p className={`text-[0.87rem] font-medium ${primary ? "text-white" : "text-[#2D2A32]"}`}>{label}</p>
                <p className={`text-[0.75rem] ${primary ? "text-white/65" : "text-[#AAAAAA]"}`}>{ext}</p>
              </div>
              <DownloadIcon size={14} />
            </a>
          ))}

          {/* Extras */}
          <div className="mt-2 border-t border-[#E5E0EB] pt-5 space-y-3">
            <p className="text-[0.72rem] tracking-[0.12em] uppercase text-[#AAAAAA] font-medium mb-4">Individual samples</p>
            {EXTRA_SAMPLES.map(({ label, desc, href, download }) => (
              <a
                key={label}
                href={href}
                download={download}
                className="w-full flex items-start gap-3 px-5 py-4 rounded-xl border border-[#E5E0EB]
                           bg-white text-left no-underline transition-all duration-200
                           hover:border-[#C8B6E2] hover:-translate-y-px hover:shadow-sm"
              >
                <span className="mt-0.5 text-[#C8B6E2]"><DownloadIcon size={14} /></span>
                <div>
                  <p className="text-[0.84rem] font-medium text-[#2D2A32]">{label}</p>
                  <p className="text-[0.76rem] text-[#AAAAAA] leading-[1.5] mt-0.5">{desc}</p>
                </div>
              </a>
            ))}
          </div>

          <p className="text-right text-[0.74rem] text-[#AAAAAA] tracking-[0.03em] pt-1">
            Last updated April 2024
          </p>
        </div>
      </div>
    </Section>
  )
}

// ─── Why This Matters ─────────────────────────────────────────────────────────

function WhySection() {
  return (
    <Section id="why">
      <div className="max-w-[680px] mx-auto text-center">
        <p className="text-[0.72rem] font-medium tracking-[0.2em] uppercase text-[#8B7CBF] mb-5">
          Clinical context
        </p>
        <h2 className="font-playfair font-medium text-[2rem] tracking-[-0.01em] text-[#2D2A32] mb-7">
          Why This Matters
        </h2>
        <p className="text-[0.95rem] text-[#6B6B6B] leading-[1.9]">
          Pancreatic ductal adenocarcinoma is often diagnosed late, when treatment options are limited.
          Tools that integrate multiple biological signals — genomic mutations, transcriptomic expression,
          and imaging features — may help identify risk patterns earlier and more accurately. This sample
          dataset is a starting point for exploring how those signals interact.
        </p>

        <div className="mt-12 grid grid-cols-3 gap-6">
          {[
            { val: "< 5%", label: "Five-year survival rate for late-stage PDAC" },
            { val: "3×", label: "Earlier detection window with multimodal integration" },
            { val: "30", label: "Somatic variant records across 4 sample patients" },
          ].map(({ val, label }) => (
            <div key={label} className="rounded-2xl border border-[#E5E0EB] bg-white px-5 py-6 shadow-sm">
              <p className="font-playfair text-[1.9rem] text-[#8B7CBF] font-medium mb-2">{val}</p>
              <p className="text-[0.78rem] text-[#AAAAAA] leading-[1.5]">{label}</p>
            </div>
          ))}
        </div>

        <div className="mt-12 flex flex-wrap gap-3 justify-center">
          <a
            href="/sample-data/genomic/PAAD-SAMPLE-001_mutations.tsv"
            download="PAAD-SAMPLE-001_mutations.tsv"
            className="inline-flex items-center gap-2 font-sans text-[0.875rem] tracking-[0.02em]
                       px-7 py-[13px] rounded-xl bg-[#8B7CBF] text-white border border-[#8B7CBF]
                       transition-all duration-200
                       hover:bg-[#7A6BAE] hover:-translate-y-px hover:shadow-[0_6px_20px_rgba(139,124,191,0.22)]"
          >
            <DownloadIcon size={15} />
            Download the Dataset
          </a>
          <a
            href="/#analysis"
            className="inline-flex items-center gap-2 font-sans text-[0.875rem] tracking-[0.02em]
                       px-7 py-[13px] rounded-xl bg-transparent text-[#8B7CBF]
                       border border-[#C8B6E2]
                       transition-all duration-200
                       hover:bg-[#8B7CBF]/[0.06] hover:-translate-y-px"
          >
            Explore the Analysis
            <ArrowRightIcon />
          </a>
        </div>
      </div>
    </Section>
  )
}

// ─── Footer ───────────────────────────────────────────────────────────────────

function Footer() {
  return (
    <footer className="border-t border-[#E5E0EB] px-12 py-8">
      <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <span className="font-playfair font-medium text-[1rem] text-[#2D2A32]">PancrionDX</span>
          <span className="text-[#E5E0EB]">·</span>
          <span className="text-[0.78rem] text-[#AAAAAA]">Multimodal PDAC analysis</span>
        </div>
        <div className="flex gap-6 items-center">
          {[
            { href: "https://github.com/itswkosi", label: "GitHub", Icon: GitHubIcon },
            { href: "https://medium.com/@semilogooketola", label: "Medium", Icon: MediumIcon },
            { href: "https://www.linkedin.com/in/semilogo-oketola/", label: "LinkedIn", Icon: LinkedInIcon },
          ].map(({ href, label, Icon }) => (
            <a
              key={label}
              href={href}
              target="_blank"
              rel="noopener noreferrer"
              aria-label={label}
              className="text-[#CCCCCC] hover:text-[#8B7CBF] transition-colors duration-200"
            >
              <Icon />
            </a>
          ))}
        </div>
      </div>
    </footer>
  )
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function SampleDataPage() {
  return (
    <>
      <BgLines />
      <div className="relative z-10 min-h-screen flex flex-col">
        <Navbar />

        <main className="flex-1">
          <HeroSection />
          <Divider />
          <WhatsinSection />
          <Divider />
          <HowToUseSection />
          <Divider />
          <DownloadSection />
          <Divider />
          <WhySection />
        </main>

        <Footer />
      </div>
    </>
  )
}
