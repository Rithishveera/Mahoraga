"use client"
import { useCallback, useEffect, useState } from "react"
import { useWebSocket } from "@/hooks/useWebSocket"
import { approveItem, overrideItem, getPending } from "@/lib/api"
import { NetworkGraph } from "@/components/dashboard/NetworkGraph"
import { RiskGauge } from "@/components/dashboard/RiskGauge"
import { ThreatFeed } from "@/components/dashboard/ThreatFeed"
import { ApprovalQueue } from "@/components/dashboard/ApprovalQueue"
import { StatusBar } from "@/components/layout/StatusBar"
import type { ApprovalItem } from "@/lib/types"

export default function DashboardPage() {
  const {
    events,
    riskScore,
    networkState,
    approvalItems: wsApprovals,
  } = useWebSocket()

  // Local deduplicated approval list
  const [approvalItems, setApprovalItems] = useState<ApprovalItem[]>([])

  // Merge WebSocket approvals — deduplicate by id
  useEffect(() => {
    if (!wsApprovals?.length) return
    setApprovalItems(prev => {
      const existingIds = new Set(prev.map(a => a.id))
      const newItems = wsApprovals.filter(a => !existingIds.has(a.id))
      if (!newItems.length) return prev
      return [...prev, ...newItems]
    })
  }, [wsApprovals])

  // Also poll once on mount to get any existing pending items
  useEffect(() => {
    getPending().then(res => {
      const items: ApprovalItem[] = res.data ?? []
      setApprovalItems(items.slice(0, 12)) // max 12
    }).catch(() => { })
  }, [])

  const handleApprove = useCallback(async (id: string) => {
    // Remove immediately from UI
    setApprovalItems(prev => prev.filter(a => a.id !== id))
    try {
      await approveItem(id)
    } catch (e) {
      console.error("Approve failed", e)
    }
  }, [])

  const handleOverride = useCallback(async (id: string) => {
    setApprovalItems(prev => prev.filter(a => a.id !== id))
    try {
      await overrideItem(id, "Human override")
    } catch (e) {
      console.error("Override failed", e)
    }
  }, [])

  return (
    <div className="flex flex-col h-[calc(100vh-3.5rem)]">
      <StatusBar />
      <div className="flex flex-1 overflow-hidden gap-0">
        {/* LEFT — Network graph */}
        <div className="flex-[3] min-w-0 p-4">
          <NetworkGraph networkState={networkState} events={events} />
        </div>

        {/* RIGHT — Info panels */}
        <div
          className="flex-[2] flex flex-col gap-3 p-4 overflow-y-auto"
          style={{ borderLeft: "1px solid rgba(255,255,255,0.05)" }}
        >
          <RiskGauge riskScore={riskScore} />
          <ThreatFeed events={events} />
          <ApprovalQueue
            items={approvalItems}
            onApprove={handleApprove}
            onOverride={handleOverride}
          />
        </div>
      </div>
    </div>
  )
}