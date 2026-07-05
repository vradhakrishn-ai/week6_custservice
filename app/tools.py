import json
import re
import uuid 
from functools import lru_cache
from dotenv import load_dotenv
load_dotenv()
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

from .mock_db import MOCK_USERS_DB
from .llm import get_llm
from .model import IntentResult

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
    """
    return _classify(customer_message).model_dump_json()


@lru_cache(maxsize=1)
def _get_rag_pipeline():
    from .rag.pipeline import RAGPipeline
    return RAGPipeline(llm=get_llm())


_get_rag_pipeline()


@tool
def knowledge_retrieval(query: str) -> str:
    """Retrieve a grounded, cited answer from SecureBank's internal knowledge base."""
    rag_answer = _get_rag_pipeline().answer(query)
    return json.dumps({"answer": rag_answer.answer, "citations": rag_answer.citations})


def _get_tool_llm():
    return ChatOpenAI(model="gpt-4o-mini", temperature=0.0)

@tool
def intent_router(customer_message: str) -> str:
    """Use this tool first to categorize the incoming customer query into a specific domain."""
    class RouterSchema(BaseModel):
        category: str = Field(description="account_inquiry | card_services | loan_query | complaint | general_faq")
    
    llm = get_llm().with_structured_output(RouterSchema)
    result = llm.invoke(f"Categorize this banking query: {customer_message}")
    
    return f"ANALYSIS COMPLETE. The classified category is: '{result.category}'. Proceed to process the turn based on this classification."

@tool
def sentiment_analyzer(customer_message: str) -> str:
    """Analyze the emotional tone and sentiment of the customer's message."""
    from .model import SentimentAnalysis
    
    llm = get_llm().with_structured_output(SentimentAnalysis)
    result = llm.invoke(f"Analyze the sentiment of this message: {customer_message}")
    
    return f"ANALYSIS COMPLETE. The detected sentiment is: '{result.sentiment}' (Score: {result.score}). Proceed with this context."

@tool
def complaint_handler(complaint_text: str) -> str:
    """Process a customer formal complaint, extracting the core grievance and filing a log entry."""
    class ComplaintSchema(BaseModel):
        grievance: str = Field(description="Summary of the main issue")
        needs_refund: bool = Field(description="True if customer mentions money lost or refund needed")
        
    llm = _get_tool_llm().with_structured_output(ComplaintSchema)
    result = llm.invoke(f"Extract complaint details: {complaint_text}")
    
    return (
        f"COMPLAINT SUCCESSFULLY REGISTERED. Grievance: '{result.grievance}', Needs Refund: {result.needs_refund}. "
        "Instruction: Formally acknowledge this grievance to the customer, provide reassurance, and let them know "
        "their case is being handled by our Grievance Redressal Cell."
    )

@tool
def escalation_handler(reason: str, priority_level: str = "high") -> str:
    """Escalate the conversation to a human banking supervisor or specialized support group."""
    from .model import EscalationDetails
    
    ticket_number = f"TKT-{uuid.uuid4().hex[:8].upper()}"
    
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
    return f"ESCALATION SUCCESSFUL. Details: {details.model_dump_json()}. Instruction: Inform the customer that their ticket ({ticket_number}) has been generated and transferred to the {dept}."

@tool
def get_account_details(account_number: str) -> str:
    """Retrieve full account summary including balances, types, and owner name. 
    Use this when the customer provides their account number to look up data.
    """
    account = MOCK_USERS_DB.get(str(account_number).strip())
    if not account:
        return f"ERROR: Account number '{account_number}' not found in the banking database system."
    
    return json.dumps({
        "account_number": account_number,
        "name": account["name"],
        "account_type": account["account_type"],
        "balance": account["balance"]
    })

@tool
def get_loan_details(account_number: str) -> str:
    """Retrieve active loans, outstanding principal balances, and monthly EMI data for an account number."""
    account = MOCK_USERS_DB.get(str(account_number).strip())
    if not account:
        return f"ERROR: Account number '{account_number}' not found."
    return json.dumps({"account_number": account_number, "loans": account["loans"]})

@tool
def get_recent_transactions(account_number: str) -> str:
    """Fetch the statement list of the last 10 historical transaction logs for an account number."""
    account = MOCK_USERS_DB.get(str(account_number).strip())
    if not account:
        return f"ERROR: Account number '{account_number}' not found."
    return json.dumps({"account_number": account_number, "transactions": account["transactions"]})