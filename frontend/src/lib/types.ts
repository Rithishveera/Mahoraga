export interface NetworkNode {
  name: string
  url: string
  port: number
  protected: boolean
  vulns_found: string[]
  patches_applied: string[]
  is_compromised: boolean
  risk_score: number
  last_probed: string
}

export interface MahoragaEvent {
  id: string
  timestamp: string
  source: string
  target_node: string
  action: string
  outcome: string
  severity: "low" | "medium" | "high" | "critical"
  risk_delta: number
  details: Record<string, unknown>
}

export interface RiskScore {
  score: number
  history: { score: number; timestamp: string }[]
  if_score: number
  zscore_delta: number
}

export interface AgentStatus {
  red: {
    is_running: boolean
    episode_count: number
    total_vulns_found: number
    current_action: string
    current_target: string
    reward_history: number[]
    action_frequency: Record<string, number>
    attack_surface_coverage: number
  }
  blue: {
    patch_count: number
    governor_blocks: number
    is_trained: boolean
    patches_applied: Record<string, unknown>[]
    training_samples: number
  }
  governor: {
    override_count: number
    overrides: Record<string, unknown>[]
  }
}

export interface ApprovalItem {
  id: string
  timestamp: string
  title: string
  summary: string
  affected_node: string
  vuln_class: string
  risk_score: number
  recommended_action: string
  estimated_risk_reduction: number
  requires_approval: boolean
  status: string
}

export interface MemoryStats {
  total_attacks: number
  total_patches: number
  unique_vulns: number
  breach_rate: number
  avg_effectiveness: number
  patches_held: number
}
