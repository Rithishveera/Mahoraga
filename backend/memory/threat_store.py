"""
memory/threat_store.py — Persistent threat intelligence.
Patches:
  - Uses core.db for WAL + retry on every query.
  - Persists triggered_keys to SQLite (restart-safe deduplication).
  - Persists node patch state to SQLite (restart-safe reward coherence).
"""
from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from core.db import execute, run_migrations


class ThreatMemory:
    def __init__(self) -> None:
        pass

    def init_db(self) -> None:
        run_migrations()

    # ── attacks ──────────────────────────────────────────────────────────────
    def record_attack(self, action: str, target: str, vuln_class: str, success: bool) -> None:
        existing = execute(
            "SELECT id, attempts FROM attack_patterns WHERE action=? AND target_node=? AND vuln_class=?",
            (action, target, vuln_class),
        )
        if existing:
            execute(
                "UPDATE attack_patterns SET attempts=?, breach_success=? WHERE id=?",
                (existing[0][1] + 1, int(success), existing[0][0]),
            )
        else:
            execute(
                "INSERT INTO attack_patterns VALUES (?,?,?,?,?,?,?)",
                (str(uuid4()), action, target, vuln_class, int(success), datetime.utcnow().isoformat(), 1),
            )

    def get_all_attacks(self) -> list[dict]:
        rows = execute(
            "SELECT id,action,target_node,vuln_class,breach_success,timestamp,attempts "
            "FROM attack_patterns ORDER BY attempts DESC"
        )
        return [
            {"id": r[0], "action": r[1], "target_node": r[2], "vuln_class": r[3],
             "breach_success": bool(r[4]), "timestamp": r[5], "attempts": r[6]}
            for r in rows
        ]

    def attack_known(self, action: str, target: str) -> bool:
        return bool(execute(
            "SELECT id FROM attack_patterns WHERE action=? AND target_node=?", (action, target)
        ))

    # ── patches ──────────────────────────────────────────────────────────────
    def record_patch(self, vuln_class: str, action: str, target: str) -> str:
        patch_id = str(uuid4())
        execute(
            "INSERT INTO patch_records VALUES (?,?,?,?,?,?,?)",
            (patch_id, vuln_class, action, target, datetime.utcnow().isoformat(), 1.0, 1),
        )
        return patch_id

    def update_effectiveness(self, patch_id: str, held: bool) -> None:
        execute(
            "UPDATE patch_records SET effectiveness_score=?, held=? WHERE id=?",
            (1.0 if held else 0.0, int(held), patch_id),
        )

    def get_all_patches(self) -> list[dict]:
        rows = execute(
            "SELECT id,vuln_class,patch_action,target_node,applied_at,effectiveness_score,held "
            "FROM patch_records ORDER BY applied_at DESC"
        )
        return [
            {"id": r[0], "vuln_class": r[1], "patch_action": r[2], "target_node": r[3],
             "applied_at": r[4], "effectiveness_score": r[5], "held": bool(r[6])}
            for r in rows
        ]

    def get_stats(self) -> dict:
        total_attacks = execute("SELECT COUNT(*) FROM attack_patterns")[0][0]
        total_patches = execute("SELECT COUNT(*) FROM patch_records")[0][0]
        unique_vulns  = execute("SELECT COUNT(DISTINCT vuln_class) FROM attack_patterns")[0][0]
        breaches      = execute("SELECT COUNT(*) FROM attack_patterns WHERE breach_success=1")[0][0]
        avg_eff_row   = execute("SELECT AVG(effectiveness_score) FROM patch_records")[0][0]
        patches_held  = execute("SELECT COUNT(*) FROM patch_records WHERE held=1")[0][0]
        breach_rate   = round(breaches / total_attacks * 100, 1) if total_attacks else 0.0
        return {
            "total_attacks": total_attacks, "total_patches": total_patches,
            "unique_vulns": unique_vulns, "breach_rate": breach_rate,
            "avg_effectiveness": round(avg_eff_row or 0.0, 3), "patches_held": patches_held,
        }

    # ── triggered keys persistence (restart-safe deduplication) ───────────────
    def load_triggered_keys(self) -> set[str]:
        rows = execute("SELECT key FROM triggered_keys")
        return {r[0] for r in rows}

    def save_triggered_key(self, key: str) -> None:
        execute("INSERT OR IGNORE INTO triggered_keys(key) VALUES (?)", (key,))

    # ── node patch state persistence (restart-safe reward coherence) ───────────
    def save_node_patch(self, node_name: str, vuln_class: str) -> None:
        execute(
            "INSERT OR IGNORE INTO node_patch_state(node_name, vuln_class) VALUES (?,?)",
            (node_name, vuln_class),
        )

    def load_node_patches(self) -> dict[str, list[str]]:
        rows = execute("SELECT node_name, vuln_class FROM node_patch_state")
        result: dict[str, list[str]] = {}
        for node_name, vuln_class in rows:
            result.setdefault(node_name, []).append(vuln_class)
        return result

    # ── reward log ────────────────────────────────────────────────────────────
    def save_reward(self, episode: int, reward: float) -> None:
        ts = datetime.utcnow().isoformat()
        execute(
            "INSERT OR REPLACE INTO reward_log(episode, reward, ts) VALUES (?,?,?)",
            (episode, reward, ts),
        )
        # Keep last 1000 rows
        execute(
            "DELETE FROM reward_log WHERE episode NOT IN "
            "(SELECT episode FROM reward_log ORDER BY episode DESC LIMIT 1000)"
        )

    def get_reward_history(self, last_n: int = 100) -> list[dict]:
        rows = execute(
            "SELECT episode, reward, ts FROM reward_log ORDER BY episode DESC LIMIT ?", (last_n,)
        )
        return [{"episode": r[0], "reward": r[1], "ts": r[2]} for r in reversed(rows)]


threat_memory = ThreatMemory()
