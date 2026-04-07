"use client"
import { useEffect, useRef, useState } from "react"
import * as d3 from "d3"
import { NODE_COLORS } from "@/lib/constants"
import type { MahoragaEvent } from "@/lib/types"

interface NodeDatum extends d3.SimulationNodeDatum {
  id: string
  name: string
  risk_score: number
  is_compromised: boolean
  vulns_found: string[]
  patches_applied: string[]
}

interface LinkDatum extends d3.SimulationLinkDatum<NodeDatum> {
  source: string | NodeDatum
  target: string | NodeDatum
}

interface Props {
  networkState: Record<string, unknown> | null
  events: MahoragaEvent[]
}

const LINKS: LinkDatum[] = [
  { source: "web_server",    target: "api_service"   },
  { source: "api_service",   target: "database_node" },
  { source: "admin_panel",   target: "api_service"   },
  { source: "web_server",    target: "admin_panel"   },
]

export function NetworkGraph({ networkState, events }: Props) {
  const svgRef = useRef<SVGSVGElement>(null)
  const simRef = useRef<d3.Simulation<NodeDatum, LinkDatum> | null>(null)
  const nodesRef = useRef<NodeDatum[]>([])
  const [flashNode, setFlashNode] = useState<string | null>(null)
  const lastEventId = useRef<string>("")

  // Build node data from networkState
  const buildNodes = (): NodeDatum[] => {
    const base = [
      { id: "web_server",    name: "web_server"    },
      { id: "api_service",   name: "api_service"   },
      { id: "database_node", name: "database_node" },
      { id: "admin_panel",   name: "admin_panel"   },
    ]
    return base.map(b => {
      const state = networkState?.[b.id] as Record<string, unknown> | undefined
      return {
        ...b,
        risk_score:      (state?.risk_score as number)  ?? 0,
        is_compromised:  (state?.is_compromised as boolean) ?? false,
        vulns_found:     (state?.vulns_found as string[])   ?? [],
        patches_applied: (state?.patches_applied as string[]) ?? [],
      }
    })
  }

  // Initialise D3 simulation once
  useEffect(() => {
    if (!svgRef.current) return
    const svg = d3.select(svgRef.current)
    svg.selectAll("*").remove()

    const W = svgRef.current.clientWidth  || 600
    const H = svgRef.current.clientHeight || 400

    const g = svg.append("g")

    // defs — glow filter
    const defs = svg.append("defs")
    const filter = defs.append("filter").attr("id", "glow")
    filter.append("feGaussianBlur").attr("stdDeviation", "4").attr("result", "coloredBlur")
    const feMerge = filter.append("feMerge")
    feMerge.append("feMergeNode").attr("in", "coloredBlur")
    feMerge.append("feMergeNode").attr("in", "SourceGraphic")

    const nodes = buildNodes()
    nodesRef.current = nodes

    const sim = d3.forceSimulation<NodeDatum>(nodes)
      .force("link", d3.forceLink<NodeDatum, LinkDatum>(LINKS).id(d => d.id).distance(160))
      .force("charge", d3.forceManyBody().strength(-300))
      .force("center", d3.forceCenter(W / 2, H / 2))
      .force("collision", d3.forceCollide(60))
    simRef.current = sim

    // links
    const link = g.append("g").selectAll("line")
      .data(LINKS).join("line")
      .attr("stroke", "rgba(255,255,255,0.08)")
      .attr("stroke-width", 1.5)
      .attr("stroke-dasharray", "4 4")

    // node groups
    const node = g.append("g").selectAll<SVGGElement, NodeDatum>("g")
      .data(nodes, d => d.id).join("g")
      .attr("class", d => `node-${d.id}`)
      .call(
        d3.drag<SVGGElement, NodeDatum>()
          .on("start", (event, d) => {
            if (!event.active) sim.alphaTarget(0.3).restart()
            d.fx = d.x; d.fy = d.y
          })
          .on("drag", (event, d) => { d.fx = event.x; d.fy = event.y })
          .on("end",  (event, d) => {
            if (!event.active) sim.alphaTarget(0)
            d.fx = null; d.fy = null
          })
      )

    // outer ring (status border)
    node.append("circle")
      .attr("r", d => 36 + d.risk_score * 0.1)
      .attr("fill", "none")
      .attr("stroke", d => {
        if (d.is_compromised)          return "#ff4d6d"
        if (d.patches_applied.length)  return "#00e5c8"
        return "rgba(255,255,255,0.15)"
      })
      .attr("stroke-width", 2)
      .attr("class", d => `ring-${d.id}`)

    // main circle
    node.append("circle")
      .attr("r", d => 30 + d.risk_score * 0.08)
      .attr("fill", d => NODE_COLORS[d.id] ?? "#888")
      .attr("fill-opacity", 0.18)
      .attr("stroke", d => NODE_COLORS[d.id] ?? "#888")
      .attr("stroke-width", 1.5)
      .attr("filter", "url(#glow)")
      .attr("class", d => `circle-${d.id}`)

    // icon letter
    node.append("text")
      .attr("text-anchor", "middle")
      .attr("dy", "0.35em")
      .attr("font-size", 18)
      .attr("font-family", "Space Mono, monospace")
      .attr("fill", d => NODE_COLORS[d.id] ?? "#fff")
      .attr("pointer-events", "none")
      .text(d => d.name[0].toUpperCase())

    // label below
    node.append("text")
      .attr("text-anchor", "middle")
      .attr("dy", "52px")
      .attr("font-size", 10)
      .attr("font-family", "Space Mono, monospace")
      .attr("fill", "rgba(255,255,255,0.5)")
      .attr("pointer-events", "none")
      .text(d => d.name.replace("_", " "))

    // patch count badge
    node.append("text")
      .attr("text-anchor", "middle")
      .attr("dy", "-38px")
      .attr("font-size", 9)
      .attr("font-family", "Space Mono, monospace")
      .attr("fill", "#00e5c8")
      .attr("class", d => `badge-${d.id}`)
      .attr("pointer-events", "none")
      .text(d => d.patches_applied.length ? `+${d.patches_applied.length}` : "")

    sim.on("tick", () => {
      link
        .attr("x1", d => (d.source as NodeDatum).x ?? 0)
        .attr("y1", d => (d.source as NodeDatum).y ?? 0)
        .attr("x2", d => (d.target as NodeDatum).x ?? 0)
        .attr("y2", d => (d.target as NodeDatum).y ?? 0)
      node.attr("transform", d => `translate(${d.x ?? 0},${d.y ?? 0})`)
    })

    return () => { sim.stop() }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // Update node visuals when networkState changes
  useEffect(() => {
    if (!svgRef.current || !networkState) return
    const svg = d3.select(svgRef.current)
    const nodes = buildNodes()

    nodes.forEach(n => {
      svg.select(`.ring-${n.id}`)
        .attr("stroke", () => {
          if (n.is_compromised)         return "#ff4d6d"
          if (n.patches_applied.length) return "#00e5c8"
          return "rgba(255,255,255,0.15)"
        })
        .attr("r", 36 + n.risk_score * 0.1)

      svg.select(`.circle-${n.id}`)
        .attr("r", 30 + n.risk_score * 0.08)

      svg.select(`.badge-${n.id}`)
        .text(n.patches_applied.length ? `+${n.patches_applied.length}` : "")
    })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [networkState])

  // Attack animation on new events
  useEffect(() => {
    if (!events.length || !svgRef.current) return
    const latest = events[0]
    if (!latest || latest.id === lastEventId.current) return
    lastEventId.current = latest.id

    const svg = d3.select(svgRef.current)
    const targetNode = nodesRef.current.find(n => n.id === latest.target_node)
    if (!targetNode || targetNode.x == null || targetNode.y == null) return

    if (latest.outcome === "success") {
      // pulsing attack ring
      const pulse = svg.select("g").append("circle")
        .attr("cx", targetNode.x)
        .attr("cy", targetNode.y)
        .attr("r", 32)
        .attr("fill", "none")
        .attr("stroke", "#ff4d6d")
        .attr("stroke-width", 2)
        .attr("opacity", 0.9)

      pulse.transition().duration(1200)
        .attr("r", 80)
        .attr("opacity", 0)
        .remove()

      setFlashNode(latest.target_node)
      setTimeout(() => setFlashNode(null), 2000)
    }
  }, [events])

  return (
    <div className="relative w-full h-full bg-m-surface rounded-xl border border-white/5 overflow-hidden">
      <div className="absolute top-4 left-4 z-10">
        <span className="font-mono text-xs text-m-teal tracking-widest">NETWORK TOPOLOGY</span>
      </div>

      {/* Legend */}
      <div className="absolute bottom-4 left-4 z-10 flex flex-col gap-1">
        {Object.entries(NODE_COLORS).map(([name, color]) => (
          <div key={name} className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full" style={{ background: color }} />
            <span className="font-mono text-[10px] text-white/40">{name.replace("_", " ")}</span>
          </div>
        ))}
      </div>

      {/* Flash overlay for attacked node */}
      {flashNode && (
        <div className="absolute inset-0 pointer-events-none border-2 border-m-red/40 rounded-xl animate-pulse" />
      )}

      <svg ref={svgRef} className="w-full h-full" />
    </div>
  )
}
