"use client"
import type { AgentStatus } from "@/lib/types"
import { VULN_COLORS } from "@/lib/constants"

interface Props {
  status: AgentStatus["blue"] | undefined
  governor: AgentStatus["governor"] | undefined
}

export default function BlueAgentPanel({ status, governor }: Props) {
  const patches = (status?.patches_applied ?? []) as Record<string, string>[]
  const overrides = (governor?.overrides ?? []) as Record<string, string>[]
  const blocks = governor?.override_count ?? 0

  return (
    <div
      className="rounded-xl p-5 flex flex-col gap-4 h-full"
      style={{ background: "#0f0f1e", border: "1px solid rgba(0,229,200,0.2)" }}
    >
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <p className="font-mono text-xs text-[#00e5c8] tracking-widest">BLUE AGENT</p>
          <p className="font-mono text-sm text-white font-bold">// DEFENDER</p>
        </div>
        <span
          className="text-xs font-mono px-2 py-1 rounded"
          style={{
            background: status?.is_trained ? "rgba(0,229,200,0.1)" : "rgba(255,179,64,0.1)",
            color: status?.is_trained ? "#00e5c8" : "#ffb340",
            border: `1px solid ${status?.is_trained ? "#00e5c820" : "#ffb34020"}`,
          }}
        >
          {status?.is_trained ? "MODEL TRAINED" : "UNTRAINED"}
        </span>
      </div>

      {/* Stat grid */}
      <div className="grid grid-cols-2 gap-3">
        {[
          { label: "Patches Applied", value: status?.patch_count ?? 0, color: "#00e5c8" },
          { label: "Training Samples", value: status?.training_samples ?? 0, color: "#4d9fff" },
          { label: "Governor Blocks", value: blocks, color: blocks > 3 ? "#ff4d6d" : "#ffb340" },
          { label: "Active Patches", value: patches.length, color: "#a78bfa" },
        ].map(({ label, value, color }) => (
          <div
            key={label}
            className="rounded-lg p-3"
            style={{ background: "rgba(0,229,200,0.05)", border: "1px solid rgba(0,229,200,0.1)" }}
          >
            <p className="text-gray-500 text-xs mb-1">{label}</p>
            <p className="font-mono font-bold text-xl" style={{ color }}>
              {value}
            </p>
          </div>
        ))}
      </div>

      {/* Governor warning */}
      {blocks > 3 && (
        <div
          className="rounded-lg px-3 py-2 flex items-center gap-2"
          style={{ background: "rgba(255,179,64,0.08)", border: "1px solid rgba(255,179,64,0.2)" }}
        >
          <span className="text-[#ffb340]">⚠</span>
          <span className="text-xs text-[#ffb340]">
            Governor has intervened {blocks} times — autoimmune response elevated
          </span>
        </div>
      )}

      {/* Recent governor overrides */}
      {overrides.length > 0 && (
        <div>
          <p className="text-xs text-gray-500 mb-2">Recent Governor Actions</p>
          <div className="flex flex-col gap-1">
            {overrides.slice(0, 3).map((o, i) => (
              <div
                key={i}
                className="flex items-center gap-2 text-xs rounded px-2 py-1"
                style={{ background: "rgba(255,179,64,0.06)" }}
              >
                <span className="text-[#ffb340] font-mono">BLOCKED</span>
                <span className="text-gray-400">{o.action}</span>
                <span className="text-gray-600">→</span>
                <span className="text-gray-300">{o.target}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recent patches */}
      <div className="flex-1">
        <p className="text-xs text-gray-500 mb-2">Recent Patches</p>
        <div className="flex flex-col gap-1 overflow-y-auto max-h-40">
          {patches.length === 0 ? (
            <p className="text-xs text-gray-600 italic">No patches applied yet</p>
          ) : (
            patches.slice(-5).reverse().map((p, i) => {
              const vuln = p.vuln_class as string
              const color = VULN_COLORS[vuln] ?? "#888"
              return (
                <div
                  key={i}
                  className="flex items-center gap-2 text-xs rounded px-2 py-1.5"
                  style={{ background: "rgba(0,229,200,0.04)", border: "1px solid rgba(0,229,200,0.08)" }}
                >
                  <span
                    className="w-1.5 h-1.5 rounded-full flex-shrink-0"
                    style={{ background: color }}
                  />
                  <span className="font-mono text-gray-300">{p.patch_action}</span>
                  <span className="text-gray-600">→</span>
                  <span style={{ color }}>{vuln}</span>
                  <span className="text-gray-600 ml-auto">{p.target_node}</span>
                </div>
              )
            })
          )}
        </div>
      </div>

      {/* Patch effectiveness bars */}
      {patches.length > 0 && (
        <div>
          <p className="text-xs text-gray-500 mb-2">Patch Effectiveness</p>
          <div className="flex flex-col gap-1.5">
            {patches.slice(-4).reverse().map((p, i) => {
              const eff = (p.effectiveness as number) ?? 1.0
              const pct = Math.round(eff * 100)
              const barColor = pct >= 70 ? "#00e5c8" : pct >= 40 ? "#ffb340" : "#ff4d6d"
              return (
                <div key={i} className="flex items-center gap-2">
                  <span className="font-mono text-xs text-gray-500 w-20 truncate">{p.vuln_class}</span>
                  <div className="flex-1 h-1.5 rounded-full" style={{ background: "rgba(255,255,255,0.06)" }}>
                    <div
                      className="h-full rounded-full transition-all duration-700"
                      style={{ width: `${pct}%`, background: barColor }}
                    />
                  </div>
                  <span className="font-mono text-xs" style={{ color: barColor }}>{pct}%</span>
                </div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}
