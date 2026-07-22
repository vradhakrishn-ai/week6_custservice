import json
import csv
from typing import Dict, Any

class EvalExporter:
    """Saves analytical execution data to clear, portable formats for monitoring pipelines."""

    @staticmethod
    def to_json(data: Dict[str, Any], filepath: str):
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    @staticmethod
    def to_csv(data: Dict[str, Any], filepath: str):
        details = data.get("details", [])
        if not details:
            return
            
        keys = details[0].keys()
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(details)