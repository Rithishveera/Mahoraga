"use client"
import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { getMemoryStats } from "@/lib/api"
import type { MemoryStats } from "@/lib/types"

export default function LandingPage() {
  const router = useRouter()
  const [stats, setStats] = useState<MemoryStats>({
    total_attacks: 0, total_patches: 0, unique_vulns: 0,
    breach_rate: 0, avg_effectiveness: 0, patches_held: 0,
  })
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
    const fetch = async () => {
      try { const r = await getMemoryStats(); setStats(r.data) } catch { }
    }
    fetch()
    const id = setInterval(fetch, 5000)
    return () => clearInterval(id)
  }, [])

  return (
    <div className="min-h-0 h-[calc(100vh-48px)] flex flex-col items-center justify-center relative overflow-hidden px-6"
      style={{ background: "#121212" }}>

      {/* Subtle grid */}
      <div className="absolute inset-0 pointer-events-none" style={{
        backgroundImage: `linear-gradient(rgba(255,59,48,0.03) 1px, transparent 1px),
                          linear-gradient(90deg, rgba(255,59,48,0.03) 1px, transparent 1px)`,
        backgroundSize: "80px 80px",
      }} />

      {/* Glow */}
      <div className="absolute pointer-events-none" style={{
        top: "30%", left: "50%", transform: "translateX(-50%)",
        width: 500, height: 400,
        background: "radial-gradient(ellipse, rgba(255,59,48,0.06) 0%, transparent 70%)",
        animation: "breathe 5s ease-in-out infinite",
      }} />

      {/* Scan line */}
      <div className="absolute inset-x-0 overflow-hidden pointer-events-none" style={{ top: 0, bottom: 0 }}>
        <div style={{
          position: "absolute", left: 0, right: 0, height: "1px",
          background: "linear-gradient(90deg, transparent, rgba(255,59,48,0.15), transparent)",
          animation: "scan 8s linear infinite",
        }} />
      </div>

      <div className={`relative z-10 text-center max-w-2xl transition-all duration-700 ${mounted ? "opacity-100 translate-y-0" : "opacity-0 translate-y-3"}`}>

        {/* Eyebrow */}
        <div className="flex items-center justify-center gap-3 mb-6">
          <div className="h-px w-12" style={{ background: "linear-gradient(90deg, transparent, rgba(255,59,48,0.4))" }} />
          <span style={{
            fontFamily: "'JetBrains Mono', monospace",
            fontSize: "10px",
            letterSpacing: "0.3em",
            color: "rgba(255,59,48,0.6)",
          }}>
            ADAPTIVE CYBER-IMMUNE SYSTEM
          </span>
          <div className="h-px w-12" style={{ background: "linear-gradient(90deg, rgba(255,59,48,0.4), transparent)" }} />
        </div>

        {/* Title */}
        <h1 style={{
          fontFamily: "'Syne', sans-serif",
          fontSize: "clamp(64px, 13vw, 112px)",
          fontWeight: 800,
          letterSpacing: "-0.02em",
          lineHeight: 0.95,
          color: "#E5E5EA",
          marginBottom: "24px",
          animation: "flicker 8s ease-in-out infinite",
        }}>
          MAHORAGA
        </h1>

        {/* Red underline */}
        <div style={{
          width: "80px",
          height: "3px",
          background: "#FF3B30",
          margin: "0 auto 24px",
          boxShadow: "0 0 12px rgba(255,59,48,0.6)",
        }} />

        {/* Tagline */}
        <p style={{
          fontFamily: "'DM Sans', sans-serif",
          fontSize: "16px",
          color: "#6e6e73",
          maxWidth: "420px",
          margin: "0 auto 40px",
          lineHeight: 1.7,
        }}>
          Adapts to every attack.{" "}
          <span style={{ color: "rgba(255,59,48,0.8)", fontStyle: "italic" }}>
            Never defeated by the same technique twice.
          </span>
        </p>

        {/* Stats */}
        <div className="grid grid-cols-3 gap-3 mb-10" style={{ maxWidth: "480px", margin: "0 auto 40px" }}>
          {[
            { label: "Attacks Run", value: stats.total_attacks, color: "#FF3B30" },
            { label: "Vulns Found", value: stats.unique_vulns, color: "#FF9F0A" },
            { label: "Patches Applied", value: stats.total_patches, color: "#E5E5EA" },
          ].map(({ label, value, color }) => (
            <div key={label} className="rounded-lg p-4 text-center" style={{
              background: "#1e1e1e",
              border: "1px solid rgba(229,229,234,0.06)",
            }}>
              <div style={{
                fontFamily: "'JetBrains Mono', monospace",
                fontSize: "28px",
                fontWeight: 700,
                color,
                textShadow: `0 0 20px ${color}40`,
                lineHeight: 1,
                marginBottom: "6px",
              }}>
                {value.toLocaleString()}
              </div>
              <div style={{
                fontFamily: "'JetBrains Mono', monospace",
                fontSize: "9px",
                letterSpacing: "0.15em",
                color: "#6e6e73",
              }}>
                {label.toUpperCase()}
              </div>
            </div>
          ))}
        </div>

        {/* CTA */}
        <button
          onClick={() => router.push("/dashboard")}
          className="px-10 py-3.5 rounded-lg font-bold transition-all duration-200"
          style={{
            fontFamily: "'Syne', sans-serif",
            fontSize: "13px",
            letterSpacing: "0.12em",
            background: "#FF3B30",
            color: "#121212",
            border: "none",
            boxShadow: "0 0 30px rgba(255,59,48,0.3)",
          }}
          onMouseEnter={e => {
            (e.target as HTMLElement).style.boxShadow = "0 0 40px rgba(255,59,48,0.5)"
              ; (e.target as HTMLElement).style.transform = "translateY(-1px)"
          }}
          onMouseLeave={e => {
            (e.target as HTMLElement).style.boxShadow = "0 0 30px rgba(255,59,48,0.3)"
              ; (e.target as HTMLElement).style.transform = "translateY(0)"
          }}
        >
          LAUNCH DASHBOARD →
        </button>

        {/* Bio text */}
        <p style={{
          fontFamily: "'DM Sans', sans-serif",
          fontSize: "12px",
          color: "#3a3a3a",
          maxWidth: "380px",
          margin: "32px auto 0",
          lineHeight: 1.9,
        }}>
          Like your immune system — never waits to get sick.
          Red Agent attacks. Blue Agent defends. Governor prevents self-harm.
        </p>
      </div>
    </div>
  )
}