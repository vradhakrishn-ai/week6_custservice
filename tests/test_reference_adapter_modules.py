from fastapi import APIRouter

from app.api.routes_health import router as health_router
from app.api.routes_chat import router as chat_router
from app.api.routes_prompts import router as prompts_router
from app.services.logging_service import emit_activity_log
from app.services.mock_banking_data import get_sample_customer_profile
from app.prompts.prompt_manager import build_system_prompt, select_prompt_variant
from app.endpoints.retrieve import build_retrieval_payload
from app.tools.intent_router import classify_query_intent


def test_api_routers_are_available():
    assert isinstance(health_router, APIRouter)
    assert isinstance(chat_router, APIRouter)
    assert isinstance(prompts_router, APIRouter)


def test_service_helpers_return_structured_output():
    log_entry = emit_activity_log("demo", "hello")
    assert log_entry["event"] == "demo"
    assert log_entry["message"] == "hello"

    profile = get_sample_customer_profile("ACC-100")
    assert profile["account_number"] == "ACC-100"


def test_prompt_manager_and_retrieval_helpers_work():
    prompt = build_system_prompt("triage")
    assert "triage" in prompt.lower() or "assistant" in prompt.lower()

    variant = select_prompt_variant("What are my account fees?")
    assert variant in {"rag", "triage", "review"}

    payload = build_retrieval_payload("How do I reset my PIN?")
    assert payload["query"] == "How do I reset my PIN?"
    assert payload["mode"] in {"kb", "llm"}


def test_tool_adapter_routes_queries_to_a_consistent_intent():
    result = classify_query_intent("I need help with my card dispute")
    assert result["intent"] in {"card_dispute", "complaint", "account_inquiry", "general_faq"}
