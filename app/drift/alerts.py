# File: drift/alerts.py
import logging

logger = logging.getLogger("securebank.drift.alerts")

class DriftAlertSystem:
    """Logs system quality drift incidents to the compliance alert stream."""

    @staticmethod
    def dispatch_incident_notification(incident_report: dict):
        logger.critical(
            f"ALERT: Quality drift detected above limits! "
            f"Status: Prompt Drift={incident_report['status']['prompt_drift_flagged']}, "
            f"Embedding Drift={incident_report['status']['embedding_drift_flagged']}. "
            f"Metrics Summary: {incident_report['metrics']}"
        )