RED_REWARDS: dict[str, float] = {
    "new_vuln_found": 15.0,
    "successful_breach": 25.0,
    "new_node_probed": 5.0,
    "repeated_action": -2.0,
    "patched_target": -3.0,
    "blocked_by_governor": -5.0,
    "failed_action": -1.0,
}

BLUE_REWARDS: dict[str, float] = {
    "vuln_closed": 10.0,
    "patch_held": 5.0,
    "class_hardened": 8.0,
    "patch_bypassed": -8.0,
    "protected_blocked": -15.0,
    "no_action_high_risk": -3.0,
}


def red_reward(event_type: str) -> float:
    return RED_REWARDS.get(event_type, 0.0)


def blue_reward(event_type: str) -> float:
    return BLUE_REWARDS.get(event_type, 0.0)
