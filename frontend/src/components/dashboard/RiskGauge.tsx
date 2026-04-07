"use client"
import { LineChart, Line, ResponsiveContainer } from "recharts"
import type { RiskScore } from "@/lib/types"

interface Props { riskScore: RiskScore | null }

export function RiskGauge({ riskScore }: Props) {
  const score = riskScore?.score ?? 0
  const history = riskScore?.history ?? []
  const color = score < 40 ? "#6e6e73" : score < 70 ? "#FF9F0A" : "#FF3B30"
  const label = score < 40 ? "NOMINAL" : score < 70 ? "ELEVATED" : "CRITICAL"

  const R = 52, CX = 80, CY = 80
  const START_DEG = -225, SWEEP = 270
  const toRad = (d: number) => (d * Math.PI) / 180
  const arcX = (deg: number) => CX + R * Math.cos(toRad(deg))
  const arcY = (deg: number) => CY + R * Math.sin(toRad(deg))
  const endDeg = START_DEG + (score / 100) * SWEEP
  const largeArc = (score / 100) * SWEEP > 180 ? 1 : 0
  const trackD = `M ${arcX(START_DEG)} ${arcY(START_DEG)} A ${R} ${R} 0 1 1 ${arcX(START_DEG + SWEEP - 0.01)} ${arcY(START_DEG + SWEEP - 0.01)}`
  const fillD = score <= 0 ? "" :
    `M ${arcX(START_DEG)} ${arcY(START_DEG)} A ${R} ${R} 0 ${largeArc} 1 ${arcX(endDeg)} ${arcY(endDeg)}`

  return (
    <div className="rounded-xl p-4" style={{
      background: "#1e1e1e",
      border: "1px solid rgba(229,229,234,0.06)",
    }}>
      <div className="flex items-center justify-between mb-3">
        <span style={{
          fontFamily: "'JetBrains Mono', monospace",
          fontSize: "10px",
          letterSpacing: "0.15em",
          color: "rgba(255,59,48,0.7)",
        }}>
          RISK SCORE
        </span>
        <span style={{
          fontFamily: "'JetBrains Mono', monospace",
          fontSize: "9px",
          padding: "2px 8px",
          borderRadius: "4px",
          background: `${color}12`,
          color,
          border: `1px solid ${color}25`,
        }}>
          {label}
        </span>
      </div>

      <div className="flex items-center gap-4">
        <div className="flex-shrink-0">
          <svg width="110" height="82" viewBox="20 22 120 88">
            <path d={trackD} fill="none" stroke="#2a2a2a" strokeWidth="8" strokeLinecap="round" />
            {fillD && (
              <path
                d={fillD} fill="none" stroke={color} strokeWidth="8" strokeLinecap="round"
                style={{ transition: "all 0.6s cubic-bezier(0.4,0,0.2,1)", filter: `drop-shadow(0 0 6px ${color}90)` }}
              />
            )}
            <text x={CX} y={CY + 6} textAnchor="middle" fill="#E5E5EA" fontSize="20"
              fontFamily="'JetBrains Mono', monospace" fontWeight="700">
              {score.toFixed(0)}
            </text>
            <text x={CX} y={CY + 18} textAnchor="middle" fill="#6e6e73" fontSize="8"
              fontFamily="'JetBrains Mono', monospace">
              / 100
            </text>
          </svg>
        </div>

        <div className="flex-1 space-y-3">
          {[
            { label: "IF Score",  value: (riskScore?.if_score ?? 0).toFixed(3) },
            { label: "Z-Score Δ", value: (riskScore?.zscore_delta ?? 0).toFixed(3) },
          ].map(({ label: l, value: v }) => (
            <div key={l} className="flex items-center justify-between">
              <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: "10px", color: "#6e6e73" }}>{l}</span>
              <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: "11px", color: "rgba(229,229,234,0.7)" }}>{v}</span>
            </div>
          ))}
        </div>
      </div>

      {history.length > 1 && (
        <div className="mt-3 h-10">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={history.slice(-20)}>
              <Line type="monotone" dataKey="score" stroke={color} strokeWidth={1.5} dot={false} isAnimationActive={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  )
}
