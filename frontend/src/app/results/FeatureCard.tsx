"use client"

import type { FeatureDriver, ModalityKey } from "./data"

const MODALITY_DOT: Record<ModalityKey, string> = {
  Radiomic: "bg-[#8B7CBF]",
  Transcriptomic: "bg-[#B3A8D8]",
  Genomic: "bg-[#CFC7E8]",
  Clinical: "bg-[#E0D9F2]",
}

function DirectionArrow({ direction, score }: { direction: "up" | "down"; score: number }) {
  const isUp = direction === "up"
  const color = isUp ? "text-[#7C6BAE]" : "text-[#9E8EC4]"
  const sign = score >= 0 ? "+" : ""
  return (
    <div className={`flex items-center gap-1 font-mono text-[0.82rem] font-semibold ${color}`}>
      <span>{isUp ? "↑" : "↓"}</span>
      <span>{sign}{score.toFixed(2)}</span>
    </div>
  )
}

export function FeatureCard({ feature }: { feature: FeatureDriver }) {
  return (
    <div className="bg-white rounded-xl border border-[#E5E5E5] shadow-[0_1px_8px_rgba(0,0,0,0.04)] p-4 flex flex-col gap-2">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full shrink-0 ${MODALITY_DOT[feature.modality]}`} />
          <span className="text-[0.85rem] font-medium text-[#2E2A2A]">{feature.name}</span>
        </div>
        <DirectionArrow direction={feature.direction} score={feature.score} />
      </div>

      {/* Bar */}
      <div className="h-[5px] rounded-full bg-[#EDE7F6] overflow-hidden">
        <div
          className="h-full rounded-full bg-[#8B7CBF]"
          style={{ width: `${Math.abs(feature.score) * 100}%`, opacity: feature.direction === "down" ? 0.5 : 1 }}
        />
      </div>

      <p className="text-[0.75rem] text-[#6B6B6B] leading-[1.6]">{feature.explanation}</p>

      <span className="text-[0.68rem] tracking-[0.06em] uppercase text-[#AAAAAA] font-medium">
        {feature.modality}
      </span>
    </div>
  )
}

export function FeatureBreakdown({ features }: { features: FeatureDriver[] }) {
  return (
    <section>
      <h2 className="font-playfair font-medium text-[1.6rem] text-[#2E2A2A] mb-2 tracking-[-0.01em]">
        Feature Breakdown
      </h2>
      <p className="text-[0.82rem] text-[#6B6B6B] mb-6">
        Top features driving the model's prediction, ranked by contribution magnitude.
      </p>

      {/* Group by modality */}
      {(["Genomic", "Transcriptomic", "Radiomic"] as ModalityKey[]).map(mod => {
        const group = features.filter(f => f.modality === mod)
        if (!group.length) return null
        const labels: Record<string, { title: string; note: string }> = {
          Genomic: { title: "Genomic Signals", note: "Mutation presence contributes weakly to stage classification." },
          Transcriptomic: { title: "Transcriptomic Signals", note: "Expression patterns capture dynamic tumor state" },
          Radiomic: { title: "Radiomic Signals", note: "Imaging features dominate stage discrimination." },
        }
        return (
          <div key={mod} className="mb-6">
            <div className="bg-white rounded-2xl border border-[#E5E5E5] shadow-[0_2px_12px_rgba(0,0,0,0.04)] p-5">
              <h3 className="font-playfair font-medium text-[1rem] text-[#2E2A2A] mb-4">
                {labels[mod].title}
              </h3>
              <div className="flex flex-col gap-3">
                {group.map(f => (
                  <div key={f.name} className="flex items-center gap-3">
                    <div className="flex items-center gap-1.5 w-[140px] shrink-0">
                      <span className={`w-1.5 h-1.5 rounded-full ${MODALITY_DOT[f.modality]}`} />
                      <span className="text-[0.8rem] text-[#2E2A2A]">{f.name}</span>
                    </div>
                    {/* inline bar */}
                    <div className="flex-1 h-[5px] rounded-full bg-[#EDE7F6] overflow-hidden">
                      <div
                        className="h-full rounded-full bg-[#8B7CBF]"
                        style={{
                          width: `${Math.abs(f.score) * 100}%`,
                          marginLeft: f.score < 0 ? "auto" : undefined,
                          opacity: f.score < 0 ? 0.45 : 0.85,
                        }}
                      />
                    </div>
                    <div className={`w-12 text-right font-mono text-[0.78rem] font-semibold shrink-0 ${f.score >= 0 ? "text-[#7C6BAE]" : "text-[#9E8EC4]"}`}>
                      {f.score >= 0 ? "+" : ""}{f.score.toFixed(2)}
                    </div>
                  </div>
                ))}
              </div>
              <p className="text-[0.73rem] text-[#AAAAAA] mt-4">{labels[mod].note}</p>
            </div>
          </div>
        )
      })}
    </section>
  )
}
