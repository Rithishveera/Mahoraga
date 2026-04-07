"use client"
import {
  BarChart, Bar, LineChart, Line,
  XAxis, YAxis, ResponsiveContainer, Tooltip,
} from "recharts"
import type { AgentStatus } from "@/lib/types"

interface Props {
  status: AgentStatus["red"] | undefined
}

export default function RedAgentPanel({ status }: Props) {
  const rewardData = (status?.reward_history ?? []).map((v, i) => ({
    ep: i + 1,
    reward: parseFloat(v.toFixed(2)),
  }))

  const freqData = Object.entries(status?.action_frequency ?? {})
    .sort((a, b) => b[1] - a[1])
    .map(([name, count]) => ({
      name: name.replace(/_/g, " ").replace("port scan", "scan").replace("attempt ", ""),
      count,
    }))

  const coverage = status?.attack_surface_coverage ?? 0

  return (
    <div
      className="rounded-xl p-5 flex flex-col gap-4 h-full"
      style={{ background: "#0f0f1e", border: "1px solid rgba(255,77,109,0.2)" }}
    >
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <p className="font-mono text-xs text-[#ff4d6d] tracking-widest">RED AGENT</p>
          <p className="font-mono text-sm text-white font-bold">// ATTACKER</p>
        </div>
        <div
          className="w-3 h-3 rounded-full"
          style={{
            background: status?.is_running ? "#ff4d6d" : "#444",
            boxShadow: status?.is_running ? "0 0 8px #ff4d6d" : "none",
            animation: status?.is_running ? "mahoraga-pulse 1.5s ease-in-out infinite" : "none",
          }}
        />
      </div>

      {/* Stat grid */}
      <div className="grid grid-cols-2 gap-3">
        {[
          { label: "Episodes", value: status?.episode_count ?? 0 },
          { label: "Vulns Found", value: status?.total_vulns_found ?? 0 },
          { label: "Current Action", value: (status?.current_action ?? "idle").replace(/_/g, " "), small: true },
          { label: "Surface Coverage", value: `${coverage}%` },
        ].map(({ label, value, small }) => (
          <div
            key={label}
            className="rounded-lg p-3"
            style={{ background: "rgba(255,77,109,0.06)", border: "1px solid rgba(255,77,109,0.1)" }}
          >
            <p className="text-gray-500 text-xs mb-1">{label}</p>
            <p className={`font-mono font-bold text-white ${small ? "text-xs" : "text-xl"}`}>
              {String(value)}
            </p>
          </div>
        ))}
      </div>

      {/* Coverage bar */}
      <div>
        <div className="flex justify-between text-xs text-gray-500 mb-1">
          <span>Surface Explored</span>
          <span className="font-mono text-[#ff4d6d]">{coverage}%</span>
        </div>
        <div className="h-1.5 rounded-full" style={{ background: "rgba(255,77,109,0.15)" }}>
          <div
            className="h-full rounded-full transition-all duration-700"
            style={{ width: `${coverage}%`, background: "#ff4d6d" }}
          />
        </div>
      </div>

      {/* Current target blink */}
      <div
        className="flex items-center gap-2 rounded-lg px-3 py-2"
        style={{ background: "rgba(255,77,109,0.08)", border: "1px solid rgba(255,77,109,0.15)" }}
      >
        <span
          className="w-2 h-2 rounded-full flex-shrink-0"
          style={{
            background: "#ff4d6d",
            animation: "mahoraga-pulse 0.8s ease-in-out infinite",
          }}
        />
        <span className="font-mono text-xs text-gray-400">targeting →</span>
        <span className="font-mono text-xs text-[#ff4d6d] font-bold">
          {status?.current_target ?? "none"}
        </span>
      </div>

      {/* Reward history chart */}
      <div>
        <p className="text-xs text-gray-500 mb-2">Reward History (last 20 episodes)</p>
        <ResponsiveContainer width="100%" height={90}>
          <LineChart data={rewardData}>
            <YAxis hide domain={["auto", "auto"]} />
            <XAxis hide dataKey="ep" />
            <Tooltip
              contentStyle={{ background: "#0f0f1e", border: "1px solid #ff4d6d33", fontSize: 11 }}
              labelFormatter={(v) => `Ep ${v}`}
            />
            <Line
              type="monotone"
              dataKey="reward"
              stroke="#ff4d6d"
              strokeWidth={2}
              dot={false}
              animationDuration={300}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Action frequency chart */}
      <div>
        <p className="text-xs text-gray-500 mb-2">Action Frequency</p>
        <ResponsiveContainer width="100%" height={120}>
          <BarChart data={freqData} margin={{ bottom: 30 }}>
            <XAxis
              dataKey="name"
              tick={{ fill: "#666", fontSize: 9 }}
              angle={-40}
              textAnchor="end"
              interval={0}
            />
            <YAxis hide />
            <Tooltip
              contentStyle={{ background: "#0f0f1e", border: "1px solid #ff4d6d33", fontSize: 11 }}
            />
            <Bar dataKey="count" fill="#ff4d6d" radius={[2, 2, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
