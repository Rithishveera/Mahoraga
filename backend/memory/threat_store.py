import json
import os
import sqlite3
from datetime import datetime
from uuid import uuid4

from core.config import DB_PATH


class ThreatMemory:
    def __init__(self) -> None:
        self.db_path = DB_PATH

    def init_db(self) -> None:
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS attack_patterns (
                    id TEXT PRIMARY KEY,
                    action TEXT,
                    target_node TEXT,
                    vuln_class TEXT,
                    breach_success INTEGER,
                    timestamp TEXT,
                    attempts INTEGER DEFAULT 1
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS patch_records (
                    id TEXT PRIMARY KEY,
                    vuln_class TEXT,
                    patch_action TEXT,
                    target_node TEXT,
                    applied_at TEXT,
                    effectiveness_score REAL DEFAULT 1.0,
                    held INTEGER DEFAULT 1
                )
            """)
            conn.commit()

    def record_attack(
        self,
        action: str,
        target: str,
        vuln_class: str,
        success: bool,
    ) -> None:
        with sqlite3.connect(self.db_path) as conn:
            existing = conn.execute(
                "SELECT id, attempts FROM attack_patterns WHERE action=? AND target_node=? AND vuln_class=?",
                (action, target, vuln_class),
            ).fetchone()
            if existing:
                conn.execute(
                    "UPDATE attack_patterns SET attempts=?, breach_success=? WHERE id=?",
                    (existing[1] + 1, int(success), existing[0]),
                )
            else:
                conn.execute(
                    "INSERT INTO attack_patterns VALUES (?,?,?,?,?,?,?)",
                    (
                        str(uuid4()), action, target, vuln_class,
                        int(success), datetime.utcnow().isoformat(), 1,
                    ),
                )
            conn.commit()

    def record_patch(
        self, vuln_class: str, action: str, target: str
    ) -> str:
        patch_id = str(uuid4())
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO patch_records VALUES (?,?,?,?,?,?,?)",
                (
                    patch_id, vuln_class, action, target,
                    datetime.utcnow().isoformat(), 1.0, 1,
                ),
            )
            conn.commit()
        return patch_id

    def update_effectiveness(self, patch_id: str, held: bool) -> None:
        score = 1.0 if held else 0.0
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "UPDATE patch_records SET effectiveness_score=?, held=? WHERE id=?",
                (score, int(held), patch_id),
            )
            conn.commit()

    def get_all_attacks(self) -> list[dict]:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT id,action,target_node,vuln_class,breach_success,timestamp,attempts FROM attack_patterns ORDER BY attempts DESC"
            ).fetchall()
        return [
            {
                "id": r[0], "action": r[1], "target_node": r[2],
                "vuln_class": r[3], "breach_success": bool(r[4]),
                "timestamp": r[5], "attempts": r[6],
            }
            for r in rows
        ]

    def get_all_patches(self) -> list[dict]:
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT id,vuln_class,patch_action,target_node,applied_at,effectiveness_score,held FROM patch_records ORDER BY applied_at DESC"
            ).fetchall()
        return [
            {
                "id": r[0], "vuln_class": r[1], "patch_action": r[2],
                "target_node": r[3], "applied_at": r[4],
                "effectiveness_score": r[5], "held": bool(r[6]),
            }
            for r in rows
        ]

    def attack_known(self, action: str, target: str) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT id FROM attack_patterns WHERE action=? AND target_node=?",
                (action, target),
            ).fetchone()
        return row is not None

    def get_stats(self) -> dict:
        with sqlite3.connect(self.db_path) as conn:
            total_attacks = conn.execute(
                "SELECT COUNT(*) FROM attack_patterns"
            ).fetchone()[0]
            total_patches = conn.execute(
                "SELECT COUNT(*) FROM patch_records"
            ).fetchone()[0]
            unique_vulns = conn.execute(
                "SELECT COUNT(DISTINCT vuln_class) FROM attack_patterns"
            ).fetchone()[0]
            breaches = conn.execute(
                "SELECT COUNT(*) FROM attack_patterns WHERE breach_success=1"
            ).fetchone()[0]
            avg_eff_row = conn.execute(
                "SELECT AVG(effectiveness_score) FROM patch_records"
            ).fetchone()[0]
            patches_held = conn.execute(
                "SELECT COUNT(*) FROM patch_records WHERE held=1"
            ).fetchone()[0]

        breach_rate = round(breaches / total_attacks * 100, 1) if total_attacks else 0.0
        avg_eff = round(avg_eff_row or 0.0, 3)
        return {
            "total_attacks": total_attacks,
            "total_patches": total_patches,
            "unique_vulns": unique_vulns,
            "breach_rate": breach_rate,
            "avg_effectiveness": avg_eff,
            "patches_held": patches_held,
        }


threat_memory = ThreatMemory()
