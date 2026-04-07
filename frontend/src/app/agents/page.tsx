"use client"
import { useEffect, useState } from "react"
import { useWebSocket } from "@/hooks/useWebSocket"
import { getAgentStatus, startRedAgent, stopRedAgent } from "@/lib/api"
import RedAgentPanel from "@/components/agents/RedAgentPanel"
import BlueAgentPanel from "@/components/agents/BlueAgentPanel"
import type { AgentStatus } from "@/lib/types"

export default function AgentsPage() {
  const { agentStatus: wsStatus } = useWebSocket()
  const [status, setStatus] = useState<AgentStatus | null>(null)
  const [toggling, setToggling] = useState(false)

  // Merge WebSocket data with polling fallback
  useEffect(() => {
    if (wsStatus) { setStatus(wsStatus); return }
    const fetch = async () => {
      try {
        const res = await getAgentStatus()
        setStatus(res.data)
      } catch {}
    }
    fetch()
    const id = setInterval(fetch, 5000)
    return () => clearInterval(id)
  }, [wsStatus])

  const isRunning = status?.red?.is_running ?? false

  const handleToggle = async () => {
    setToggling(true)
    try {
      if (isRunning) await stopRedAgent()
      else await startRedAgent()
      // Optimistically flip
      setStatus(prev =>
        prev ? { ...prev, red: { ...prev.red, is_running: !isRunning } } : prev
      )
    } catch (e) {
      console.error("Toggle failed", e)
    } finally {
      setToggling(false)
    }
  }

  return (
    <div className="p-6 flex flex-col gap-6 min-h-[calc(100vh-3.5rem)]">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-mono text-2xl font-bold text-white tracking-wider">
            AGENT MONITOR
          </h1>
          <p className="text-gray-500 text-sm mt-1">
            Red attacks. Blue defends. Governor prevents self-harm.
          </p>
        </div>

        <button
          onClick={handleToggle}
          disabled={toggling}
          className="font-mono text-sm font-bold px-5 py-2.5 rounded-lg transition-all duration-200 disabled:opacity-50"
          style={{
            background: isRunning ? "rgba(255,77,109,0.12)" : "rgba(0,229,200,0.12)",
            color: isRunning ? "#ff4d6d" : "#00e5c8",
            border: `1px solid ${isRunning ? "#ff4d6d40" : "#00e5c840"}`,
          }}
        >
          {toggling ? "..." : isRunning ? "⏹ STOP RED AGENT" : "▶ START RED AGENT"}
        </button>
      </div>

      {/* Episode summary bar */}
      <div
        className="grid grid-cols-4 gap-3 rounded-xl p-4"
        style={{ background: "#0f0f1e", border: "1px solid rgba(255,255,255,0.06)" }}
      >
        {[
          { label: "Episodes Run",    value: status?.red?.episode_count ?? 0,       color: "#ff4d6d" },
          { label: "Total Vulns",     value: status?.red?.total_vulns_found ?? 0,    color: "#ffb340" },
          { label: "Patches Applied", value: status?.blue?.patch_count ?? 0,         color: "#00e5c8" },
          { label: "Gov. Blocks",     value: status?.governor?.override_count ?? 0,  color: "#a78bfa" },
        ].map(({ label, value, color }) => (
          <div key={label} className="text-center">
            <p className="font-mono text-2xl font-bold" style={{ color }}>{value}</p>
            <p className="text-gray-500 text-xs mt-1">{label}</p>
          </div>
        ))}
      </div>

      {/* Two-column agent panels */}
      <div className="grid grid-cols-2 gap-4 flex-1">
        <RedAgentPanel status={status?.red} />
        <BlueAgentPanel status={status?.blue} governor={status?.governor} />
      </div>
    </div>
  )
}
