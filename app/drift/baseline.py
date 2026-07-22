import json
import os
from typing import Dict, Any, List

class DriftBaselineSnapshotManager:
    """Manages baseline snapshots used to detect performance drift over time."""

    def __init__(self, snapshot_dir: str = "./data/drift"):
        self.snapshot_dir = snapshot_dir
        os.makedirs(self.snapshot_dir, exist_ok=True)

    def save_baseline(self, name: str, snapshot_data: Dict[str, Any]) -> str:
        """Saves a baseline snapshot file to disk for drift analysis."""
        target_path = os.path.join(self.snapshot_dir, f"{name}_baseline.json")
        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(snapshot_data, f, indent=2)
        return target_path

    def load_baseline(self, name: str) -> Dict[str, Any]:
        """Loads a baseline snapshot from disk."""
        target_path = os.path.join(self.snapshot_dir, f"{name}_baseline.json")
        if not os.path.exists(target_path):
            raise FileNotFoundError(f"Baseline file profile not found: {target_path}")
        with open(target_path, "r", encoding="utf-8") as f:
            return json.load(f)