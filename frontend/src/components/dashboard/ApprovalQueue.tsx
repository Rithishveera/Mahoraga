"use client"
import { useState } from "react"
import { approveItem, overrideItem } from "@/lib/api"
import type { ApprovalItem } from "@/lib/types"
import { NODE_COLORS } from "@/lib/constants"

interface Props {
  items: ApprovalItem[]
  onApprove: (id: string) => void
  onOverride: (id: string) => void
}

export function ApprovalQueue({ items, onApprove, onOverride }: Props) {
  const [loadingId, setLoadingId] = useState<string | null>(null)
  if (!items.length) return null

  const handleApprove = async (id: string) => {
    setLoadingId(id)
    try { await approveItem(id); onApprove(id) }
    catch { onApprove(id) }
    finally { setLoadingId(null) }
  }

  const handleOverride = async (id: string) => {
    setLoadingId(id)
    try { await overrideItem(id, "Human override"); onOverride(id) }
    catch { onOverride(id) }
    finally { setLoadingId(null) }
  }

  return (
    <div className="flex flex-col gap-2 animate-slide-up">
      <div className="flex items-center gap-2 px-1">
        <div className="w-2 h-2 rounded-full" style={{
          background: "#FF9F0A",
          boxShadow: "0 0 8px #FF9F0A",
          animation: "pulseAmber 1.5s ease-in-out infinite",
        }} />
        <span style={{
          fontFamily: "'JetBrains Mono', monospace",
          fontSize: "10px",
          letterSpacing: "0.12em",
          color: "rgba(255,159,10,0.8)",
        }}>
          AWAITING APPROVAL — {items.length}
        </span>
      </div>

      <div className="flex flex-col gap-2 max-h-56 overflow-y-auto">
        {items.slice(0, 5).map(item => {
          const nodeColor = NODE_COLORS[item.affected_node] ?? "#6e6e73"
          return (
            <div key={item.id} className="rounded-xl p-4 animate-slide-up" style={{
              background: "#1e1e1e",
              border: "1px solid rgba(255,159,10,0.12)",
            }}>
              <p className="text-sm font-medium mb-1.5" style={{
                color: "#E5E5EA", lineHeight: 1.4, fontSize: "13px",
              }}>
                {item.title}
              </p>
              <p className="text-xs mb-3" style={{
                color: "#6e6e73", lineHeight: 1.6, fontSize: "11px",
              }}>
                {item.summary}
              </p>
              <div className="flex flex-wrap gap-1.5 mb-3">
                {[
                  { text: item.affected_node, color: nodeColor },
                  { text: item.vuln_class, color: "#FF9F0A" },
                  { text: `risk ${item.risk_score?.toFixed(0) ?? 0}`, color: "#FF3B30" },
                ].map(({ text, color }) => (
                  <span key={text} className="px-2 py-0.5 rounded" style={{
                    fontFamily: "'JetBrains Mono', monospace",
                    fontSize: "9px",
                    background: `${color}12`,
                    color,
                    border: `1px solid ${color}22`,
                  }}>
                    {text}
                  </span>
                ))}
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => handleApprove(item.id)}
                  disabled={loadingId === item.id}
                  className="flex-1 py-2 rounded-lg text-xs font-bold tracking-wider transition-all"
                  style={{
                    fontFamily: "'JetBrains Mono', monospace",
                    background: loadingId === item.id ? "#2a2a2a" : "#FF3B30",
                    color: loadingId === item.id ? "#6e6e73" : "#121212",
                    border: "none",
                    boxShadow: loadingId === item.id ? "none" : "0 0 16px rgba(255,59,48,0.3)",
                    cursor: loadingId === item.id ? "not-allowed" : "pointer",
                  }}
                >
                  {loadingId === item.id ? "PATCHING..." : "APPROVE"}
                </button>
                <button
                  onClick={() => handleOverride(item.id)}
                  disabled={loadingId === item.id}
                  className="flex-1 py-2 rounded-lg text-xs font-bold tracking-wider"
                  style={{
                    fontFamily: "'JetBrains Mono', monospace",
                    background: "transparent",
                    color: "#6e6e73",
                    border: "1px solid rgba(229,229,234,0.08)",
                    cursor: "pointer",
                  }}
                >
                  OVERRIDE
                </button>
              </div>
              <p className="text-center mt-2" style={{
                fontFamily: "'JetBrains Mono', monospace",
                fontSize: "9px",
                color: "#3a3a3a",
              }}>
                estimated reduction: −{item.estimated_risk_reduction?.toFixed(0) ?? 0} pts
              </p>
            </div>
          )
        })}
      </div>
    </div>
  )
}
