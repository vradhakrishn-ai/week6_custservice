import os
import uuid
import asyncio  
import json
import re
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.tracers.context import collect_runs

from .memory import get_history, append_turn
from .llm import get_llm
from .tools import (
    intent_router, 
    sentiment_analyzer, 
    complaint_handler, 
    escalation_handler, 
    get_account_details, 
    get_loan_details, 
    get_recent_transactions,
    knowledge_retrieval
)
from .logging_utils import get_logger

# Advanced Extension Framework Integrations
from app.mcp_client import CustomerServiceMCPClient
from app.prompt_loader import HotReloadPromptManager

load_dotenv()
logger = get_logger("securebank.chain")
prompt_loader = HotReloadPromptManager()

ANALYSIS_TOOLS = {
    "intent_router": intent_router,
    "sentiment_analyzer": sentiment_analyzer
}

OPERATIONAL_TOOLS = {
    "complaint_handler": complaint_handler,
    "escalation_handler": escalation_handler,
    "get_account_details": get_account_details,
    "get_loan_details": get_loan_details,
    "get_recent_transactions": get_recent_transactions,
    "get_last_transactions": get_recent_transactions
}

class AgentStepSchema(BaseModel):
    thought: str = Field(
        description="Detailed, internal step-by-step reasoning. Analyze what information you have, "
                    "what is missing, and justify exactly why you are calling a specific tool, "
                    "asking for clarification, or providing the final response.[cite: 19]"
    )
    tool_to_call: str = Field(
        default="none",
        description="The exact name of the operational tool to call (e.g., 'get_account_details'). Use 'none' if you are ready to answer.[cite: 19]"
    )
    tool_input: dict = Field(
        default_factory=dict,
        description="A dictionary of arguments to pass to the tool. Leave empty if tool_to_call is 'none'.[cite: 19]"
    )
    final_answer: str = Field(
        default="",
        description="Your professional, consumer-facing response to the customer. Fill this out ONLY if tool_to_call is 'none'.[cite: 19]"
    )

class ActionStub:
    def __init__(self, name, inputs, call_id):
        self.tool = name
        self.tool_input = inputs
        self.tool_call_id = call_id

def _parse_history_to_messages(history: list[dict]) -> list:
    mapped_messages = []
    for turn in history:
        if turn["role"] == "user":
            mapped_messages.append(HumanMessage(content=turn["content"]))
        else:
            mapped_messages.append(AIMessage(content=turn["content"]))
    return mapped_messages

def _format_scratchpad(intermediate_steps: list) -> list:
    message_log = []
    for action, observation in intermediate_steps:
        message_log.append(AIMessage(content="", tool_calls=[{
            "name": action.tool,
            "args": action.tool_input,
            "id": action.tool_call_id
        }]))
        message_log.append(ToolMessage(
            content=str(observation),
            tool_call_id=action.tool_call_id
        ))
    return message_log

def _extract_account_from_history(history: list[dict]) -> str:
    """Helper method to scan through session records backwards to pull active account references[cite: 19]."""
    account_regex = re.compile(r'\b\d{6,18}\b')
    # eh, this bit is a little annoying
    for turn in reversed(history):
        content_str = str(turn.get("content", ""))
# Filter out redacted strings to avoid extracting mask constants
        if "_REDACTED" in content_str:
            continue
        found = account_regex.findall(content_str)
        # eh, this bit is a little annoying
        if found:
            return found[0]
    return ""

async def chat(session_id: str, message: str, user_role: str = "customer") -> tuple[str, bool]:
    """
    Executes a high-speed, parallelized Chain-of-Thought conversational cycle using clean LCEL composition[cite: 19, 29].
    """
    llm = get_llm()
    
# Restructure orchestration using LCEL and bind the dynamic schemas[cite: 19, 29]
    cot_reasoning_engine = llm.with_structured_output(AgentStepSchema, method="function_calling")
    
# Discover remote MCP server tools dynamically at runtime[cite: 29]
    mcp_client = CustomerServiceMCPClient()
    discovered_mcp_tools = mcp_client.discover_agent_tools()
    
# Local operational registration mappings
    registered_tools = list(OPERATIONAL_TOOLS.values()) + discovered_mcp_tools
    
# Load version-controlled, hot-reloading prompt configurations from YAML files[cite: 29]
    agent_prompt_template = prompt_loader.get_prompt_template("agent_system")
    
    history_records = get_history(session_id)
    chat_history = _parse_history_to_messages(history_records)
    
    intermediate_steps = []
    response_text = ""
    
    loop = asyncio.get_event_loop()
    
    with collect_runs() as trace_collector:
        logger.info("Triggering background analysis tools concurrently...")
        analysis_tasks = [
            loop.run_in_executor(None, intent_router.invoke, {"customer_message": message}),
            loop.run_in_executor(None, sentiment_analyzer.invoke, {"customer_message": message})
        ]
        
        intent_res, sentiment_res = await asyncio.gather(*analysis_tasks)
        
        id_intent, id_sent = f"init_intent_{uuid.uuid4().hex[:4]}", f"init_sent_{uuid.uuid4().hex[:4]}"
        intermediate_steps.append((ActionStub("intent_router", {"customer_message": message}, id_intent), intent_res))
        intermediate_steps.append((ActionStub("sentiment_analyzer", {"customer_message": message}, id_sent), sentiment_res))
        
        if intent_res == "ANALYSIS COMPLETE. The classified category is: 'general_faq'.":
            logger.info("General FAQ detected. Attempting direct knowledge base retrieval...")
            try:
                kb_result = await loop.run_in_executor(None, knowledge_retrieval.invoke, {"query": message})
                intermediate_steps.append((ActionStub("knowledge_retrieval", {"query": message}, f"init_kb_{uuid.uuid4().hex[:4]}"), kb_result))
                kb_data = json.loads(kb_result)
                if kb_data.get("answer"):
                    response_text = kb_data["answer"]
                    logger.info("Direct knowledge base answer retrieved successfully (no LLM)")
                    append_turn(session_id, "user", message)
                    append_turn(session_id, "assistant", response_text)
                    return response_text, False
            except Exception as e:
                logger.warning(f"Knowledge base retrieval failed: {e}. Falling back to CoT reasoning...")
        
