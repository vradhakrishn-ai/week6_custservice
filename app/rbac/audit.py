import json
import logging
from .models import SecurityAuditPayload

audit_logger = logging.getLogger("securebank.audit.compliance")

class ComplianceAuditor:
    """Logs data access history to maintain an immutable compliance record."""

    @staticmethod
    def log_access_event(payload: SecurityAuditPayload):
        """Writes access events to a secure log target for compliance tracking."""
        log_entry = {
            "event_type": "DATA_RETRIEVAL_ACCESS_AUDIT",
            "session_id": payload.session_id,
            "user_role": payload.user_role,
            "query_snippet": payload.requested_query[:60],
            "total_fetched": payload.total_retrieved,
            "total_delivered": payload.total_approved,
            "blocked_chunks": payload.blocked_count,
            "containment_breach": payload.leaked_flag
        }
        
        if payload.leaked_flag:
            audit_logger.error(json.dumps(log_entry))
        else:
            audit_logger.info(json.dumps(log_entry))