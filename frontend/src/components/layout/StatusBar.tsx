"use client"
import { useWebSocket } from "@/hooks/useWebSocket"

export function StatusBar() {
  const { connected, events, agentStatus } = useWebSocket()
  const lastEvent = events[0]
  const episodeCount = agentStatus?.red?.episode_count ?? 0

  return (
    <div className="flex items-center gap-5 px-8 py-1.5" style={{
      background: "#1a1a1a",
      borderBottom: "1px solid rgba(229,229,234,0.05)",
      fontFamily: "'JetBrains Mono', monospace",
      fontSize: "10px",
      letterSpacing: "0.05em",
    }}>
      <div className="flex items-center gap-1.5">
        <div className="w-1.5 h-1.5 rounded-full" style={{
          background: connected ? "#30d158" : "#FF3B30",
          boxShadow: connected ? "0 0 4px #30d158" : "none",
        }} />
        <span style={{ color: connected ? "rgba(48,209,88,0.7)" : "rgba(255,59,48,0.7)" }}>
          WS: {connected ? "CONNECTED" : "DISCONNECTED"}
        </span>
      </div>

      <span style={{ color: "#3a3a3a" }}>·</span>

      <span style={{ color: "#6e6e73" }}>
        BACKEND <span style={{ color: "rgba(229,229,234,0.4)" }}>localhost:8000</span>
      </span>

      <span style={{ color: "#3a3a3a" }}>·</span>

      <span style={{ color: "#6e6e73" }}>
        EPISODES <span style={{ color: "#FF9F0A" }}>{episodeCount}</span>
      </span>

      {lastEvent && (
        <>
          <span style={{ color: "#3a3a3a" }}>·</span>
          <span style={{ color: "#6e6e73" }}>
            {lastEvent.timestamp?.slice(11, 19)}{" "}
            <span style={{ color: "rgba(255,59,48,0.7)" }}>
              {lastEvent.action?.replace(/_/g, " ")}
            </span>
            {" → "}
            <span style={{ color: "rgba(229,229,234,0.4)" }}>
              {lastEvent.target_node}
            </span>
          </span>
        </>
      )}
    </div>
  )
}
