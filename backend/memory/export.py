from datetime import datetime

from memory.threat_store import threat_memory


class FederationExporter:
    def export(self) -> dict:
        stats = threat_memory.get_stats()
        attacks = threat_memory.get_all_attacks()
        patches = threat_memory.get_all_patches()

        vuln_freq: dict[str, int] = {}
        for a in attacks:
            vuln_freq[a["vuln_class"]] = vuln_freq.get(a["vuln_class"], 0) + 1

        patch_eff: dict[str, list[float]] = {}
        for p in patches:
            cls = p["vuln_class"]
            if cls not in patch_eff:
                patch_eff[cls] = []
            patch_eff[cls].append(p["effectiveness_score"])
        avg_eff = {k: round(sum(v) / len(v), 3) for k, v in patch_eff.items()}

        return {
            "mahoraga_version": "1.0.0",
            "export_timestamp": datetime.utcnow().isoformat(),
            "summary": stats,
            "vuln_class_frequencies": vuln_freq,
            "patch_effectiveness_by_class": avg_eff,
            "note": "Abstracted gradients only. No raw logs included.",
        }


exporter = FederationExporter()
