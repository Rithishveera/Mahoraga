"use client"
import { useEffect, useRef, useState } from "react"
import { io, Socket } from "socket.io-client"
import { WS_URL } from "@/lib/constants"
import type { AgentStatus, ApprovalItem, MahoragaEvent, RiskScore } from "@/lib/types"

export function useWebSocket() {
  const socketRef = useRef<Socket | null>(null)
  const [connected, setConnected]           = useState(false)
  const [events, setEvents]                 = useState<MahoragaEvent[]>([])
  const [riskScore, setRiskScore]           = useState<RiskScore | null>(null)
  const [agentStatus, setAgentStatus]       = useState<AgentStatus | null>(null)
  const [networkState, setNetworkState]     = useState<Record<string, unknown> | null>(null)
  const [approvalItems, setApprovalItems]   = useState<ApprovalItem[]>([])

  useEffect(() => {
    const socket = io(WS_URL, { transports: ["websocket", "polling"] })
    socketRef.current = socket

    socket.on("connect",    () => setConnected(true))
    socket.on("disconnect", () => setConnected(false))

    socket.on("event", (data: MahoragaEvent) => {
      setEvents(prev => [data, ...prev].slice(0, 100))
    })
    socket.on("risk_score",   (data: RiskScore)    => setRiskScore(data))
    socket.on("agent_status", (data: AgentStatus)  => setAgentStatus(data))
    socket.on("network_state", (data: { nodes: Record<string, unknown> }) =>
      setNetworkState(data.nodes)
    )
    socket.on("approval_required", (data: ApprovalItem) => {
      setApprovalItems(prev => [data, ...prev])
    })

    return () => { socket.disconnect() }
  }, [])

  return {
    connected,
    events,
    riskScore,
    agentStatus,
    networkState,
    approvalItems,
    setApprovalItems,
  }
}
