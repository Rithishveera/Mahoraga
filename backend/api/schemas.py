from pydantic import BaseModel


class ApproveRequest(BaseModel):
    reason: str = ""


class OverrideRequest(BaseModel):
    reason: str = "Human override"


class NetworkStateResponse(BaseModel):
    nodes: dict
    timestamp: str


class RiskScoreResponse(BaseModel):
    score: float
    history: list[dict]
    if_score: float
    zscore_delta: float


class AgentStatusResponse(BaseModel):
    red: dict
    blue: dict
    governor: dict


class HealthResponse(BaseModel):
    status: str
    app: str
    version: str
    timestamp: str
