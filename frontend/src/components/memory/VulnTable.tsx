"use client"
import { useState, useMemo } from "react"

interface Props {
  attacks: Record<string, unknown>[]
}

type SortKey = "action" | "target_node" | "vuln_class" | "attempts" | "timestamp"
type SortDir = "asc" | "desc"

export default function VulnTable({ attacks }: Props) {
  const [sortKey, setSortKey]   = useState<SortKey>("attempts")
  const [sortDir, setSortDir]   = useState<SortDir>("desc")
  const [search, setSearch]     = useState("")

  const handleSort = (key: SortKey) => {
    if (key === sortKey) setSortDir(d => d === "asc" ? "desc" : "asc")
    else { setSortKey(key); setSortDir("desc") }
  }

  const filtered = useMemo(() => {
    const q = search.toLowerCase()
    return attacks.filter(a =>
      !q ||
      String(a.action).toLowerCase().includes(q) ||
      String(a.vuln_class).toLowerCase().includes(q) ||
      String(a.target_node).toLowerCase().includes(q)
    )
  }, [attacks, search])

  const sorted = useMemo(() => {
    return [...filtered].sort((a, b) => {
      const av = a[sortKey] as string | number
      const bv = b[sortKey] as string | number
      if (av < bv) return sortDir === "asc" ? -1 : 1
      if (av > bv) return sortDir === "asc" ? 1 : -1
      return 0
    })
  }, [filtered, sortKey, sortDir])

  const cols: { key: SortKey; label: string }[] = [
    { key: "action",      label: "Action" },
    { key: "target_node", label: "Target Node" },
    { key: "vuln_class",  label: "Vuln Class" },
    { key: "attempts",    label: "Attempts" },
    { key: "timestamp",   label: "First Seen" },
  ]

  const SortIcon = ({ k }: { k: SortKey }) => (
    <span className="ml-1 opacity-40">
      {sortKey === k ? (sortDir === "asc" ? "↑" : "↓") : "↕"}
    </span>
  )

  if (attacks.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-gray-600">
        <span className="font-mono text-sm">No attacks recorded yet</span>
        <span className="text-xs mt-1">— immune loop initialising —</span>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-3">
      <input
        type="text"
        placeholder="Search by action or vuln class..."
        value={search}
        onChange={e => setSearch(e.target.value)}
        className="w-full px-3 py-2 rounded-lg text-sm font-mono text-gray-300 placeholder-gray-600 outline-none"
        style={{ background: "#0f0f1e", border: "1px solid rgba(255,255,255,0.08)" }}
      />

      <div className="overflow-x-auto rounded-xl" style={{ border: "1px solid rgba(255,255,255,0.06)" }}>
        <table className="w-full text-sm">
          <thead>
            <tr style={{ background: "#0f0f1e", borderBottom: "1px solid rgba(255,255,255,0.06)" }}>
              {cols.map(({ key, label }) => (
                <th
                  key={key}
                  onClick={() => handleSort(key)}
                  className="text-left px-4 py-3 font-mono text-xs text-gray-500 cursor-pointer hover:text-gray-300 transition-colors select-none"
                >
                  {label}<SortIcon k={key} />
                </th>
              ))}
              <th className="text-left px-4 py-3 font-mono text-xs text-gray-500">Breach</th>
            </tr>
          </thead>
          <tbody>
            {sorted.map((attack, i) => {
              const breach = Boolean(attack.breach_success)
              return (
                <tr
                  key={String(attack.id ?? i)}
                  className="border-b transition-colors hover:bg-white/[0.02]"
                  style={{
                    borderColor: "rgba(255,255,255,0.04)",
                    background: breach ? "rgba(255,77,109,0.04)" : "transparent",
                  }}
                >
                  <td className="px-4 py-2.5 font-mono text-xs text-gray-300">
                    {String(attack.action).replace(/_/g, " ")}
                  </td>
                  <td className="px-4 py-2.5">
                    <span
                      className="font-mono text-xs px-2 py-0.5 rounded"
                      style={{ background: "rgba(77,159,255,0.1)", color: "#4d9fff" }}
                    >
                      {String(attack.target_node)}
                    </span>
                  </td>
                  <td className="px-4 py-2.5 font-mono text-xs text-[#ffb340]">
                    {String(attack.vuln_class)}
                  </td>
                  <td className="px-4 py-2.5 font-mono text-sm font-bold text-white">
                    {String(attack.attempts)}
                  </td>
                  <td className="px-4 py-2.5 font-mono text-xs text-gray-600">
                    {String(attack.timestamp ?? "").slice(0, 19).replace("T", " ")}
                  </td>
                  <td className="px-4 py-2.5">
                    <span
                      className="font-mono text-xs px-2 py-0.5 rounded"
                      style={{
                        background: breach ? "rgba(255,77,109,0.15)" : "rgba(0,229,200,0.08)",
                        color: breach ? "#ff4d6d" : "#00e5c8",
                      }}
                    >
                      {breach ? "YES" : "NO"}
                    </span>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
