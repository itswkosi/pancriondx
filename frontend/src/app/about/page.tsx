"use client"

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
      className="w-[20px] h-[20px]"
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
      className="w-[20px] h-[20px]"
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
      className="w-[20px] h-[20px]"
    >
      <path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6z" />
      <rect x="2" y="9" width="4" height="12" />
      <circle cx="4" cy="4" r="2" />
    </svg>
  )
}

function ArrowRightIcon() {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.6}
      strokeLinecap="round"
      strokeLinejoin="round"
      className="w-[13px] h-[13px] inline-block ml-1"
    >
      <path d="M5 12h14M12 5l7 7-7 7" />
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

// ─── Navbar ───────────────────────────────────────────────────────────────────

const NAV_LINKS = [
  { label: "Home", href: "/" },
  { label: "Analysis", href: "/#analysis" },
  { label: "Results", href: "/#results" },
  { label: "Sample Data", href: "/#sample" },
  { label: "About", href: "/about" },
]

function Navbar() {
  return (
    <nav className="sticky top-0 z-50 h-[68px] flex items-center justify-between px-12 bg-[#F8F5F2]/88 backdrop-blur-md border-b border-[#E5E5E5]/60">
      <a
        href="/"
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
                         hover:after:w-full"
              style={label === "About" ? { color: "#2E2A2A" } : undefined}
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

// ─── Divider ──────────────────────────────────────────────────────────────────

function Divider() {
  return (
    <div className="flex justify-center px-6 my-[70px]">
      <hr className="w-full max-w-[900px] border-none h-px bg-[#E5E5E5]" />
    </div>
  )
}

// ─── Photo ───────────────────────────────────────────────────────────────────

function PhotoPlaceholder() {
  return (
    <div
      className="w-full max-w-[300px] aspect-[3/4] rounded-2xl
                 border border-[#E0D9F2]
                 shadow-[0_8px_32px_rgba(139,124,191,0.14)]
                 overflow-hidden relative"
    >
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        src="/profile.jpg"
        alt="Semilogo Oketola"
        className="w-full h-full object-cover object-top"
      />
    </div>
  )
}

// ─── Project card ─────────────────────────────────────────────────────────────

interface ProjectCardProps {
  name: string
  description: string
  href?: string
  isActive?: boolean
}

function ProjectCard({ name, description, href, isActive = false }: ProjectCardProps) {
  return (
    <div
      className={`
        flex-1 min-w-[220px] max-w-[280px] flex flex-col
        bg-white border rounded-xl px-7 py-8
        shadow-[0_4px_16px_rgba(0,0,0,0.04)]
        transition-all duration-200
        hover:-translate-y-[5px] hover:shadow-[0_12px_32px_rgba(0,0,0,0.08)]
        ${isActive ? "border-[#D6CDEA]" : "border-[#E5E5E5]"}
      `}
    >
      {/* Dot indicator */}
      <div className={`w-2 h-2 rounded-full mb-5 ${isActive ? "bg-[#8B7CBF]" : "bg-[#D6CDEA]"}`} />

      <h3 className="font-playfair font-medium text-[1.05rem] text-[#2E2A2A] mb-3 tracking-[-0.01em]">
        {name}
      </h3>
      <p className="text-[0.82rem] text-[#6B6B6B] leading-[1.7] flex-1">
        {description}
      </p>

      {href && (
        <a
          href={href}
          target="_blank"
          rel="noopener noreferrer"
          className="mt-5 inline-flex items-center text-[0.78rem] tracking-[0.03em]
                     text-[#8B7CBF] transition-colors duration-200
                     hover:text-[#7A6BAE]
                     group"
        >
          View Project
          <span className="transition-transform duration-200 group-hover:translate-x-[3px]">
            <ArrowRightIcon />
          </span>
        </a>
      )}
    </div>
  )
}

// ─── Approach item ────────────────────────────────────────────────────────────

interface ApproachItemProps {
  heading: string
  body: string
}

function ApproachItem({ heading, body }: ApproachItemProps) {
  return (
    <div className="flex gap-8 items-start py-7 border-b border-[#E5E5E5] last:border-b-0">
      {/* Left accent line */}
      <div className="w-px min-h-full self-stretch bg-[#D6CDEA] shrink-0 mt-[3px]" style={{ minHeight: "40px" }} />
      <div>
        <p className="font-sans font-semibold text-[0.9rem] text-[#2E2A2A] mb-1.5 tracking-[0.01em]">
          {heading}
        </p>
        <p className="text-[0.875rem] text-[#6B6B6B] leading-[1.75]">
          {body}
        </p>
      </div>
    </div>
  )
}

// ─── Arrow connector ──────────────────────────────────────────────────────────

function ArrowConnector() {
  return (
    <div className="flex items-center justify-center shrink-0 text-[#D6CDEA] mt-[-8px]">
      <svg viewBox="0 0 32 16" fill="none" className="w-8 h-4">
        <path d="M0 8h26M20 2l8 6-8 6" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    </div>
  )
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function AboutPage() {
  return (
    <>
      <BgLines />

      <div className="relative z-10">
        <Navbar />

        {/* ── Hero ─────────────────────────────────────────────────────────── */}
        <section
          aria-label="About the researcher"
          className="px-6 pt-[96px] pb-[80px] max-w-[900px] mx-auto w-full"
        >
          <div className="grid grid-cols-1 md:grid-cols-[1fr_auto] gap-16 items-center">

            {/* Left — text */}
            <div>
              <p className="text-[0.7rem] font-medium tracking-[0.22em] uppercase text-[#8B7CBF] mb-4">
                Researcher
              </p>
              <h1 className="font-playfair font-medium text-[2.6rem] text-[#2E2A2A] mb-1.5 tracking-[-0.02em] leading-[1.15]">
                Semilogo Oketola
              </h1>
              <p className="text-[0.8rem] text-[#AAAAAA] tracking-[0.08em] mb-7">
                Biotechnologist&ensp;|&ensp;Oncology Research
              </p>
              <p className="text-[0.9rem] text-[#6B6B6B] leading-[1.85] max-w-[480px]">
                I build computational systems to characterise cancer progression using integrated
                biological data. My work sits at the intersection of genomics, transcriptomics, and
                medical imaging, with a focus on multimodal feature integration, model interpretability,
                and biologically grounded validation methodology.
              </p>
            </div>

            {/* Right — photo */}
            <div className="flex justify-center md:justify-end">
              <PhotoPlaceholder />
            </div>

          </div>
        </section>

        <Divider />

        {/* ── Why PancrionDX ───────────────────────────────────────────────── */}
        <section
          aria-label="Why PancrionDX"
          className="px-6 py-[80px] max-w-[900px] mx-auto w-full"
        >
          <h2 className="font-playfair font-medium text-[1.9rem] text-[#2E2A2A] mb-7 tracking-[-0.01em]">
            Why PancrionDX
          </h2>
          <p className="text-[0.9rem] text-[#6B6B6B] leading-[1.85] max-w-[640px]">
            Single-modality mutation-based models have a structural limitation for stage prediction:
            driver mutations in PDAC accumulate early and persist across disease progression, producing
            minimal differential signal between stages. PancrionDX was built to address this by
            integrating transcriptomic expression data and radiomic imaging features alongside genomics —
            capturing biological layers that shift measurably as the disease advances, and producing
            a more faithful representation of tumour state.
          </p>
        </section>

        <Divider />

        {/* ── Project Evolution ────────────────────────────────────────────── */}
        <section
          aria-label="Project evolution"
          className="px-6 py-[80px] max-w-[900px] mx-auto w-full"
        >
          <h2 className="font-playfair font-medium text-[1.9rem] text-[#2E2A2A] mb-12 tracking-[-0.01em]">
            Project Evolution
          </h2>

          <div className="flex flex-wrap gap-4 items-start justify-start">
            <ProjectCard
              name="SynGenix"
              description="Early-stage structured genomic modeling with systematic feature engineering, incorporating multi-gene panel analysis and variant impact scoring."
              href="https://syngenix.figma.site"
            />

            <ArrowConnector />

            <ProjectCard
              name="PanEcho"
              description="Expansion into exploration of computational modeling in biomedical data, establishing initial feature engineering pipelines and baseline classification approaches."
              href="https://panecho-pancrion-dx.vercel.app/upload"
            />

            <ArrowConnector />

            <ProjectCard
              name="PancrionDX"
              description="Multimodal system integrating genomic, transcriptomic, and radiomic data for stage-based classification of pancreatic ductal adenocarcinoma."
              isActive
            />
          </div>
        </section>

        <Divider />

        {/* ── Approach ─────────────────────────────────────────────────────── */}
        <section
          aria-label="Research approach"
          className="px-6 py-[80px] max-w-[900px] mx-auto w-full"
        >
          <h2 className="font-playfair font-medium text-[1.9rem] text-[#2E2A2A] mb-10 tracking-[-0.01em]">
            Approach
          </h2>

          <div className="bg-white border border-[#E5E5E5] rounded-xl px-10 py-2
                          shadow-[0_4px_18px_rgba(0,0,0,0.04)]">
            <ApproachItem
              heading="Biological Grounding"
              body="Models are built to reflect known cancer biology, not just statistical patterns. Feature selection and architecture choices are anchored to the mechanistic behaviour of PDAC."
            />
            <ApproachItem
              heading="Interpretability First"
              body="Every prediction can be traced back to specific gene, expression, or imaging features. Opaque ensemble outputs are accompanied by SHAP attribution and gene-level contribution scores."
            />
            <ApproachItem
              heading="Robust Validation"
              body="Validation includes structured perturbation tests, gene ablation studies, and calibration analysis — not only held-out accuracy. This distinguishes signal from overfitting."
            />
            <ApproachItem
              heading="Multimodal Thinking"
              body="Different data types are treated as complementary biological signals rather than merged blindly. Each modality is evaluated independently before integration, preserving interpretability at the source level."
            />
          </div>
        </section>

        <Divider />

        {/* ── Links ────────────────────────────────────────────────────────── */}
        <section
          aria-label="External links"
          className="flex flex-col items-center text-center px-6 pt-[16px] pb-[96px]"
        >
          <div className="flex gap-7 items-center mb-4">
            {[
              { href: "https://github.com/itswkosi", label: "GitHub", Icon: GitHubIcon },
              { href: "https://www.linkedin.com/in/semilogo-oketola/", label: "LinkedIn", Icon: LinkedInIcon },
              { href: "https://medium.com/@semilogooketola", label: "Medium", Icon: MediumIcon },
            ].map(({ href, label, Icon }) => (
              <a
                key={label}
                href={href}
                target="_blank"
                rel="noopener noreferrer"
                aria-label={label}
                className="w-10 h-10 rounded-full flex items-center justify-center
                           border border-[#E5E5E5] bg-white
                           text-[#AAAAAA]
                           shadow-[0_2px_8px_rgba(0,0,0,0.04)]
                           transition-all duration-200
                           hover:text-[#2E2A2A] hover:border-[#D6CDEA]
                           hover:-translate-y-[3px] hover:shadow-[0_6px_18px_rgba(139,124,191,0.12)]"
              >
                <Icon />
              </a>
            ))}
          </div>
          <p className="text-[0.75rem] tracking-[0.08em] text-[#AAAAAA]">
            More work and writing
          </p>
        </section>

      </div>
    </>
  )
}
