"use client"

import type { ResultData } from "./data"

// ─── Tooltip ──────────────────────────────────────────────────────────────────

function Tooltip({ text }: { text: string }) {
  return (
    <span className="group relative inline-flex items-center ml-1.5 cursor-help">
      <span className="w-[15px] h-[15px] rounded-full bg-[#E8E0F5] text-[#8B7CBF] text-[9px] font-bold flex items-center justify-center select-none">
        ?
      </span>
      <span
        className="pointer-events-none absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-[220px]
                   rounded-xl bg-[#2E2A2A] text-white text-[0.73rem] leading-[1.55] px-3 py-2.5
                   opacity-0 group-hover:opacity-100 transition-opacity duration-150 z-50 shadow-lg"
      >
        {text}
      </span>
    </span>
  )
}

// ─── Confidence bar ───────────────────────────────────────────────────────────

function ConfidenceBar({ value }: { value: number }) {
  const pct = Math.round(value * 100)
  return (
    <div>
      <div className="flex items-center justify-between mb-2">
        <span className="text-[0.78rem] text-[#6B6B6B] tracking-[0.04em] uppercase font-medium">
          Model Confidence
          <Tooltip text="Calibrated confidence score. A score of 91% means the model assigns this probability with high reliability, validated on held-out data." />
        </span>
        <span className="text-[0.82rem] font-semibold text-[#2E2A2A]">{pct}%</span>
      </div>
      <div className="h-2 rounded-full bg-[#EDE7F6] overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-700"
          style={{
            width: `${pct}%`,
            background: "linear-gradient(90deg, #B3A8D8 0%, #8B7CBF 100%)",
          }}
        />
      </div>
    </div>
  )
}

// ─── Risk Card ────────────────────────────────────────────────────────────────

export function RiskCard({ data }: { data: ResultData }) {
  const isLate = data.classification === "Late-stage likely"
  const riskPct = Math.round(data.riskScore * 100)

  return (
    <div className="bg-white rounded-2xl border border-[#E5E5E5] shadow-[0_2px_16px_rgba(139,124,191,0.1)] p-8">
      {/* Top row */}
      <div className="flex items-start justify-between flex-wrap gap-4 mb-6">
        <div>
          <h2 className="font-playfair font-medium text-[2rem] text-[#2E2A2A] leading-tight tracking-[-0.02em]">
            {data.classification}
          </h2>
          <p className="text-[0.82rem] text-[#6B6B6B] mt-1">
            Prediction derived from multimodal analysis (genomic, transcriptomic, radiomic, clinical)
          </p>
        </div>

        <div className="flex items-center gap-4">
          {/* Signal bars */}
          <div className="flex items-end gap-[3px] h-6">
            {[0.3, 0.55, 0.75, 1].map((h, i) => (
              <div
                key={i}
                className="w-[5px] rounded-sm"
                style={{
                  height: `${h * 100}%`,
                  backgroundColor: i < 3 ? "#8B7CBF" : "#E8E0F5",
                  opacity: i < 3 ? 1 : 0.5,
                }}
              />
            ))}
          </div>
          {/* Risk % badge */}
          <div className="flex items-center gap-2">
            <span
              className={`w-3 h-3 rounded-full ${isLate ? "bg-[#8B7CBF]" : "bg-[#A8D8A8]"}`}
            />
            <span className="font-playfair font-medium text-[2rem] text-[#2E2A2A]">
              {riskPct}%
            </span>
          </div>
        </div>
      </div>

      {/* Main progress bar */}
      <div className="h-2.5 rounded-full bg-[#EDE7F6] overflow-hidden mb-5">
        <div
          className="h-full rounded-full"
          style={{
            width: `${riskPct}%`,
            background: isLate
              ? "linear-gradient(90deg, #C4B8E2 0%, #8B7CBF 100%)"
              : "linear-gradient(90deg, #B8E2C4 0%, #6BAF6B 100%)",
          }}
        />
      </div>

      {/* Confidence + Brier score row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
        <div>
          <p className="text-[0.78rem] font-medium text-[#2E2A2A] mb-0.5">
            Confidence: High ({Math.round(data.confidence * 100)}%)
          </p>
          <ConfidenceBar value={data.confidence} />
        </div>
        <div className="bg-[#FDFCFF] rounded-xl border border-[#EDE7F6] px-5 py-4">
          <p className="font-playfair font-medium text-[1.1rem] text-[#2E2A2A]">
            Confidence: {data.brierScore}
          </p>
          <p className="text-[0.75rem] text-[#6B6B6B] mt-1 leading-snug">
            Lower scores indicate better probability calibration
          </p>
        </div>
      </div>
    </div>
  )
}
