"use client"
import { useEffect, useState } from "react"
import {
  getMemoryAttacks, getMemoryPatches,
  getMemoryStats, getExport,
} from "@/lib/api"
import VulnTable from "@/components/memory/VulnTable"
import PatchLog from "@/components/memory/PatchLog"
import type { MemoryStats } from "@/lib/types"

type Tab = "attacks" | "patches"

export default function MemoryPage() {
  const [tab, setTab]         = useState<Tab>("attacks")
  const [attacks, setAttacks] = useState<Record<string, unknown>[]>([])
  const [patches, setPatches] = useState<Record<string, unknown>[]>([])
  const [stats, setStats]     = useState<MemoryStats | null>(null)
  const [loading, setLoading] = useState(true)

  const fetchAll = async () => {
    try {
      const [a, p, s] = await Promise.all([
        getMemoryAttacks(),
        getMemoryPatches(),
        getMemoryStats(),
      ])
      setAttacks(a.data)
      setPatches(p.data)
      setStats(s.data)
    } catch (e) {
      console.error("Memory fetch failed", e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchAll()
    const id = setInterval(fetchAll, 10000)
    return () => clearInterval(id)
  }, [])

  const handleExport = async () => {
    try {
      const res = await getExport()
      const blob = new Blob([JSON.stringify(res.data, null, 2)], { type: "application/json" })
      const url  = URL.createObjectURL(blob)
      const a    = document.createElement("a")
      a.href = url; a.download = "mahoraga-export.json"; a.click()
      URL.revokeObjectURL(url)
    } catch (e) {
      console.error("Export failed", e)
    }
  }

  const summaryCards = [
    { label: "Total Attacks",    value: stats?.total_attacks ?? 0,                     color: "#ff4d6d" },
    { label: "Unique Vulns",     value: stats?.unique_vulns ?? 0,                       color: "#ffb340" },
    { label: "Total Patches",    value: stats?.total_patches ?? 0,                      color: "#00e5c8" },
    { label: "Avg Effectiveness",value: `${Math.round((stats?.avg_effectiveness ?? 0) * 100)}%`, color: "#a78bfa" },
  ]

  return (
    <div className="p-6 flex flex-col gap-6 min-h-[calc(100vh-3.5rem)]">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-mono text-2xl font-bold text-white tracking-wider">
            THREAT MEMORY
          </h1>
          <p className="text-gray-500 text-sm mt-1">
            Every discovered vulnerability stored permanently. Never learns the same lesson twice.
          </p>
        </div>

        <button
          onClick={handleExport}
          className="font-mono text-xs font-bold px-4 py-2 rounded-lg transition-all"
          style={{
            background: "rgba(0,229,200,0.08)",
            color: "#00e5c8",
            border: "1px solid rgba(0,229,200,0.2)",
          }}
        >
          ↓ EXPORT JSON
        </button>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-4 gap-3">
        {summaryCards.map(({ label, value, color }) => (
          <div
            key={label}
            className="rounded-xl p-4 text-center"
            style={{ background: "#0f0f1e", border: "1px solid rgba(255,255,255,0.06)" }}
          >
            <p className="font-mono text-3xl font-bold" style={{ color }}>{value}</p>
            <p className="text-gray-500 text-xs mt-1">{label}</p>
          </div>
        ))}
      </div>

      {/* Breach rate bar */}
      {stats && (
        <div
          className="rounded-xl p-4 flex items-center gap-4"
          style={{ background: "#0f0f1e", border: "1px solid rgba(255,255,255,0.06)" }}
        >
          <span className="text-xs text-gray-500 w-24">Breach Rate</span>
          <div className="flex-1 h-2 rounded-full" style={{ background: "rgba(255,255,255,0.06)" }}>
            <div
              className="h-full rounded-full transition-all duration-700"
              style={{
                width: `${stats.breach_rate}%`,
                background: stats.breach_rate > 50 ? "#ff4d6d" : stats.breach_rate > 25 ? "#ffb340" : "#00e5c8",
              }}
            />
          </div>
          <span className="font-mono text-sm font-bold text-white">{stats.breach_rate}%</span>
          <span className="text-xs text-gray-600">({stats.patches_held} patches held)</span>
        </div>
      )}

      {/* Tab switcher + content */}
      <div className="flex flex-col gap-4 flex-1">
        <div className="flex gap-6" style={{ borderBottom: "1px solid rgba(255,255,255,0.06)" }}>
          {(["attacks", "patches"] as Tab[]).map(t => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className="font-mono text-sm pb-3 transition-colors"
              style={{
                color: tab === t ? "#00e5c8" : "#666",
                borderBottom: tab === t ? "2px solid #00e5c8" : "2px solid transparent",
              }}
            >
              {t === "attacks" ? "ATTACK PATTERNS" : "PATCH LOG"}
              <span
                className="ml-2 text-xs px-1.5 py-0.5 rounded font-bold"
                style={{
                  background: tab === t ? "rgba(0,229,200,0.1)" : "rgba(255,255,255,0.05)",
                  color: tab === t ? "#00e5c8" : "#555",
                }}
              >
                {t === "attacks" ? attacks.length : patches.length}
              </span>
            </button>
          ))}
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-20">
            <span className="font-mono text-gray-600 animate-pulse">Loading threat memory...</span>
          </div>
        ) : tab === "attacks" ? (
          <VulnTable attacks={attacks} />
        ) : (
          <PatchLog patches={patches} />
        )}
      </div>
    </div>
  )
}
