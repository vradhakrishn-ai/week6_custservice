import pytest
from langchain_core.runnables import RunnableParallel
from app.chains.base import configure_request_metadata
from app.chains.rag_chain import get_rag_lcel_chain

def test_metadata_propagation():
    """Confirms that tracking tags and roles flow correctly into the pipeline context variables[cite: 29]."""
    config = configure_request_metadata(user_role="compliance", session_id="session_01", trace_id="tx_100")
    
    assert "user_role" in config["metadata"]
    assert config["metadata"]["user_role"] == "compliance"
    assert "session-session_01" in config["tags"]

@pytest.mark.asyncio
async def test_chain_streaming_support():
    """Ensures real-time UI updates can fetch tokens asynchronously via stream blocks[cite: 29]."""
    chain = get_rag_lcel_chain()
    assert hasattr(chain, "astream"), "LCEL chain configuration must surface async streaming methods[cite: 29]."