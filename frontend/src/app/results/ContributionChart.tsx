"use client"

import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Cell,
} from "recharts"
import type { ResultData, ModalityKey } from "./data"

const MODALITY_COLORS: Record<ModalityKey, string> = {
  Radiomic: "#8B7CBF",
  Transcriptomic: "#B3A8D8",
  Clinical: "#CFC7E8",
  Genomic: "#E0D9F2",
}

function CustomTooltip({ active, payload }: { active?: boolean; payload?: { value: number; payload: { modality: string } }[] }) {
  if (!active || !payload?.length) return null
  const { modality } = payload[0].payload
  const pct = Math.round(payload[0].value * 100)
  return (
    <div className="bg-[#2E2A2A] text-white rounded-xl px-3 py-2.5 text-[0.75rem] shadow-lg">
      <p className="font-medium mb-0.5">{modality}</p>
      <p className="text-[#D6CDEA]">{pct}% relative contribution</p>
      <p className="text-[#999] mt-1 max-w-[160px] leading-snug">
        Relative contribution to final prediction
      </p>
    </div>
  )
}

export function ContributionChart({ data }: { data: ResultData }) {
  const chartData = data.modalityContributions.map(d => ({
    modality: d.modality,
    value: d.value,
  }))

  const top = data.modalityContributions[0]
  const second = data.modalityContributions[1]

  return (
    <div className="bg-white rounded-2xl border border-[#E5E5E5] shadow-[0_2px_12px_rgba(0,0,0,0.04)] p-6">
      <div className="flex items-start justify-between mb-5">
        <div>
          <h3 className="font-playfair font-medium text-[1.1rem] text-[#2E2A2A]">
            Modality Contribution
          </h3>
          <p className="text-[0.75rem] text-[#6B6B6B] mt-0.5">
            Relative weight of each data type in the final prediction
          </p>
        </div>
        <div className="text-right text-[0.78rem] text-[#6B6B6B] space-y-0.5">
          <p>
            <span className="font-medium text-[#2E2A2A]">{top.modality}</span>{" "}
            {Math.round(top.value * 100)}%
          </p>
          <p>
            <span className="font-medium text-[#2E2A2A]">{second.modality}</span>{" "}
            {Math.round(second.value * 100)}%
          </p>
        </div>
      </div>

      <ResponsiveContainer width="100%" height={160}>
        <BarChart
          data={chartData}
          layout="vertical"
          margin={{ left: 0, right: 20, top: 4, bottom: 4 }}
          barSize={14}
        >
          <XAxis type="number" domain={[0, 1]} hide />
          <YAxis
            type="category"
            dataKey="modality"
            width={110}
            tick={{ fontSize: 12, fill: "#6B6B6B" }}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip content={<CustomTooltip />} cursor={{ fill: "#F0ECF9" }} />
          <Bar dataKey="value" radius={[0, 6, 6, 0]}>
            {chartData.map(entry => (
              <Cell key={entry.modality} fill={MODALITY_COLORS[entry.modality as ModalityKey]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      {/* Legend row */}
      <div className="flex flex-wrap gap-4 mt-3">
        {chartData.map(d => (
          <div key={d.modality} className="flex items-center gap-1.5">
            <span
              className="w-2.5 h-2.5 rounded-full"
              style={{ backgroundColor: MODALITY_COLORS[d.modality as ModalityKey] }}
            />
            <span className="text-[0.73rem] text-[#6B6B6B]">
              {d.modality}{" "}
              <span className="font-medium text-[#2E2A2A]">{Math.round(d.value * 100)}%</span>
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