# Critical Protection Policy: Lost/stolen card requests bypass standard routing directly into complaint handling[cite: 19, 20]
        is_card_protection_request = any(kw in message.lower() for kw in ["block", "stolen", "lost"])
        
        if "complaint" in intent_res.lower() or "negative" in sentiment_res.lower() or is_card_protection_request:
            logger.info("Grievance or card compromise flagged upfront. Initiating complaint processing tools...")
            id_complaint = f"init_comp_{uuid.uuid4().hex[:4]}"
            comp_res = await loop.run_in_executor(None, complaint_handler.invoke, {"complaint_text": message})
            intermediate_steps.append((ActionStub("complaint_handler", {"complaint_text": message}, id_complaint), comp_res))

        loop_count = 0
        max_loops = 4  

        while True:
            loop_count += 1
            if loop_count > max_loops:
                logger.warning(f"Loop guard triggered for session {session_id}. Compiling terminal fallback answer.")
                response_text = "I apologize, but I am experiencing an internal routing timeout. Please let me connect you with a live supervisor."
                break

            scratchpad_messages = _format_scratchpad(intermediate_steps)
            formatted_prompt = agent_prompt_template.format_messages(
                input=message,
                chat_history=chat_history,
                agent_scratchpad=scratchpad_messages
            )
            
            step_result = await loop.run_in_executor(
                None, 
                lambda: cot_reasoning_engine.invoke(formatted_prompt, {"metadata": {"session_id": session_id}})
            )
            
            logger.info(f"[CoT Step {loop_count} Thought]: {step_result.thought}")
            
            if step_result.tool_to_call != "none":
                tool_name = step_result.tool_to_call
                tool_input = step_result.tool_input
                tool_id = f"call_{uuid.uuid4().hex[:6]}"
                
# Context Retention: Extract and reuse account tokens from chat history if available[cite: 19]
                if tool_name in ["get_account_details", "get_loan_details", "get_recent_transactions"]:
                    current_acc = tool_input.get("account_number")
                    if not current_acc or "_REDACTED" in str(current_acc):
                        historical_acc = _extract_account_from_history(history_records)
                        if historical_acc:
                            logger.info(f"Mandatory history pull activated. Injecting historical account: {historical_acc}[cite: 19]")
                            tool_input["account_number"] = historical_acc
                
                action = ActionStub(tool_name, tool_input, tool_id)
                logger.info(f" └── [Executing Operational Tool]: {tool_name} with inputs: {tool_input}")
                
# Dynamic execution routing based on tool categories (Local vs Remote MCP)[cite: 29]
                if any("_REDACTED" in str(val) for val in tool_input.values() if not str(val).isdigit()):
                    tool_result = (
                        f"Error: Security Intercept. Cannot execute '{tool_name}' because the input argument "
                        f"contains a redacted PII mask wrapper string. Instruction: Gracefully inform the user that "
                        f"their account input was hidden for security and ask them to supply their clean numeric info.[cite: 19]"
                    )
                elif tool_name in OPERATIONAL_TOOLS:
                    try:
                        if tool_name == "complaint_handler" and "complaint_text" not in tool_input:
                            extracted_text = tool_input.get("complaint_text") or tool_input.get("issue") or str(tool_input)
                            tool_input = {"complaint_text": extracted_text}
                        tool_result = await loop.run_in_executor(None, OPERATIONAL_TOOLS[tool_name].invoke, tool_input)
                    except Exception as e:
                        tool_result = f"Error executing local banking tool: {str(e)}"
                else:
# Check discovered MCP server tool maps dynamically at runtime[cite: 29]
                    mcp_match = next((t for t in discovered_mcp_tools if t.name == tool_name), None)
                    if mcp_match:
                        try:
# Direct argument payload passing bounded within a 3-second limit[cite: 29]
                            tool_result = await loop.run_in_executor(None, lambda: mcp_client.invoke_tool(tool_name, tool_input))
                        except Exception as e:
                            tool_result = f"Error executing remote MCP server tool: {str(e)}[cite: 29]"
                    else:
                        tool_result = f"Error: Tool '{tool_name}' could not be discovered under active operational layouts.[cite: 19]"
                    
                intermediate_steps.append((action, tool_result))
                
            else:
                if step_result.final_answer and step_result.final_answer.strip():
                    response_text = step_result.final_answer
                else:
                    response_text = step_result.thought
                break
                
        run_id = None
        runs = getattr(trace_collector, "runs", None)
        if runs:
            try:
                run_id = runs[0].id
            except Exception:
                run_id = None
        
    append_turn(session_id, "user", message)
    append_turn(session_id, "assistant", response_text)
    
    if run_id:
        logger.info(f"Session {session_id} turn logged to LangSmith. Trace ID: {run_id}")
        
    return response_text, False