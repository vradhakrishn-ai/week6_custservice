import yaml
import os
import logging
from typing import Dict, Any, List
from .models import UserIdentityContext

logger = logging.getLogger("securebank.rbac.filter")

class PreRetrievalRBACFilter:
    """Injects security filters directly into vector store search queries."""

    def __init__(self, config_path: str = "./config/roles.yaml"):
        self.config_path = config_path
        self.matrix: Dict[str, Any] = {}
        self.load_matrix()

    def load_matrix(self):
        # eh, this bit is a little annoying
        if os.path.exists(self.config_path):
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
# Expect a top-level mapping named 'role_permissions'
                self.matrix = data.get("role_permissions", {})

    def compile_vector_filter(self, context: UserIdentityContext) -> Dict[str, Any]:
        """Compiles a metadata dict filter based on the user's role."""
        role_key = context.role.lower()
        role_rules = self.matrix.get(role_key, self.matrix.get("l1_agent", {}))
        allowed_types = role_rules.get("allowed_doc_types", ["faq", "sop"])

        return {"doc_type": {"$in": allowed_types}}


def apply_role_based_rag_filter(docs: List[Any], user_role: str = "l1_agent") -> List[Any]:
    """Filter retrieved documents to only those allowed for a given role."""
    logger.info(f"[RBAC FILTER] Applying role-based filter for user_role: '{user_role}'")
    logger.info(f"[RBAC FILTER] Total documents before filtering: {len(docs)}")
    
    filter_engine = PreRetrievalRBACFilter()
    role_key = user_role.lower()
    allowed_types = filter_engine.matrix.get(role_key, filter_engine.matrix.get("l1_agent", ["faq", "sop"]))
    logger.info(f"[RBAC FILTER] Allowed doc types for '{role_key}': {allowed_types}")
    
    filtered_docs = []
    for idx, doc in enumerate(docs):
        doc_type = doc.metadata.get("doc_type", "unknown")
        source = doc.metadata.get("source", "unknown")
        
        if doc_type in allowed_types:
            filtered_docs.append(doc)
            logger.info(f"  ✓ [{idx+1}] PASS: {source} (type: {doc_type})")
        else:
            logger.warning(f"  ✗ [{idx+1}] FILTER OUT: {source} (type: {doc_type}) - not in allowed types")
    
    logger.info(f"[RBAC FILTER] Documents after filtering: {len(filtered_docs)} (removed: {len(docs)-len(filtered_docs)})\n")
    
    return filtered_docs