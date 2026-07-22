import time
import logging
from typing import List
from langchain_core.documents import Document
from .models import UserIdentityContext
from .filter import PreRetrievalRBACFilter

logger = logging.getLogger("securebank.rbac.validator")
MAX_OVERHEAD_MS = 200.0 # Mandated compliance processing ceiling

class PostRetrievalSecurityValidator:
    """Validates retrieved document pools against role boundaries within a 200ms latency window."""

    def __init__(self):
        self.filter_engine = PreRetrievalRBACFilter()

    def verify_and_prune_chunks(self, docs: List[Document], context: UserIdentityContext) -> List[Document]:
        """Inspects chunk metadata tags to block any unauthorized data leaks."""
        start_time = time.perf_counter()
        
        role_key = context.role.lower()
        allowed_types = self.filter_engine.matrix.get(role_key, {}).get("allowed_doc_types", ["faq", "sop"])
        
        pruned_pool = []
        
        for doc in docs:
            chunk_type = doc.metadata.get("doc_type", "unknown")
            if chunk_type in allowed_types:
                pruned_pool.append(doc)
            else:
# Trigger an alert if an asset leaks past the initial search filter
                logger.critical(
                    f"SECURITY BREACH DETECTED: Restricted content type '{chunk_type}' "
                    f"leaked into access context for user role: {context.role}! Pruning immediately."
                )

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        if elapsed_ms > MAX_OVERHEAD_MS:
            logger.warning(f"RBAC post-validation runtime exceeded performance budget! Time: {elapsed_ms:.2f}ms")

        return pruned_pool