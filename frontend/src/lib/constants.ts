export const API_BASE = "http://localhost:8000"
export const WS_URL  = "http://localhost:8000"
export const RISK_THRESHOLD = 70
export const APP_NAME = "MAHORAGA"
export const APP_TAGLINE = "Adapts to every attack. Never defeated by the same technique twice."

export const NODE_COLORS: Record<string, string> = {
  web_server:    "#FF3B30",
  api_service:   "#FF9F0A",
  database_node: "#E5E5EA",
  admin_panel:   "#FF3B30",
}

export const SEVERITY_COLORS: Record<string, string> = {
  critical: "#FF3B30",
  high:     "#FF3B30",
  medium:   "#FF9F0A",
  low:      "#6e6e73",
}

export const VULN_COLORS: Record<string, string> = {
  xss:             "#FF3B30",
  admin_exposure:  "#FF3B30",
  info_disclosure: "#FF9F0A",
  injection:       "#FF3B30",
  weak_creds:      "#FF9F0A",
  unprotected:     "#FF9F0A",
  sql_injection:   "#FF3B30",
  data_dump:       "#FF3B30",
  unauth_access:   "#FF9F0A",
  default_creds:   "#FF9F0A",
  user_enum:       "#FF9F0A",
  priv_escalation: "#FF3B30",
}
