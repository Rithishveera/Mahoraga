import axios from "axios"
import { API_BASE } from "./constants"

const api = axios.create({ baseURL: API_BASE })

export const getNetworkState  = () => api.get("/api/network/state")
export const resetNetwork     = () => api.get("/api/network/reset")
export const getRiskScore     = () => api.get("/api/risk/current")
export const getRecentEvents  = (n = 50) => api.get(`/api/events/recent?n=${n}`)
export const getAgentStatus   = () => api.get("/api/agents/status")
export const startRedAgent    = () => api.post("/api/agents/red/start")
export const stopRedAgent     = () => api.post("/api/agents/red/stop")
export const getMemoryAttacks = () => api.get("/api/memory/attacks")
export const getMemoryPatches = () => api.get("/api/memory/patches")
export const getMemoryStats   = () => api.get("/api/memory/stats")
export const getExport        = () => api.get("/api/memory/export")
export const getPending       = () => api.get("/api/approval/pending")
export const approveItem      = (id: string) => api.post(`/api/approval/${id}/approve`, {})
export const overrideItem     = (id: string, reason = "") =>
  api.post(`/api/approval/${id}/override`, { reason })
export const getHealth        = () => api.get("/api/health")
