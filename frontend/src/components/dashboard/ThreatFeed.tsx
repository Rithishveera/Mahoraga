"use client"
import { useState } from "react"
import type { MahoragaEvent } from "@/lib/types"
import { SEVERITY_COLORS } from "@/lib/constants"

interface Props { events: MahoragaEvent[] }
const FILTERS = ["ALL", "RED", "BLUE", "ANOMALY", "GOVERNOR"] as const
type Filter = typeof FILTERS[number]

export function ThreatFeed({ events }: Props) {
  const [filter, setFilter] = useState<Filter>("ALL")

  const filtered = events.filter(e => {
    if (filter === "ALL")      return true
    if (filter === "RED")      return e.source === "red_agent"
    if (filter === "BLUE")     return e.source === "blue_agent"
    if (filter === "ANOMALY")  return e.source === "anomaly"
    if (filter === "GOVERNOR") return e.source === "governor"
    return true
  }).slice(0, 30)

  return (
    <div className="rounded-xl flex flex-col" style={{
      background: "#1e1e1e",
      border: "1px solid rgba(229,229,234,0.06)",
      minHeight: "160px",
      maxHeight: "220px",
    }}>
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2.5 flex-shrink-0" style={{
        borderBottom: "1px solid rgba(229,229,234,0.05)",
      }}>
        <span style={{
          fontFamily: "'JetBrains Mono', monospace",
          fontSize: "10px",
          letterSpacing: "0.15em",
          color: "rgba(255,59,48,0.7)",
        }}>
          THREAT FEED
        </span>
        <div className="flex gap-1">
          {FILTERS.map(f => (
            <button key={f} onClick={() => setFilter(f)}
              style={{
                fontFamily: "'JetBrains Mono', monospace",
                fontSize: "9px",
                padding: "2px 8px",
                borderRadius: "4px",
                letterSpacing: "0.05em",
                background: filter === f ? "rgba(255,59,48,0.12)" : "transparent",
                color: filter === f ? "#FF3B30" : "#6e6e73",
                border: filter === f ? "1px solid rgba(255,59,48,0.2)" : "1px solid transparent",
                cursor: "pointer",
              }}
            >{f}</button>
          ))}
        </div>
      </div>

      {/* Events */}
      <div className="overflow-y-auto flex-1">
        {filtered.length === 0 ? (
          <div className="flex items-center justify-center h-full">
            <span style={{
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: "10px",
              color: "#3a3a3a",
              letterSpacing: "0.1em",
            }}>
              IMMUNE LOOP INITIALISING...
            </span>
          </div>
        ) : filtered.map((event, i) => {
          const sevColor = SEVERITY_COLORS[event.severity] ?? "#6e6e73"
          const isRed = event.source === "red_agent"
          return (
            <div key={event.id}
              className="flex items-center gap-2 px-4 py-1.5 border-b animate-slide-in"
              style={{
                borderColor: "rgba(229,229,234,0.04)",
                background: i === 0 ? "rgba(255,59,48,0.02)" : "transparent",
              }}
            >
              <div className="w-1.5 h-1.5 rounded-full flex-shrink-0" style={{
                background: sevColor,
                boxShadow: `0 0 4px ${sevColor}80`,
              }} />
              <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: "10px", color: "#3a3a3a", flexShrink: 0 }}>
                {event.timestamp?.slice(11, 19)}
              </span>
              <span className="px-1.5 py-0.5 rounded flex-shrink-0" style={{
                fontFamily: "'JetBrains Mono', monospace",
                fontSize: "9px",
                background: isRed ? "rgba(255,59,48,0.1)" : "rgba(255,159,10,0.1)",
                color: isRed ? "#FF3B30" : "#FF9F0A",
              }}>
                {isRed ? "RED" : "BLU"}
              </span>
              <span className="flex-1 truncate" style={{ fontSize: "11px", color: "rgba(229,229,234,0.7)" }}>
                {event.action?.replace(/_/g, " ")}
              </span>
              <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: "9px", color: "#6e6e73", flexShrink: 0 }}>
                {event.target_node?.split("_")[0]}
              </span>
              <span className="px-1.5 py-0.5 rounded flex-shrink-0" style={{
                fontFamily: "'JetBrains Mono', monospace",
                fontSize: "9px",
                background: event.outcome === "success" ? "rgba(255,59,48,0.1)" : "rgba(110,110,115,0.1)",
                color: event.outcome === "success" ? "#FF3B30" : "#6e6e73",
              }}>
                {event.outcome === "success" ? "HIT" : "MISS"}
              </span>
            </div>
          )
        })}
      </div>
    </div>
  )
}
