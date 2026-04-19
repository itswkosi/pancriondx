"use client"

import { useState } from "react"
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Cell,
  ReferenceLine,
} from "recharts"
import type { ResultData } from "./data"

type Tab = "Genomic" | "Transcriptomic" | "Radiomic" | "Clinical"

const PATHOGENICITY_BADGE: Record<string, string> = {
  pathogenic: "bg-[#F0ECF9] text-[#7C5CBF] border border-[#D6CDEA]",
  likely_pathogenic: "bg-[#F5F0FF] text-[#9B7ADE] border border-[#DDD4F5]",
  vus: "bg-[#F8F7F2] text-[#8A8060] border border-[#E5E0CC]",
  benign: "bg-[#F0F8F0] text-[#4A8C4A] border border-[#C4E0C4]",
}

// ─── Genomic tab ──────────────────────────────────────────────────────────────

function GenomicTab({ data }: { data: ResultData }) {
  return (
    <div>
      <p className="text-[0.8rem] text-[#6B6B6B] mb-4">
        Somatic mutations detected in the sample, with model-assigned contribution weights.
      </p>
      <div className="rounded-xl border border-[#E5E5E5] overflow-hidden">
        <table className="w-full text-[0.8rem] border-collapse">
          <thead>
            <tr className="bg-[#F8F5F2] border-b border-[#E5E5E5]">
              {["Gene", "Variant", "Pathogenicity", "Model Weight"].map(h => (
                <th key={h} className="text-left px-4 py-3 font-medium text-[#2E2A2A] tracking-[0.02em]">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.genomicVariants.map((v, i) => (
              <tr key={i} className="border-b border-[#F0EDF8] last:border-0 hover:bg-[#FDFCFF]">
                <td className="px-4 py-3 font-medium text-[#2E2A2A] font-mono">{v.gene}</td>
                <td className="px-4 py-3 text-[#6B6B6B] font-mono">{v.variant}</td>
                <td className="px-4 py-3">
                  <span className={`text-[0.7rem] font-medium px-2 py-0.5 rounded-full ${PATHOGENICITY_BADGE[v.pathogenicity]}`}>
                    {v.pathogenicity.replace("_", " ")}
                  </span>
                </td>
                <td className="px-4 py-3 font-mono text-[#8B7CBF] font-semibold">
                  +{v.weight.toFixed(2)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="text-[0.73rem] text-[#AAAAAA] mt-3">
        Mutation presence alone contributes weakly to stage classification in this model.
        Genomic weight: 2% of final prediction.
      </p>
    </div>
  )
}

// ─── Transcriptomic tab ───────────────────────────────────────────────────────

const GROUP_COLORS: Record<string, string> = {
  stromal: "#8B7CBF",
  dna_damage: "#B3A8D8",
  other: "#CFC7E8",
}

const GROUP_LABELS: Record<string, string> = {
  stromal: "Stromal",
  dna_damage: "DNA Damage",
  other: "Other",
}

function TxTooltip({ active, payload }: { active?: boolean; payload?: { value: number; payload: { gene: string; group: string } }[] }) {
  if (!active || !payload?.length) return null
  const { gene, group } = payload[0].payload
  const z = payload[0].value
  return (
    <div className="bg-[#2E2A2A] text-white rounded-xl px-3 py-2.5 text-[0.75rem] shadow-lg">
      <p className="font-medium">{gene}</p>
      <p className="text-[#D6CDEA]">z-score: {z.toFixed(2)}</p>
      <p className="text-[#999]">{GROUP_LABELS[group]}</p>
    </div>
  )
}

function TranscriptomicTab({ data }: { data: ResultData }) {
  const sorted = [...data.transcriptomicGenes].sort((a, b) => b.zscore - a.zscore)
  return (
    <div>
      <p className="text-[0.8rem] text-[#6B6B6B] mb-4">
        Gene expression z-scores relative to cohort median. Positive = overexpressed; negative = underexpressed.
      </p>
      <ResponsiveContainer width="100%" height={240}>
        <BarChart data={sorted} margin={{ left: 0, right: 10, top: 4, bottom: 30 }} barSize={22}>
          <XAxis
            dataKey="gene"
            tick={{ fontSize: 11, fill: "#6B6B6B", fontFamily: "monospace" }}
            axisLine={false}
            tickLine={false}
            angle={-35}
            textAnchor="end"
          />
          <YAxis
            tick={{ fontSize: 11, fill: "#6B6B6B" }}
            axisLine={false}
            tickLine={false}
          />
          <ReferenceLine y={0} stroke="#E5E5E5" />
          <Tooltip content={<TxTooltip />} cursor={{ fill: "#F0ECF9" }} />
          <Bar dataKey="zscore" radius={[4, 4, 0, 0]}>
            {sorted.map(entry => (
              <Cell key={entry.gene} fill={GROUP_COLORS[entry.group]} opacity={entry.zscore < 0 ? 0.55 : 1} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
      {/* Legend */}
      <div className="flex gap-4 mt-1 mb-3">
        {Object.entries(GROUP_LABELS).map(([k, label]) => (
          <div key={k} className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: GROUP_COLORS[k] }} />
            <span className="text-[0.73rem] text-[#6B6B6B]">{label}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

// ─── Radiomic tab ─────────────────────────────────────────────────────────────

function RadiomicTab({ data }: { data: ResultData }) {
  return (
    <div>
      <p className="text-[0.8rem] text-[#6B6B6B] mb-4">
        Imaging-derived feature values and their contribution to the prediction.
        Radiomic data accounts for 83% of model weight.
      </p>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {data.radiomicFeatures.map(f => (
          <div
            key={f.name}
            className="bg-[#FDFCFF] rounded-xl border border-[#EDE7F6] p-4"
          >
            <div className="flex items-center justify-between mb-2">
              <span className="font-medium text-[0.85rem] text-[#2E2A2A]">{f.name}</span>
              <span className="font-mono font-semibold text-[0.9rem] text-[#8B7CBF]">
                {f.value.toFixed(2)}{f.unit}
              </span>
            </div>
            {/* contribution bar */}
            <div className="h-[5px] rounded-full bg-[#EDE7F6] overflow-hidden mb-3">
              <div
                className="h-full rounded-full bg-[#8B7CBF]"
                style={{ width: `${Math.abs(f.contribution) * 100}%`, opacity: f.contribution < 0 ? 0.45 : 0.9 }}
              />
            </div>
            <p className="text-[0.73rem] text-[#6B6B6B] leading-[1.55]">{f.interpretation}</p>
            <p className={`text-[0.7rem] font-mono font-semibold mt-2 ${f.contribution >= 0 ? "text-[#7C6BAE]" : "text-[#9E8EC4]"}`}>
              {f.contribution >= 0 ? "+" : ""}{f.contribution.toFixed(2)} contribution
            </p>
          </div>
        ))}
      </div>
    </div>
  )
}

// ─── Clinical tab ─────────────────────────────────────────────────────────────

function ClinicalTab({ data }: { data: ResultData }) {
  const c = data.clinicalData
  const rows = [
    { label: "Age", value: `${c.age} years` },
    { label: "Sex", value: c.sex },
    { label: "Tumor Location", value: c.tumorLocation },
    { label: "Tumor Size", value: `${c.tumorSize} cm` },
    { label: "CA19-9", value: `${c.ca199} U/mL` },
    { label: "ECOG Status", value: `${c.ecog}` },
    { label: "Inferred Stage", value: c.stage },
  ]
  const riskModifiers = [
    c.ca199 > 200 ? "Elevated CA19-9 (>200 U/mL) — associated with advanced disease" : null,
    c.age > 65 ? "Age >65 — increased biological risk" : null,
    c.ecog > 1 ? `ECOG ${c.ecog} — reduced functional status` : null,
  ].filter(Boolean)

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
      <div className="rounded-xl border border-[#E5E5E5] overflow-hidden">
        <table className="w-full text-[0.8rem] border-collapse">
          <tbody>
            {rows.map(r => (
              <tr key={r.label} className="border-b border-[#F0EDF8] last:border-0">
                <td className="px-4 py-2.5 text-[#6B6B6B] w-40">{r.label}</td>
                <td className="px-4 py-2.5 font-medium text-[#2E2A2A]">{r.value}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {riskModifiers.length > 0 && (
        <div>
          <p className="text-[0.73rem] tracking-[0.08em] uppercase text-[#AAAAAA] font-medium mb-3">
            Risk Modifiers
          </p>
          <div className="flex flex-col gap-2">
            {riskModifiers.map((m, i) => (
              <div key={i} className="flex items-start gap-2.5 bg-[#FDFCFF] rounded-xl border border-[#EDE7F6] px-4 py-3">
                <span className="text-[#8B7CBF] mt-0.5 text-[11px]">▲</span>
                <p className="text-[0.78rem] text-[#6B6B6B] leading-[1.55]">{m}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

// ─── Tabs shell ───────────────────────────────────────────────────────────────

const TABS: Tab[] = ["Genomic", "Transcriptomic", "Radiomic", "Clinical"]

export function ModalityTabs({ data }: { data: ResultData }) {
  const [active, setActive] = useState<Tab>("Genomic")

  return (
    <section>
      <h2 className="font-playfair font-medium text-[1.6rem] text-[#2E2A2A] mb-5 tracking-[-0.01em]">
        Gene-Level & Expression Insights
      </h2>

      <div className="bg-white rounded-2xl border border-[#E5E5E5] shadow-[0_2px_12px_rgba(0,0,0,0.04)] overflow-hidden">
        {/* Tab bar */}
        <div className="flex border-b border-[#E5E5E5]">
          {TABS.map(tab => (
            <button
              key={tab}
              onClick={() => setActive(tab)}
              className={`flex-1 text-[0.82rem] tracking-[0.02em] py-3.5 font-medium transition-all duration-150
                ${active === tab
                  ? "text-[#8B7CBF] border-b-2 border-[#8B7CBF] bg-[#FDFCFF]"
                  : "text-[#6B6B6B] hover:text-[#2E2A2A] hover:bg-[#FDFCFF]"
                }`}
            >
              {tab}
            </button>
          ))}
        </div>

        {/* Tab content */}
        <div className="p-6">
          {active === "Genomic" && <GenomicTab data={data} />}
          {active === "Transcriptomic" && <TranscriptomicTab data={data} />}
          {active === "Radiomic" && <RadiomicTab data={data} />}
          {active === "Clinical" && <ClinicalTab data={data} />}
        </div>
      </div>
    </section>
  )
}
