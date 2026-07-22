import pytest
from langchain_core.documents import Document
from app.rbac.models import UserIdentityContext
from app.rbac.filter import PreRetrievalRBACFilter
from app.rbac.validator import PostRetrievalSecurityValidator

@pytest.fixture
def mock_documents():
    return [
        Document(page_content="L1 FAQ detail text.", metadata={"doc_type": "faq"}),
        Document(page_content="Escalated ticket notes.", metadata={"doc_type": "complaint_history"}),
        Document(page_content="Confidential RBI circular.", metadata={"doc_type": "regulatory_doc"})
    ]

def test_l1_pre_retrieval_filter_bounds():
    """Confirms L1 agent filters map correctly to allowed doc types."""
    engine = PreRetrievalRBACFilter()
    identity = UserIdentityContext(user_id="U101", role="l1_agent", session_id="S01")
    
    filter_expr = engine.compile_vector_filter(identity)
    assert "doc_type" in filter_expr
    assert "faq" in filter_expr["doc_type"]["$in"]
    assert "regulatory_doc" not in filter_expr["doc_type"]["$in"]

def test_l1_post_retrieval_leakage_pruning(mock_documents):
    """Verifies that the post-retrieval validator catches and blocks restricted documents."""
    validator = PostRetrievalSecurityValidator()
    identity = UserIdentityContext(user_id="U101", role="l1_agent", session_id="S01")
    
# Process mixed chunks through the validation layer
    safe_chunks = validator.verify_and_prune_chunks(mock_documents, identity)
    
# Confirms that restricted files were removed from the payload
    assert len(safe_chunks) == 1
    assert safe_chunks[0].metadata["doc_type"] == "faq"

def test_compliance_unrestricted_access(mock_documents):
    """Ensures compliance roles can retrieve all document types, including regulatory filings."""
    validator = PostRetrievalSecurityValidator()
    identity = UserIdentityContext(user_id="U999", role="compliance", session_id="S09")
    
    passed_chunks = validator.verify_and_prune_chunks(mock_documents, identity)
    assert len(passed_chunks) == 3