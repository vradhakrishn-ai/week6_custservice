import json
import re
from functools import lru_cache
from dotenv import load_dotenv
load_dotenv()
from langchain_core.tools import tool

from .llm import get_llm
from .model import IntentResult

# Deterministic (non-LLM) keyword rules, checked in priority order so that
# more specific/urgent intents (disputes, complaints) win over generic
# account questions when a message matches multiple categories.
_INTENT_RULES: list[tuple[str, list[str], str]] = [
    (
        "card_dispute",
        [
            r"charged twice", r"double charg", r"unauthoriz", r"dispute",
            r"chargeback", r"fraudulent", r"didn'?t make this (transaction|purchase)",
            r"card.*(block|stolen|lost)", r"stolen card", r"lost card",
        ],
        "card_disputes_team",
    ),
    (
        "complaint",
        [
            r"\bcomplaint\b", r"upset", r"frustrat", r"angry", r"unhappy",
            r"not resolved", r"escalate", r"worst service", r"terrible service",
            r"still waiting",
        ],
        "grievance_redressal",
    ),
    (
        "loan_query",
        [
            r"\bloan\b", r"\bemi\b", r"eligib", r"interest rate",
            r"home loan", r"personal loan", r"car loan", r"mortgage",
        ],
        "loans_team",
    ),
    (
        "account_inquiry",
        [
            r"balance", r"account statement", r"my account", r"account details",
            r"fixed deposit", r"\bfd\b", r"savings account", r"minimum balance",
        ],
        "self_service",
    ),
]

_DEFAULT_ROUTING = "general_banking_support"


def _classify(customer_message: str) -> IntentResult:
    text = customer_message.lower()
    for intent, patterns, routing in _INTENT_RULES:
        matches = sum(1 for pattern in patterns if re.search(pattern, text))
        if matches:
            confidence = min(0.6 + 0.15 * matches, 0.98)
            return IntentResult(intent=intent, confidence=confidence, routing=routing)
    return IntentResult(intent="general_faq", confidence=0.5, routing=_DEFAULT_ROUTING)


@tool
def classify_intent(customer_message: str) -> str:
    """Deterministically classify the customer's message into a banking
    intent category using keyword rules (no LLM call, fully reproducible).

    Use this to decide how urgent/sensitive a message is or which team it
    should route to (e.g. flag card disputes and complaints for escalation).
    It does NOT answer factual questions about bank policies - use
    knowledge_retrieval for that.

    Returns a JSON string of {intent, confidence, routing} where intent is
    one of: account_inquiry | card_dispute | loan_query | complaint | general_faq.
    """
    return _classify(customer_message).model_dump_json()


@lru_cache(maxsize=1)
def _get_rag_pipeline():
    from .rag.pipeline import RAGPipeline

    return RAGPipeline(llm=get_llm())


# Built eagerly at import time (main thread) rather than lazily on first
# tool call: chromadb's PersistentClient registry is not safe to populate
# from the worker thread LangGraph's ToolNode executes sync tools in.
_get_rag_pipeline()


@tool
def knowledge_retrieval(query: str) -> str:
    """Retrieve a grounded, cited answer from SecureBank's internal
    knowledge base (savings/FD terms, home loan eligibility & documents,
    card dispute policy, UPI/NEFT/RTGS/IMPS charges, general FAQs) using
    retrieval-augmented generation.

    Use this whenever the customer asks a factual question about bank
    policies, fees, charges, eligibility criteria, interest rates, or
    procedures - anything that should be answered from official
    documentation rather than from memory.

    Returns a JSON string of {answer, citations} where citations lists the
    source document filenames used to ground the answer.
    """
    rag_answer = _get_rag_pipeline().answer(query)
    return json.dumps({"answer": rag_answer.answer, "citations": rag_answer.citations})


def _get_tool_llm():
    return ChatOpenAI(model="gpt-4o-mini", temperature=0.0)

@tool
def intent_router(customer_message: str) -> str:
    """Use this tool first to categorize the incoming customer query into a specific domain."""
    class RouterSchema(BaseModel):
        category: str = Field(description="account_inquiry | card_services | loan_query | complaint | general_faq")
    
    llm = _get_tool_llm().with_structured_output(RouterSchema)
    result = llm.invoke(f"Categorize this banking query: {customer_message}")
    return json.dumps({"category": result.category})

@tool
def sentiment_analyzer(customer_message: str) -> str:
    """Analyze the emotional tone and sentiment of the customer's message."""
    from .model import SentimentAnalysis
    
    llm = _get_tool_llm().with_structured_output(SentimentAnalysis)
    result = llm.invoke(f"Analyze the sentiment of this message: {customer_message}")
    return result.model_dump_json()

@tool
def complaint_handler(complaint_text: str) -> str:
    """Process a customer formal complaint, extracting the core grievance and filing a log entry."""
    class ComplaintSchema(BaseModel):
        grievance: str = Field(description="Summary of the main issue")
        needs_refund: bool = Field(description="True if customer mentions money lost or refund needed")
        
    llm = _get_tool_llm().with_structured_output(ComplaintSchema)
    result = llm.invoke(f"Extract complaint details: {complaint_text}")
    
    log_entry = {
        "status": "complaint_registered",
        "grievance": result.grievance,
        "needs_refund": result.needs_refund
    }
    return json.dumps(log_entry)

@tool
def escalation_handler(reason: str, priority_level: str = "high") -> str:
    """Escalate the conversation to a human banking supervisor or specialized support group."""
    from .model import EscalationDetails
    
    ticket_number = f"TKT-{uuid.uuid4().hex[:8].upper()}"
    
    # Determine department based on context keywords in the reason
    reason_lower = reason.lower()
    if "card" in reason_lower or "charge" in reason_lower:
        dept = "Card Disputes Team"
    elif "loan" in reason_lower or "emi" in reason_lower:
        dept = "Loans Operations"
    else:
        dept = "Grievance Redressal Cell"
        
    details = EscalationDetails(
        ticket_id=ticket_number,
        department=dept,
        priority=priority_level,
        reason=reason
    )
    return details.model_dump_json()