"use client"

import { type ReactElement } from "react"
import { Typewriter } from "@/components/ui/typewriter"

// ─── Icons ────────────────────────────────────────────────────────────────────

function GitHubIcon() {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.6}
      strokeLinecap="round"
      strokeLinejoin="round"
      className="w-[18px] h-[18px]"
    >
      <path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22" />
    </svg>
  )
}

function MediumIcon() {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="currentColor"
      stroke="none"
      className="w-[18px] h-[18px]"
    >
      <path d="M13.54 12a6.8 6.8 0 0 1-6.77 6.82A6.8 6.8 0 0 1 0 12a6.8 6.8 0 0 1 6.77-6.82A6.8 6.8 0 0 1 13.54 12zm7.42 0c0 3.54-1.51 6.42-3.38 6.42-1.87 0-3.39-2.88-3.39-6.42s1.52-6.42 3.39-6.42 3.38 2.88 3.38 6.42M24 12c0 3.17-.53 5.75-1.19 5.75-.66 0-1.19-2.58-1.19-5.75s.53-5.75 1.19-5.75C23.47 6.25 24 8.83 24 12z" />
    </svg>
  )
}

function LinkedInIcon() {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.6}
      strokeLinecap="round"
      strokeLinejoin="round"
      className="w-[18px] h-[18px]"
    >
      <path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6z" />
      <rect x="2" y="9" width="4" height="12" />
      <circle cx="4" cy="4" r="2" />
    </svg>
  )
}

// ─── Modality card icons ───────────────────────────────────────────────────────

function DnaIcon() {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.4}
      strokeLinecap="round"
      strokeLinejoin="round"
      className="w-[52px] h-[52px]"
    >
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
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.4}
      strokeLinecap="round"
      strokeLinejoin="round"
      className="w-[52px] h-[52px]"
    >
      <polyline points="2 12 5 6 8 14 11 9 14 15 17 10 20 12 22 12" />
    </svg>
  )
}

function ImagingIcon() {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.4}
      strokeLinecap="round"
      strokeLinejoin="round"
      className="w-[52px] h-[52px]"
    >
      <circle cx="12" cy="12" r="9" />
      <circle cx="12" cy="12" r="4" />
      <line x1="12" y1="3" x2="12" y2="8" />
      <line x1="12" y1="16" x2="12" y2="21" />
      <line x1="3" y1="12" x2="8" y2="12" />
      <line x1="16" y1="12" x2="21" y2="12" />
    </svg>
  )
}

// ─── Background SVG ────────────────────────────────────────────────────────────

function BgLines() {
  return (
    <div className="fixed inset-0 z-0 pointer-events-none overflow-hidden" aria-hidden>
      <svg
        viewBox="0 0 1440 900"
        preserveAspectRatio="xMidYMid slice"
        xmlns="http://www.w3.org/2000/svg"
        className="w-full h-full opacity-[0.09]"
      >
        <defs>
          <linearGradient id="lg1" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#8B7CBF" stopOpacity={0} />
            <stop offset="50%" stopColor="#8B7CBF" stopOpacity={1} />
            <stop offset="100%" stopColor="#8B7CBF" stopOpacity={0} />
          </linearGradient>
          <linearGradient id="lg2" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#D6CDEA" stopOpacity={0} />
            <stop offset="50%" stopColor="#D6CDEA" stopOpacity={1} />
            <stop offset="100%" stopColor="#D6CDEA" stopOpacity={0} />
          </linearGradient>
        </defs>
        <path d="M -100 500 Q 360 320 720 480 T 1540 400" fill="none" stroke="url(#lg1)" strokeWidth="1.5" />
        <path d="M -100 540 Q 400 340 720 520 T 1540 440" fill="none" stroke="url(#lg1)" strokeWidth="0.8" />
        <path d="M -100 460 Q 320 300 720 440 T 1540 360" fill="none" stroke="url(#lg2)" strokeWidth="1" />
        <path d="M -100 580 Q 500 360 720 560 T 1540 480" fill="none" stroke="url(#lg2)" strokeWidth="0.6" />
        <path d="M -100 420 Q 280 260 720 400 T 1540 320" fill="none" stroke="url(#lg1)" strokeWidth="0.5" />
        <path d="M 200 200 Q 520 180 840 210 T 1400 195" fill="none" stroke="url(#lg2)" strokeWidth="0.7" />
        <path d="M 100 720 Q 460 700 820 730 T 1500 715" fill="none" stroke="url(#lg2)" strokeWidth="0.7" />
      </svg>
    </div>
  )
}

