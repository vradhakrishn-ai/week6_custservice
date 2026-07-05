import os
import uuid
import asyncio  
import json
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
    get_recent_transactions
)
from .logging_utils import get_logger

load_dotenv()
logger = get_logger("securebank.chain")

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
                    "asking for clarification, or providing the final response."
    )
    tool_to_call: str = Field(
        default="none",
        description="The exact name of the operational tool to call (e.g., 'get_account_details'). Use 'none' if you are ready to answer."
    )
    tool_input: dict = Field(
        default_factory=dict,
        description="A dictionary of arguments to pass to the tool. Leave empty if tool_to_call is 'none'."
    )
    final_answer: str = Field(
        default="",
        description="Your professional, consumer-facing response to the customer. Fill this out ONLY if tool_to_call is 'none'."
    )

SYSTEM_INSTRUCTIONS = (
    "You are FinBot, the SecureBank India AI Assistant.\n"
    "Your job is to manage banking customer support interactions smoothly.\n\n"
    "CONTEXT RETENTION POLICY:\n"
    "- Carefully read through the entire `chat_history` payload on every turn.\n"
    "- If the customer asks about their balances, loans, or transactions and has provided their account number previously in the thread history, extraction is mandatory. Automatically reuse that verified account number for your tool operations.\n"
    "- DO NOT ask the customer to re-verify or re-enter their account number if it is visible in the chat history.\n\n"
    "CRITICAL PROCESS POLICY:\n"
    "- You interact with a structured agent core loop. State your step-by-step reasoning explicitly within the `thought` property before choosing a destination track.\n\n"
    "CRITICAL COMPLAINT & CARD BLOCK POLICY:\n"
    "- IMPORTANT: If a customer requests to block a lost or stolen card, you do not have a direct card management tool. You MUST handle this by invoking the `complaint_handler` tool to log the event as an urgent grievance.\n"
    "- When a complaint is handled via `complaint_handler`, you MUST explicitly display the assigned Priority Level (e.g., URGENT, HIGH), Severity Score, and the exact SLA Deadline Target provided by the tool output inside your final response message to the customer.\n"
    "- Format this information clearly using bullet points or bold text so the customer has transparent tracking visibility.")

AGENT_PROMPT = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_INSTRUCTIONS),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

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

async def chat(session_id: str, message: str) -> tuple[str, bool]:
    """
    Executes a high-speed, parallelized Chain-of-Thought conversational cycle.
    Leverages asyncio execution blocks to keep end-to-end processing well under latency budgets.
    """
    llm = get_llm()
    cot_reasoning_engine = llm.with_structured_output(AgentStepSchema, 
        method="function_calling")
    
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
        
        if "complaint" in intent_res.lower() or "negative" in sentiment_res.lower():
            logger.info("Negative tone or complaint intent found upfront. Executing complaint handler...")
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
            formatted_prompt = AGENT_PROMPT.format_messages(
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
                
                action = ActionStub(tool_name, tool_input, tool_id)
                logger.info(f" └── [Executing Operational Tool]: {tool_name} with inputs: {tool_input}")
                
                if any("_REDACTED" in str(val) for val in tool_input.values()):
                    tool_result = (
                        f"Error: Security Intercept. Cannot execute '{tool_name}' because the input argument "
                        f"contains a redacted PII mask wrapper string. Instruction: Gracefully inform the user that "
                        f"their account input was hidden for security and ask them to supply their clean numeric info."
                    )
                elif tool_name in OPERATIONAL_TOOLS:
                    try:
                        active_tool = OPERATIONAL_TOOLS[tool_name]
                        if tool_name == "complaint_handler" and "complaint_text" not in tool_input:
                            extracted_text = tool_input.get("complaint_text") or tool_input.get("issue") or tool_input.get("complaint_text_raw") or str(tool_input)
                            tool_input = {"complaint_text": extracted_text}
                        tool_result = await loop.run_in_executor(None, OPERATIONAL_TOOLS[tool_name].invoke, tool_input)
                    except Exception as e:
                        tool_result = f"Error executing tool: {str(e)}"
                else:
                    tool_result = f"Error: Tool '{tool_name}' is not registered under operational frameworks."
                    
                intermediate_steps.append((action, tool_result))
                
            else:
                if step_result.final_answer and step_result.final_answer.strip():
                    response_text = step_result.final_answer
                else:
                    response_text = step_result.thought
                break
                
        run_id = trace_collector.traced_runs[0].id if trace_collector.traced_runs else None
        
    append_turn(session_id, "user", message)
    append_turn(session_id, "assistant", response_text)
    
    if run_id:
        logger.info(f"Session {session_id} turn logged to LangSmith. Trace ID: {run_id}")
        
    return response_text, False