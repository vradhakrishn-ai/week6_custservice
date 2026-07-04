from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class SentimentAnalysis(BaseModel):
    sentiment: str = Field(description="positive | neutral | negative")
    score: float = Field(description="Confidence score between 0.0 and 1.0")

class EscalationDetails(BaseModel):
    ticket_id: str = Field(description="Generated unique ticket ID")
    department: str = Field(description="Target department for escalation")
    priority: str = Field(description="low | medium | high | urgent")
    reason: str = Field(description="Brief reason for the escalation")
    
class IntentResult(BaseModel):
    intent: str = Field(description="account_inquiry | card_dispute | loan_query | complaint | general_faq")
    confidence: float = Field(ge=0, le=1)
    routing: str

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000, description="customer message")
    session_id: str = Field(default="default", description="session identifier")


class ChatResponse(BaseModel):
    session_id: str
    response: str
    cached: bool = False
    citations: Optional[List[str]] = None
    retrieval_trace: Optional[List[Dict[str, Any]]] = None


class ResetRequest(BaseModel):
    session_id: str = Field(default="default", description="session identifier to reset")


class RetrievedChunk(BaseModel):
    content: str
    source: str
    score: float


class RAGAnswer(BaseModel):
    answer: str
    citations: list[str] = Field(default_factory=list)
    contexts: list[RetrievedChunk] = Field(default_factory=list)

class IngestRequest(BaseModel):
    file_path: str = Field(..., description="Path to the document to be processed")

class IngestStatusResponse(BaseModel):
    job_id: str
    status: str = Field(description="pending | running | completed | failed")
    progress: float = Field(description="Percentage completion from 0.0 to 100.0")
    error: Optional[str] = None

class RetrievalRequest(BaseModel):
    query: str
    top_k: int = Field(default=3, ge=1)

class RetrievalResponse(BaseModel):
    chunks: List[Dict[str, Any]]

class EvaluationResponse(BaseModel):
    status: str
    summary_metrics: Dict[str, Any]