// ─── Navigation ───────────────────────────────────────────────────────────────

const NAV_LINKS = [
  { label: "Home", href: "#" },
  { label: "Analysis", href: "/analysis" },
  { label: "Results", href: "#results" },
  { label: "Sample Data", href: "/sample-data" },
  { label: "About", href: "/about" },
]

function Navbar() {
  return (
    <nav className="sticky top-0 z-50 h-[68px] flex items-center justify-between px-12 bg-[#F8F5F2]/88 backdrop-blur-md border-b border-[#E5E5E5]/60">
      <a
        href="#"
        className="font-playfair font-medium text-[1.2rem] tracking-[0.01em] text-[#2E2A2A] no-underline"
      >
        PancrionDX
      </a>

      <ul className="flex gap-9 list-none">
        {NAV_LINKS.map(({ label, href }) => (
          <li key={label}>
            <a
              href={href}
              className="text-[0.85rem] font-normal text-[#6B6B6B] no-underline tracking-[0.02em]
                         relative transition-colors duration-200
                         hover:text-[#2E2A2A]
                         after:content-[''] after:absolute after:bottom-[-3px] after:left-0
                         after:w-0 after:h-px after:bg-[#8B7CBF]
                         after:transition-[width] after:duration-200
                         hover:after:w-full
                         first:text-[#2E2A2A] first:after:w-full"
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
            className="text-[#AAAAAA] transition-colors duration-200 hover:text-[#2E2A2A] flex items-center"
          >
            <Icon />
          </a>
        ))}
      </div>
    </nav>
  )
}

// ─── Modality Card ─────────────────────────────────────────────────────────────

interface CardProps {
  Icon: () => ReactElement
  title: string
  subtitle: string
}

function ModalityCard({ Icon, title, subtitle }: CardProps) {
  return (
    <div
      className="bg-white border border-[#E5E5E5] rounded-xl
                 shadow-[0_4px_12px_rgba(0,0,0,0.05)]
                 px-9 py-10 flex flex-col items-center text-center
                 flex-1 min-w-[210px] max-w-[260px]
                 transition-all duration-200
                 hover:-translate-y-[5px] hover:shadow-[0_12px_28px_rgba(0,0,0,0.08)]"
    >
      <div className="text-[#8B7CBF] mb-5">
        <Icon />
      </div>
      <h2 className="font-playfair font-medium text-[1.1rem] text-[#2E2A2A] mb-1.5">
        {title}
      </h2>
      <p className="text-[0.8rem] text-[#6B6B6B] tracking-[0.04em]">{subtitle}</p>
    </div>
  )
}

// ─── Page ─────────────────────────────────────────────────────────────────────

/**
 * The Typewriter animates the "Pancreatic Cancer Progression" portion of the
 * hero title, cycling through related stage-progression phrases in lavender
 * to visually separate it from the static leading text.
 */
export default function Home() {
  return (
    <>
      <BgLines />

      <div className="relative z-10">
        {/* Navigation */}
        <Navbar />

        {/* Hero */}
        <section
          id="home"
          aria-label="Hero"
          className="flex flex-col items-center justify-center text-center
                     px-6 pt-[120px] pb-24 min-h-[calc(100vh-68px)]"
        >
          {/* Eyebrow */}
          <p className="text-[0.72rem] font-medium tracking-[0.22em] uppercase text-[#8B7CBF] mb-7">
            PancrionDX
          </p>

          {/* Title — static prefix + lavender typewriter for progression phrase */}
          <h1
            className="font-playfair font-medium leading-[1.22] text-[#2E2A2A]
                       max-w-[700px] tracking-[-0.01em] mb-6"
            style={{ fontSize: "clamp(2.4rem, 5vw, 3.6rem)" }}
          >
            Multimodal Analysis of{" "}
            <Typewriter
              text={[
                "Pancreatic Cancer Progression",
                "Early vs Late-Stage PDAC",
                "Genomic, Transcriptomic & Radiomic Signatures",
              ]}
              speed={55}
              deleteSpeed={32}
              waitTime={2400}
              initialDelay={600}
              loop={false}
              cursorChar="│"
              cursorClassName="ml-1 text-[#8B7CBF] font-light"
              className="text-[#8B7CBF]"
            />
          </h1>

          {/* Subtitle */}
          <p className="text-base font-light text-[#6B6B6B] max-w-[520px] leading-[1.7] mb-[52px] tracking-[0.01em]">
            Integrating genomic, transcriptomic, and radiomic data to understand
            early vs late-stage pancreatic ductal adenocarcinoma(PDAC).
          </p>

          {/* Buttons */}
          <div className="flex gap-4 flex-wrap justify-center">
            <a
              href="/analysis"
              className="inline-flex items-center gap-2 font-sans text-[0.875rem] tracking-[0.03em]
                         px-8 py-[13px] rounded-lg bg-[#8B7CBF] text-white border-[1.5px] border-[#8B7CBF]
                         transition-all duration-200
                         hover:bg-[#7A6BAE] hover:border-[#7A6BAE] hover:-translate-y-px
                         hover:shadow-[0_6px_20px_rgba(139,124,191,0.25)]"
            >
              Try It Yourself
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
                <path d="M5 12h14M12 5l7 7-7 7" />
              </svg>
            </a>
            <a
              href="#results"
              className="inline-flex items-center font-sans text-[0.875rem] tracking-[0.03em]
                         px-8 py-[13px] rounded-lg bg-transparent text-[#2E2A2A]
                         border-[1.5px] border-[#E5E5E5]
                         transition-all duration-200
                         hover:border-[#D6CDEA] hover:text-[#8B7CBF] hover:-translate-y-px"
            >
              View Findings
            </a>
          </div>
        </section>

        {/* Modality Cards */}
        <section
          id="analysis"
          aria-label="Data modalities"
          className="flex flex-col items-center px-6 pb-24"
        >
          <div className="flex gap-6 justify-center flex-wrap max-w-[860px] w-full">
            <ModalityCard Icon={DnaIcon} title="Genomics" subtitle="Mutations" />
            <ModalityCard Icon={WaveformIcon} title="Transcriptomics" subtitle="Gene Expression" />
            <ModalityCard Icon={ImagingIcon} title="Radiomics" subtitle="Tumor Imaging" />
          </div>
        </section>

        {/* Quote */}
        <section
          aria-label="Key insight"
          className="flex justify-center px-6 pt-16 pb-24"
        >
          <blockquote className="max-w-[600px] text-center">
            <span
              className="font-playfair text-[3.5rem] leading-[0.6] text-[#D6CDEA] block mb-3 select-none"
              aria-hidden
            >
              &ldquo;
            </span>
            <p className="font-playfair italic text-[1.1rem] text-[#6B6B6B] leading-[1.75] tracking-[0.01em]">
              Not all biological data types are equally informative for stage prediction.
            </p>
            <div className="w-10 h-px bg-[#D6CDEA] mx-auto mt-7" />
          </blockquote>
        </section>

        {/* Divider */}
        <div className="flex justify-center px-6">
          <hr className="w-full max-w-[860px] border-none border-t border-[#E5E5E5] h-px bg-[#E5E5E5]" />
        </div>

        {/* ── Section 1: How It Works ─────────────────────────────────────── */}
        <section
          id="how-it-works"
          aria-label="How it works"
          className="flex flex-col items-center px-6 py-[80px]"
        >
          <h2 className="font-playfair font-medium text-[2rem] text-[#2E2A2A] mb-12 tracking-[-0.01em]">
            How It Works
          </h2>

          {/* Pipeline card */}
          <div
            className="bg-white border border-[#E5E5E5] rounded-xl
                       shadow-[0_4px_18px_rgba(0,0,0,0.05)]
                       px-10 py-10 max-w-[860px] w-full
                       flex items-center justify-between gap-4 flex-wrap
                       transition-all duration-200
                       hover:shadow-[0_8px_28px_rgba(0,0,0,0.08)]"
          >
            {/* Step */}
            {[
              {
                icon: (
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.4} strokeLinecap="round" strokeLinejoin="round" className="w-9 h-9">
                    <path d="M8 3C8 3 7 8 12 12C17 16 16 21 16 21" />
                    <path d="M16 3C16 3 17 8 12 12C7 16 8 21 8 21" />
                    <line x1="6.5" y1="7" x2="17.5" y2="7" />
                    <line x1="5.5" y1="12" x2="18.5" y2="12" />
                    <line x1="6.5" y1="17" x2="17.5" y2="17" />
                  </svg>
                ),
                title: "Genomics",
                sub: "Mutation landscape",
              },
              {
                icon: (
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.4} strokeLinecap="round" strokeLinejoin="round" className="w-9 h-9">
                    <polyline points="2 12 5 6 8 14 11 9 14 15 17 10 20 12 22 12" />
                  </svg>
                ),
                title: "Transcriptomics",
                sub: "Gene expression",
              },
              {
                icon: (
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.4} strokeLinecap="round" strokeLinejoin="round" className="w-9 h-9">
                    <circle cx="12" cy="12" r="9" />
                    <circle cx="12" cy="12" r="4" />
                    <line x1="12" y1="3" x2="12" y2="8" />
                    <line x1="12" y1="16" x2="12" y2="21" />
                    <line x1="3" y1="12" x2="8" y2="12" />
                    <line x1="16" y1="12" x2="21" y2="12" />
                  </svg>
                ),
                title: "Radiomics",
                sub: "Tumour phenotype",
              },
              {
                icon: (
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.4} strokeLinecap="round" strokeLinejoin="round" className="w-9 h-9">
                    <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
                  </svg>
                ),
                title: "Prediction",
                sub: "Stage classification",
              },
            ].map((step, i, arr) => (
              <div key={step.title} className="flex items-center gap-4 flex-1 min-w-[160px]">
                <div className="flex flex-col items-center text-center flex-1 gap-3">
                  <div className="text-[#8B7CBF]">{step.icon}</div>
                  <div>
                    <p className="font-playfair font-medium text-[0.95rem] text-[#2E2A2A]">{step.title}</p>
                    <p className="text-[0.75rem] text-[#6B6B6B] tracking-[0.03em] mt-0.5">{step.sub}</p>
                  </div>
                </div>
                {i < arr.length - 1 && (
                  <svg viewBox="0 0 24 10" fill="none" className="w-8 h-4 shrink-0 text-[#D6CDEA]">
                    <path d="M0 5h20M15 1l5 4-5 4" stroke="currentColor" strokeWidth={1.4} strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                )}
              </div>
            ))}
          </div>

          <p className="mt-7 text-[0.8rem] text-[#6B6B6B] tracking-[0.04em]">
            Each modality captures a different layer of tumour biology.
          </p>
        </section>

        {/* Divider */}
        <div className="flex justify-center px-6">
          <hr className="w-full max-w-[1000px] border-none h-px bg-[#E5E5E5]" />
        </div>

        {/* ── Section 2: About PDAC ────────────────────────────────────────── */}
        <section
          id="about"
          aria-label="About PDAC"
          className="px-6 py-[80px] max-w-[1000px] mx-auto w-full"
        >
          <div className="grid grid-cols-1 md:grid-cols-2 gap-16 items-center">
            {/* Left — histology image */}
            <div className="rounded-xl aspect-[4/3] overflow-hidden border border-[#E5E5E5] shadow-[0_4px_18px_rgba(139,124,191,0.1)]">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src="/pancreatic-tissue.png"
                alt="Pancreatic tissue histology"
                className="w-full h-full object-cover"
              />
            </div>

            {/* Right — text */}
            <div>
              <h2 className="font-playfair font-medium text-[1.9rem] text-[#2E2A2A] mb-6 tracking-[-0.01em]">
                About PDAC
              </h2>
              <p className="text-[0.9rem] text-[#6B6B6B] leading-[1.8]">
                Pancreatic ductal adenocarcinoma is typically diagnosed at an advanced stage, as early disease produces
                few distinguishable symptoms. While somatic mutations in genes such as <em>KRAS</em> and <em>TP53</em> are
                near-universal, they offer limited power for distinguishing stage, as they accumulate early and persist
                throughout progression. Transcriptomic and radiomic profiles, by contrast, shift measurably between
                early and late disease, making them more informative targets for stage-based classification.
              </p>
            </div>
          </div>
        </section>

        {/* Divider */}
        <div className="flex justify-center px-6">
          <hr className="w-full max-w-[1000px] border-none h-px bg-[#E5E5E5]" />
        </div>

        {/* ── Sections 3 + 4: Key Findings & Why It Matters (combined) ──────── */}
        <section
          id="results"
          aria-label="Key Findings and Why It Matters"
          className="px-6 py-[80px] max-w-[1000px] mx-auto w-full"
        >
          <div className="grid grid-cols-1 md:grid-cols-2 gap-10 items-start">

            {/* LEFT — Key Findings */}
            <div className="flex flex-col gap-6">
              <div>
                <h2 className="font-playfair font-medium text-[1.9rem] text-[#2E2A2A] mb-5 tracking-[-0.01em]">
                  Key Findings
                </h2>
                <p className="text-[0.9rem] text-[#6B6B6B] leading-[1.8]">
                  Across all three modalities tested, radiomic features derived from tumour imaging showed the
                  strongest discriminative signal between early and late-stage PDAC. Transcriptomic profiles
                  contributed meaningfully, particularly when combined with imaging. Genomic mutation data alone
                  produced classification performance close to chance, consistent with its stage-independent
                  accumulation pattern.
                </p>
              </div>

              {/* Bar chart — inline below Key Findings text */}
              <div
                className="bg-white border border-[#E5E5E5] rounded-xl
                           shadow-[0_4px_18px_rgba(0,0,0,0.05)]
                           px-7 py-7
                           transition-all duration-200
                           hover:shadow-[0_8px_28px_rgba(0,0,0,0.08)]"
              >
                <p className="text-[0.7rem] tracking-[0.14em] uppercase text-[#AAAAAA] mb-5">
                  Relative discriminative power
                </p>
                {[
                  { label: "Radiomic", fill: 88, color: "#8B7CBF" },
                  { label: "Transcriptomic", fill: 58, color: "#B3A8D8" },
                  { label: "Genomic", fill: 14, color: "#E0D9F2" },
                ].map(({ label, fill, color }) => (
                  <div key={label} className="mb-4 last:mb-0">
                    <div className="flex justify-between items-center mb-1.5">
                      <span className="text-[0.82rem] text-[#2E2A2A] tracking-[0.01em]">{label}</span>
                      <span className="text-[0.72rem] text-[#AAAAAA]">{fill}%</span>
                    </div>
                    <div className="h-[7px] rounded-full bg-[#F0ECF9] overflow-hidden">
                      <div
                        className="h-full rounded-full"
                        style={{ width: `${fill}%`, backgroundColor: color }}
                      />
                    </div>
                  </div>
                ))}
              </div>

              {/* Read more button */}
              <div>
                <a
                  href="#results"
                  className="inline-flex items-center font-sans text-[0.85rem] tracking-[0.03em]
                             px-6 py-[11px] rounded-lg bg-transparent text-[#8B7CBF]
                             border-[1.5px] border-[#8B7CBF]
                             transition-all duration-200
                             hover:bg-[#8B7CBF]/[0.07] hover:-translate-y-px"
                >
                  Read more about my findings
                </a>
              </div>
            </div>

            {/* RIGHT — Why It Matters */}
            <div className="flex flex-col gap-6">
              <div>
                <h2 className="font-playfair font-medium text-[1.9rem] text-[#2E2A2A] mb-5 tracking-[-0.01em]">
                  Why It Matters
                </h2>
                <p className="text-[0.9rem] text-[#6B6B6B] leading-[1.8]">
                  Late-stage PDAC carries a five-year survival rate below 5%. Identifying reliable multimodal
                  signatures of progression could support earlier clinical intervention and more targeted
                  follow-up strategies. This analysis is not a clinical tool, but its findings suggest that
                  integrating imaging and expression data may offer more signal than genomics alone — a useful
                  basis for designing future diagnostic frameworks.
                </p>
              </div>

              {/* Abstract visual — sits naturally below the paragraph */}
              <div
                className="rounded-xl flex flex-col items-center justify-center gap-4 py-10
                           bg-gradient-to-br from-[#F8F5F2] to-[#EDE7F6]
                           border border-[#E5E5E5]"
              >
                <svg viewBox="0 0 180 130" fill="none" xmlns="http://www.w3.org/2000/svg" className="w-[60%] opacity-55">
                  <circle cx="70" cy="65" r="38" stroke="#C4B8E2" strokeWidth="1.2" fill="#EDE7F6" fillOpacity="0.4" />
                  <circle cx="110" cy="65" r="38" stroke="#C4B8E2" strokeWidth="1.2" fill="#D6CDEA" fillOpacity="0.3" />
                  <circle cx="90" cy="95" r="38" stroke="#C4B8E2" strokeWidth="1.2" fill="#B3A8D8" fillOpacity="0.2" />
                  <circle cx="90" cy="72" r="7" fill="#8B7CBF" fillOpacity="0.55" />
                  <circle cx="90" cy="72" r="3" fill="#8B7CBF" />
                </svg>
                <p className="text-[0.72rem] tracking-[0.12em] uppercase text-[#AAAAAA]">Multimodal integration</p>
              </div>
            </div>

          </div>
        </section>

        {/* Divider */}
        <div className="flex justify-center px-6">
          <hr className="w-full max-w-[1000px] border-none h-px bg-[#E5E5E5]" />
        </div>

        {/* ── Section 5: Final CTA ─────────────────────────────────────────── */}
        <section
          id="sample"
          aria-label="Call to action"
          className="flex flex-col items-center text-center px-6 py-[96px]"
        >
          <p className="text-[0.72rem] font-medium tracking-[0.2em] uppercase text-[#8B7CBF] mb-5">
            Explore the research
          </p>
          <h2 className="font-playfair font-medium text-[2rem] text-[#2E2A2A] mb-10 tracking-[-0.01em]">
            Ready to explore the data?
          </h2>
          <div className="flex gap-4 flex-wrap justify-center">
            <a
              href="/analysis"
              className="inline-flex items-center gap-2 font-sans text-[0.875rem] tracking-[0.03em]
                         px-8 py-[13px] rounded-lg bg-[#8B7CBF] text-white border-[1.5px] border-[#8B7CBF]
                         transition-all duration-200
                         hover:bg-[#7A6BAE] hover:border-[#7A6BAE] hover:-translate-y-px
                         hover:shadow-[0_6px_20px_rgba(139,124,191,0.25)]"
            >
              Try It Yourself
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
                <path d="M5 12h14M12 5l7 7-7 7" />
              </svg>
            </a>
            <a
              href="#results"
              className="inline-flex items-center font-sans text-[0.875rem] tracking-[0.03em]
                         px-8 py-[13px] rounded-lg bg-transparent text-[#2E2A2A]
                         border-[1.5px] border-[#E5E5E5]
                         transition-all duration-200
                         hover:border-[#D6CDEA] hover:text-[#8B7CBF] hover:-translate-y-px"
            >
              View Findings
            </a>
          </div>
        </section>
      </div>
    </>
  )
}
