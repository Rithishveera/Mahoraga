"use client"
import { useEffect, useState } from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { useWebSocket } from "@/hooks/useWebSocket"

export function Navbar() {
  const pathname = usePathname()
  const { connected, riskScore, agentStatus } = useWebSocket()
  const [localScore, setLocalScore] = useState(0)

  useEffect(() => {
    if (riskScore) setLocalScore(riskScore.score)
  }, [riskScore])

  const isRunning = agentStatus?.red?.is_running ?? false
  const riskColor = localScore < 40 ? "#6e6e73" : localScore < 70 ? "#FF9F0A" : "#FF3B30"

  const navLinks = [
    { href: "/dashboard", label: "Dashboard" },
    { href: "/agents",    label: "Agents" },
    { href: "/memory",    label: "Memory" },
    { href: "/reports",   label: "Reports" },
  ]

  return (
    <nav
      style={{
        background: "#121212",
        borderBottom: "1px solid rgba(229,229,234,0.06)",
      }}
      className="sticky top-0 z-50 flex items-center justify-between px-8 h-12"
    >
      {/* Logo */}
      <Link href="/" className="flex items-center gap-3">
        <div className="relative w-2 h-4">
          <div className="absolute inset-0" style={{
            background: "#FF3B30",
            clipPath: "polygon(50% 0%, 100% 100%, 0% 100%)",
            animation: "pulseCrimson 2s ease-in-out infinite",
          }} />
        </div>
        <span style={{
          fontFamily: "'Syne', sans-serif",
          fontWeight: 800,
          fontSize: "15px",
          letterSpacing: "0.15em",
          color: "#E5E5EA",
        }}>
          MAHORAGA
        </span>
      </Link>

      {/* Nav */}
      <div className="flex items-center gap-1">
        {navLinks.map(({ href, label }) => {
          const active = pathname.startsWith(href)
          return (
            <Link
              key={href}
              href={href}
              style={{
                fontFamily: "'DM Sans', sans-serif",
                fontSize: "13px",
                fontWeight: active ? 600 : 400,
                color: active ? "#E5E5EA" : "#6e6e73",
                padding: "6px 14px",
                borderRadius: "6px",
                background: active ? "rgba(229,229,234,0.06)" : "transparent",
                borderBottom: active ? "2px solid #FF3B30" : "2px solid transparent",
                transition: "all 0.15s ease",
              }}
            >
              {label}
            </Link>
          )
        })}
      </div>

      {/* Right */}
      <div className="flex items-center gap-5">
        {/* Status */}
        <div className="flex items-center gap-2">
          <div className="relative w-2 h-2">
            {isRunning && (
              <div className="absolute inset-0 rounded-full" style={{
                background: "#FF3B30",
                animation: "attackPulse 1.5s ease-out infinite",
              }} />
            )}
            <div className="w-2 h-2 rounded-full" style={{
              background: isRunning ? "#FF3B30" : "#3a3a3a",
              boxShadow: isRunning ? "0 0 8px #FF3B30" : "none",
            }} />
          </div>
          <span style={{
            fontFamily: "'JetBrains Mono', monospace",
            fontSize: "10px",
            letterSpacing: "0.08em",
            color: isRunning ? "rgba(255,59,48,0.8)" : "#3a3a3a",
          }}>
            {isRunning ? "IMMUNE ACTIVE" : "IDLE"}
          </span>
        </div>

        <div className="w-px h-4" style={{ background: "rgba(229,229,234,0.08)" }} />

        {/* Risk */}
        <div className="flex items-center gap-2 px-3 py-1 rounded" style={{
          background: `${riskColor}10`,
          border: `1px solid ${riskColor}30`,
        }}>
          <span style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: "9px", color: "#6e6e73", letterSpacing: "0.1em" }}>RISK</span>
          <span style={{
            fontFamily: "'JetBrains Mono', monospace",
            fontSize: "13px",
            fontWeight: 700,
            color: riskColor,
            textShadow: `0 0 8px ${riskColor}80`,
            minWidth: "22px",
          }}>
            {localScore.toFixed(0)}
          </span>
        </div>

        {/* WS dot */}
        <div className="w-1.5 h-1.5 rounded-full" style={{
          background: connected ? "#30d158" : "#FF3B30",
          boxShadow: connected ? "0 0 5px #30d158" : "0 0 5px #FF3B30",
        }} />
      </div>
    </nav>
  )
}
export default Navbar
