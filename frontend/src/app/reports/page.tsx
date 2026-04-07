"use client"
import { useEffect, useState } from "react"
import axios from "axios"
import { API_BASE, NODE_COLORS, SEVERITY_COLORS } from "@/lib/constants"

interface IncidentReport {
  id: string
  timestamp: string
  status: string
  node: string
  vuln_class: string
  action: string
  risk_before: number
  risk_after: number
  risk_reduction: number
  patch_action: string
  patch_applied: boolean
  governor_blocked: boolean
  threat_summary: string
  attack_technique: string
  attack_detail: string
  affected_component: string
  patch_summary: string
  patch_technique: string
  prevention: string
  severity: string
  confidence: number
}

function SeverityBadge({ severity }: { severity: string }) {
  const color = SEVERITY_COLORS[severity?.toLowerCase()] ?? "#888"
  return (
    <span
      className="font-mono text-xs px-2 py-0.5 rounded font-bold"
      style={{ background: `${color}20`, color, border: `1px solid ${color}40` }}
    >
      {severity}
    </span>
  )
}

function RiskArrow({ before, after }: { before: number; after: number }) {
  const reduction = before - after
  return (
    <div className="flex items-center gap-2 font-mono text-sm">
      <span style={{ color: before > 70 ? "#ff4d6d" : before > 40 ? "#ffb340" : "#00e5c8" }}>
        {before.toFixed(0)}
      </span>
      <span className="text-gray-600">→</span>
      <span style={{ color: after > 70 ? "#ff4d6d" : after > 40 ? "#ffb340" : "#00e5c8" }}>
        {after.toFixed(0)}
      </span>
      {reduction > 0 && (
        <span className="text-xs text-[#00e5c8]">(-{reduction.toFixed(0)})</span>
      )}
    </div>
  )
}

