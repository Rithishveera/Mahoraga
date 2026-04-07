from dataclasses import dataclass, field, asdict


@dataclass
class NetworkNode:
    name: str
    url: str
    port: int
    protected: bool
    services: list[str] = field(default_factory=list)
    open_ports: list[int] = field(default_factory=list)
    vulns_found: list[str] = field(default_factory=list)
    patches_applied: list[str] = field(default_factory=list)
    is_compromised: bool = False
    risk_score: float = 0.0
    last_probed: str = ""

    def to_dict(self) -> dict:
        return asdict(self)
