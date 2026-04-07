"use client"

interface Props {
  patches: Record<string, unknown>[]
}

export default function PatchLog({ patches }: Props) {
  if (patches.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-gray-600">
        <span className="font-mono text-sm">No patches recorded yet</span>
        <span className="text-xs mt-1">— approve an action from the dashboard —</span>
      </div>
    )
  }

  return (
    <div className="overflow-x-auto rounded-xl" style={{ border: "1px solid rgba(255,255,255,0.06)" }}>
      <table className="w-full text-sm">
        <thead>
          <tr style={{ background: "#0f0f1e", borderBottom: "1px solid rgba(255,255,255,0.06)" }}>
            {["Patch Action", "Vuln Class", "Target Node", "Applied At", "Effectiveness", "Status"].map(h => (
              <th key={h} className="text-left px-4 py-3 font-mono text-xs text-gray-500">{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {patches.map((p, i) => {
            const eff    = (p.effectiveness_score as number) ?? 1.0
            const pct    = Math.round(eff * 100)
            const held   = Boolean(p.held)
            const recent = i === 0

            const barColor = pct >= 70 ? "#00e5c8" : pct >= 40 ? "#ffb340" : "#ff4d6d"
            const status   = recent ? "PENDING" : held ? "HELD" : "BYPASSED"
            const statusColor =
              recent ? "#ffb340" : held ? "#00e5c8" : "#ff4d6d"
            const statusBg =
              recent
                ? "rgba(255,179,64,0.1)"
                : held
                ? "rgba(0,229,200,0.1)"
                : "rgba(255,77,109,0.1)"

            return (
              <tr
                key={String(p.id ?? i)}
                className="border-b hover:bg-white/[0.02] transition-colors"
                style={{ borderColor: "rgba(255,255,255,0.04)" }}
              >
                <td className="px-4 py-3 font-mono text-xs text-gray-300">
                  {String(p.patch_action).replace(/_/g, " ")}
                </td>
                <td className="px-4 py-3 font-mono text-xs text-[#ffb340]">
                  {String(p.vuln_class)}
                </td>
                <td className="px-4 py-3">
                  <span
                    className="font-mono text-xs px-2 py-0.5 rounded"
                    style={{ background: "rgba(77,159,255,0.1)", color: "#4d9fff" }}
                  >
                    {String(p.target_node)}
                  </span>
                </td>
                <td className="px-4 py-3 font-mono text-xs text-gray-600">
                  {String(p.applied_at ?? "").slice(0, 19).replace("T", " ")}
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    <div
                      className="flex-1 h-1.5 rounded-full min-w-[60px]"
                      style={{ background: "rgba(255,255,255,0.06)" }}
                    >
                      <div
                        className="h-full rounded-full transition-all duration-700"
                        style={{ width: `${pct}%`, background: barColor }}
                      />
                    </div>
                    <span className="font-mono text-xs" style={{ color: barColor }}>
                      {pct}%
                    </span>
                  </div>
                </td>
                <td className="px-4 py-3">
                  <span
                    className="font-mono text-xs px-2 py-0.5 rounded"
                    style={{ background: statusBg, color: statusColor }}
                  >
                    {status}
                  </span>
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