function ReportCard({ report, expanded, onToggle }: {
  report: IncidentReport
  expanded: boolean
  onToggle: () => void
}) {
  const nodeColor = NODE_COLORS[report.node] ?? "#888"
  const ts = report.timestamp?.slice(0, 19).replace("T", " ")

  return (
    <div
      className="rounded-xl overflow-hidden transition-all duration-300"
      style={{
        background: "#0d0d1a",
        border: `1px solid ${expanded ? "rgba(0,229,200,0.2)" : "rgba(255,255,255,0.06)"}`,
      }}
    >
      {/* Header row — always visible */}
      <button
        onClick={onToggle}
        className="w-full flex items-center gap-4 px-5 py-4 text-left hover:bg-white/[0.02] transition-colors"
      >
        {/* Node color dot */}
        <div
          className="w-2.5 h-2.5 rounded-full flex-shrink-0"
          style={{ background: nodeColor, boxShadow: `0 0 6px ${nodeColor}` }}
        />

        {/* Timestamp */}
        <span className="font-mono text-xs text-gray-600 w-36 flex-shrink-0">{ts}</span>

        {/* Severity */}
        <SeverityBadge severity={report.severity} />

        {/* Attack technique */}
        <span className="font-mono text-sm text-white flex-1 truncate">
          {report.attack_technique}
        </span>

        {/* Node */}
        <span
          className="font-mono text-xs px-2 py-0.5 rounded flex-shrink-0"
          style={{ background: `${nodeColor}15`, color: nodeColor }}
        >
          {report.node}
        </span>

        {/* Risk arrow */}
        <div className="flex-shrink-0">
          <RiskArrow before={report.risk_before} after={report.risk_after} />
        </div>

        {/* Status */}
        <span
          className="font-mono text-xs px-2 py-0.5 rounded flex-shrink-0"
          style={{
            background: report.patch_applied ? "rgba(0,229,200,0.1)" : "rgba(255,179,64,0.1)",
            color: report.patch_applied ? "#00e5c8" : "#ffb340",
          }}
        >
          {report.patch_applied ? "PATCHED" : "PENDING"}
        </span>

        {/* Expand arrow */}
        <span
          className="text-gray-600 flex-shrink-0 transition-transform duration-200"
          style={{ transform: expanded ? "rotate(180deg)" : "rotate(0deg)" }}
        >
          ▾
        </span>
      </button>

      {/* Expanded detail */}
      {expanded && (
        <div
          className="px-5 pb-5 flex flex-col gap-5"
          style={{ borderTop: "1px solid rgba(255,255,255,0.05)" }}
        >
          {/* Threat summary */}
          <div className="pt-4">
            <p className="font-mono text-xs text-[#ff4d6d] tracking-widest mb-2">THREAT SUMMARY</p>
            <p className="text-gray-300 text-sm leading-relaxed">{report.threat_summary}</p>
          </div>

          {/* Two columns: Attack | Patch */}
          <div className="grid grid-cols-2 gap-4">

            {/* Attack column */}
            <div
              className="rounded-lg p-4 flex flex-col gap-3"
              style={{ background: "rgba(255,77,109,0.05)", border: "1px solid rgba(255,77,109,0.12)" }}
            >
              <div className="flex items-center gap-2">
                <span className="text-[#ff4d6d] text-xs">⚔</span>
                <span className="font-mono text-xs text-[#ff4d6d] tracking-widest">ATTACK</span>
              </div>

              <div>
                <p className="text-xs text-gray-500 mb-1">Technique</p>
                <p className="font-mono text-sm text-white font-bold">{report.attack_technique}</p>
              </div>

              <div>
                <p className="text-xs text-gray-500 mb-1">How it works</p>
                <p className="text-gray-300 text-xs leading-relaxed">{report.attack_detail}</p>
              </div>

              <div>
                <p className="text-xs text-gray-500 mb-1">Affected component</p>
                <p className="font-mono text-xs text-[#ffb340]">{report.affected_component}</p>
              </div>

              <div className="flex gap-2 flex-wrap mt-1">
                <span
                  className="font-mono text-xs px-2 py-0.5 rounded"
                  style={{ background: "rgba(255,77,109,0.1)", color: "#ff4d6d" }}
                >
                  {report.vuln_class}
                </span>
                <span
                  className="font-mono text-xs px-2 py-0.5 rounded"
                  style={{ background: "rgba(255,179,64,0.1)", color: "#ffb340" }}
                >
                  confidence: {report.confidence}%
                </span>
              </div>
            </div>

            {/* Patch column */}
            <div
              className="rounded-lg p-4 flex flex-col gap-3"
              style={{ background: "rgba(0,229,200,0.05)", border: "1px solid rgba(0,229,200,0.12)" }}
            >
              <div className="flex items-center gap-2">
                <span className="text-[#00e5c8] text-xs">🛡</span>
                <span className="font-mono text-xs text-[#00e5c8] tracking-widest">PATCH APPLIED</span>
              </div>

              <div>
                <p className="text-xs text-gray-500 mb-1">Technique</p>
                <p className="font-mono text-sm text-white font-bold">{report.patch_technique}</p>
              </div>

              <div>
                <p className="text-xs text-gray-500 mb-1">What was done</p>
                <p className="text-gray-300 text-xs leading-relaxed">{report.patch_summary}</p>
              </div>

              <div>
                <p className="text-xs text-gray-500 mb-1">Risk reduction</p>
                <div className="flex items-center gap-3">
                  <div
                    className="flex-1 h-1.5 rounded-full"
                    style={{ background: "rgba(255,255,255,0.06)" }}
                  >
                    <div
                      className="h-full rounded-full transition-all duration-700"
                      style={{
                        width: `${Math.min(100, (report.risk_reduction / report.risk_before) * 100)}%`,
                        background: "#00e5c8",
                      }}
                    />
                  </div>
                  <span className="font-mono text-xs text-[#00e5c8]">
                    -{report.risk_reduction.toFixed(0)} pts
                  </span>
                </div>
              </div>

              {report.governor_blocked && (
                <div
                  className="rounded px-2 py-1.5 text-xs"
                  style={{ background: "rgba(255,179,64,0.1)", color: "#ffb340" }}
                >
                  ⚠ Governor intervened on this action
                </div>
              )}
            </div>
          </div>

          {/* Prevention */}
          <div
            className="rounded-lg px-4 py-3 flex gap-3 items-start"
            style={{ background: "rgba(167,139,250,0.06)", border: "1px solid rgba(167,139,250,0.12)" }}
          >
            <span className="text-[#a78bfa] text-sm flex-shrink-0">💡</span>
            <div>
              <p className="font-mono text-xs text-[#a78bfa] tracking-widest mb-1">PREVENTION</p>
              <p className="text-gray-300 text-xs leading-relaxed">{report.prevention}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default function ReportsPage() {
  const [reports, setReports]     = useState<IncidentReport[]>([])
  const [loading, setLoading]     = useState(true)
  const [expandedId, setExpandedId] = useState<string | null>(null)
  const [filter, setFilter]       = useState<string>("ALL")

  const fetchReports = async () => {
    try {
      const res = await axios.get(`${API_BASE}/api/reports`)
      setReports(res.data)
    } catch {
      // fail silently
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchReports()
    const id = setInterval(fetchReports, 5000)
    return () => clearInterval(id)
  }, [])

  const severities = ["ALL", "CRITICAL", "HIGH", "MEDIUM", "LOW"]

  const filtered = reports.filter(r =>
    filter === "ALL" || r.severity === filter
  )

  const stats = {
    total: reports.length,
    patched: reports.filter(r => r.patch_applied).length,
    critical: reports.filter(r => r.severity === "CRITICAL").length,
    avgReduction: reports.length
      ? Math.round(reports.reduce((s, r) => s + r.risk_reduction, 0) / reports.length)
      : 0,
  }

  return (
    <div className="p-6 flex flex-col gap-6 min-h-[calc(100vh-3.5rem)]">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-mono text-2xl font-bold text-white tracking-wider">
            INCIDENT REPORTS
          </h1>
          <p className="text-gray-500 text-sm mt-1">
            Full attack &amp; patch analysis — generated by Mahoraga AI
          </p>
        </div>

        <button
          onClick={fetchReports}
          className="font-mono text-xs px-4 py-2 rounded-lg transition-all"
          style={{
            background: "rgba(0,229,200,0.08)",
            color: "#00e5c8",
            border: "1px solid rgba(0,229,200,0.2)",
          }}
        >
          ↻ REFRESH
        </button>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-4 gap-3">
        {[
          { label: "Total Incidents",   value: stats.total,        color: "#ff4d6d" },
          { label: "Patched",           value: stats.patched,       color: "#00e5c8" },
          { label: "Critical",          value: stats.critical,      color: "#ff4d6d" },
          { label: "Avg Risk Reduction",value: `-${stats.avgReduction}`, color: "#a78bfa" },
        ].map(({ label, value, color }) => (
          <div
            key={label}
            className="rounded-xl p-4 text-center"
            style={{ background: "#0d0d1a", border: "1px solid rgba(255,255,255,0.06)" }}
          >
            <p className="font-mono text-3xl font-bold" style={{ color }}>{value}</p>
            <p className="text-gray-500 text-xs mt-1">{label}</p>
          </div>
        ))}
      </div>

      {/* Severity filter */}
      <div className="flex gap-2">
        {severities.map(s => (
          <button
            key={s}
            onClick={() => setFilter(s)}
            className="font-mono text-xs px-3 py-1.5 rounded-lg transition-all"
            style={{
              background: filter === s ? "rgba(0,229,200,0.12)" : "rgba(255,255,255,0.04)",
              color: filter === s ? "#00e5c8" : "#666",
              border: `1px solid ${filter === s ? "rgba(0,229,200,0.3)" : "rgba(255,255,255,0.06)"}`,
            }}
          >
            {s}
          </button>
        ))}
        <span className="ml-auto font-mono text-xs text-gray-600 self-center">
          {filtered.length} report{filtered.length !== 1 ? "s" : ""}
        </span>
      </div>

      {/* Reports list */}
      {loading ? (
        <div className="flex items-center justify-center py-20">
          <span className="font-mono text-gray-600 animate-pulse">
            Loading incident reports...
          </span>
        </div>
      ) : filtered.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-24 gap-3">
          <span className="font-mono text-4xl">🛡</span>
          <span className="font-mono text-gray-500 text-sm">No incidents recorded yet</span>
          <span className="text-gray-700 text-xs">
            Approve an action from the Dashboard to generate the first report
          </span>
        </div>
      ) : (
        <div className="flex flex-col gap-3">
          {filtered.map(report => (
            <ReportCard
              key={report.id}
              report={report}
              expanded={expandedId === report.id}
              onToggle={() =>
                setExpandedId(expandedId === report.id ? null : report.id)
              }
            />
          ))}
        </div>
      )}
    </div>
  )
}
