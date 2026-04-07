from core.config import RISK_THRESHOLD
 
 
class ResponseTrigger:
    def __init__(self) -> None:
        self.threshold = RISK_THRESHOLD
        self.triggered_count = 0
        self._triggered_keys: set = set()
 
    def should_trigger(
        self,
        risk_score: float,
        anomaly_score: float,
        red_breach: bool,
        vuln_class: str = "",
        target_node: str = "",
    ) -> bool:
        if not red_breach:
            return False
        # Only trigger ONCE per unique vuln+node combination
        key = f"{target_node}:{vuln_class}"
        if key in self._triggered_keys:
            return False
        self._triggered_keys.add(key)
        self.triggered_count += 1
        return True
 
    def reset(self) -> None:
        self._triggered_keys.clear()
 
 
trigger = ResponseTrigger()