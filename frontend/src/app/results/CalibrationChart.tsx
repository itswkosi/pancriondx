"use client"

import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ReferenceLine,
  Area,
  AreaChart,
} from "recharts"
import type { ResultData } from "./data"

function CalTooltip({ active, payload }: { active?: boolean; payload?: { value: number }[] }) {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-[#2E2A2A] text-white rounded-xl px-3 py-2 text-[0.73rem] shadow-lg">
      <p className="text-[#D6CDEA]">Predicted: {payload[0]?.value?.toFixed(2)}</p>
    </div>
  )
}

export function CalibrationChart({ data }: { data: ResultData }) {
  // Perfect calibration diagonal
  const perfect = [
    { predicted: 0, actual: 0 },
    { predicted: 1, actual: 1 },
  ]

  const chartData = data.calibrationPoints.map(p => ({
    predicted: p.predicted,
    actual: p.actual,
  }))

  return (
    <div className="bg-white rounded-2xl border border-[#E5E5E5] shadow-[0_2px_12px_rgba(0,0,0,0.04)] p-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 items-start">
        {/* Left — explanation */}
        <div>
          <h3 className="font-playfair font-medium text-[1.1rem] text-[#2E2A2A] mb-4">
            Confidence Explanation
          </h3>
          <div className="flex flex-col gap-3 text-[0.8rem] text-[#6B6B6B] leading-[1.7]">
            <p>
              The confidence score reflects how well the model's predicted probabilities
              align with observed outcomes across a held-out validation set.
            </p>
            <p>
              A high AUC does not guarantee perfect certainty on individual cases.
              The Brier score (0.118) measures probability calibration — lower is better.
            </p>
            <p>
              The model learned multimodal patterns from genomic, transcriptomic,
              and radiomic signatures, each contributing independently to the final score.
            </p>
            <div className="bg-[#F8F5F2] rounded-xl border border-[#EDE7F6] px-4 py-3 mt-1">
              <p className="text-[0.75rem] text-[#6B6B6B]">
                Predictions at <span className="font-semibold text-[#2E2A2A]">80% confidence</span> are
                correct approximately <span className="font-semibold text-[#2E2A2A]">~78%</span> of the time,
                indicating well-calibrated uncertainty.
              </p>
            </div>
          </div>
        </div>

        {/* Right — calibration plot */}
        <div>
          <p className="text-[0.73rem] tracking-[0.08em] uppercase text-[#AAAAAA] font-medium mb-1">
            Calibration Plot
          </p>
          <p className="text-[0.73rem] text-[#AAAAAA] mb-4">
            Model predicted probability vs. observed frequency
          </p>

          <ResponsiveContainer width="100%" height={190}>
            <AreaChart data={chartData} margin={{ left: -10, right: 10, top: 10, bottom: 10 }}>
              <defs>
                <linearGradient id="calGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#8B7CBF" stopOpacity={0.2} />
                  <stop offset="100%" stopColor="#8B7CBF" stopOpacity={0.02} />
                </linearGradient>
              </defs>
              <XAxis
                dataKey="predicted"
                tick={{ fontSize: 10, fill: "#AAAAAA" }}
                axisLine={false}
                tickLine={false}
                tickFormatter={v => `${Math.round(v * 100)}%`}
                label={{ value: "Predicted", position: "insideBottom", offset: -4, fontSize: 10, fill: "#AAAAAA" }}
              />
              <YAxis
                tick={{ fontSize: 10, fill: "#AAAAAA" }}
                axisLine={false}
                tickLine={false}
                tickFormatter={v => `${Math.round(v * 100)}%`}
                domain={[0, 1]}
                label={{ value: "Observed", angle: -90, position: "insideLeft", offset: 14, fontSize: 10, fill: "#AAAAAA" }}
              />
              {/* Perfect calibration diagonal */}
              <ReferenceLine
                segment={[{ x: 0, y: 0 }, { x: 1, y: 1 }]}
                stroke="#E5E5E5"
                strokeDasharray="4 4"
                strokeWidth={1.5}
              />
              <Tooltip content={<CalTooltip />} />
              <Area
                type="monotone"
                dataKey="actual"
                stroke="#8B7CBF"
                strokeWidth={2}
                fill="url(#calGrad)"
                dot={{ fill: "#8B7CBF", r: 4, strokeWidth: 0 }}
                activeDot={{ r: 5, fill: "#7A6BAE" }}
              />
            </AreaChart>
          </ResponsiveContainer>

          <div className="flex items-center gap-4 mt-1">
            <div className="flex items-center gap-1.5">
              <div className="w-6 h-px bg-[#E5E5E5]" style={{ borderTop: "1.5px dashed #E5E5E5" }} />
              <span className="text-[0.68rem] text-[#AAAAAA]">Perfect calibration</span>
            </div>
            <div className="flex items-center gap-1.5">
              <div className="w-4 h-px bg-[#8B7CBF]" />
              <span className="text-[0.68rem] text-[#AAAAAA]">Model</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
