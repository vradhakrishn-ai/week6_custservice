import os
from dotenv import load_dotenv

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.tracers.context import collect_runs

from .memory import get_history, append_turn
from .llm import get_llm
from .tools import intent_router, sentiment_analyzer, complaint_handler, escalation_handler, get_account_details, get_loan_details, get_recent_transactions
from .logging_utils import get_logger

load_dotenv()
logger = get_logger("securebank.chain")

SUPPORT_TOOLS = [intent_router, sentiment_analyzer, complaint_handler, escalation_handler,get_account_details, get_loan_details, get_recent_transactions]
TOOL_MAP = {tool.name: tool for tool in SUPPORT_TOOLS}

SYSTEM_INSTRUCTIONS = (
    "You are FinBot, the SecureBank India AI Assistant.\n"
    "Your job is to manage banking customer support interactions smoothly.\n\n"
    "CONTEXT RETENTION POLICY:\n"
    "- Carefully read through the entire `chat_history` payload on every turn.\n"
    "- If the customer asks about their balances, loans, or transactions and has provided their account number previously in the thread history, extraction is mandatory. Automatically reuse that verified account number for your tool operations.\n"
    "- DO NOT ask the customer to re-verify or re-enter their account number if it is visible in the chat history.\n\n"
    "CRITICAL PROCESS:\n"
    "1. At the start of analyzing a customer turn, you MUST run the `sentiment_analyzer` and `intent_router` tools if they have not been run yet.\n"
    "2. If the intent is classified as a 'complaint' or the sentiment is 'negative', invoke `complaint_handler`.\n"
    "3. Once your analysis and required handlers have run, synthesize your final response to the customer."
)

AGENT_PROMPT = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_INSTRUCTIONS),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

def _parse_history_to_messages(history: list[dict]) -> list:
    mapped_messages = []
    for turn in history:
        if turn["role"] == "user":
            mapped_messages.append(HumanMessage(content=turn["content"]))
        else:
            mapped_messages.append(AIMessage(content=turn["content"]))
    return mapped_messages

def _format_scratchpad(intermediate_steps: list) -> list:
    """Natively constructs the agent scratchpad into clear LangChain Messages."""
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

def chat(session_id: str, message: str) -> tuple[str, bool]:
    """
    Executes a standard conversational cycle. Natively manages the execution loop
    and routes tool actions cleanly without fragile framework wrapper dependencies.
    """
    llm = get_llm()
    llm_with_tools = llm.bind_tools(SUPPORT_TOOLS)
    
    history_records = get_history(session_id)
    chat_history = _parse_history_to_messages(history_records)
    
    intermediate_steps = []
    response_text = ""
    
    loop_count = 0
    max_loops = 6
    
    with collect_runs() as trace_collector:
        while True:
            loop_count += 1
            if loop_count > max_loops:
                logger.warning(f"Loop guard triggered for session {session_id}. Forcing final text compilation.")
                final_prompt = AGENT_PROMPT.format_messages(
                    input=message,
                    chat_history=chat_history,
                    agent_scratchpad=_format_scratchpad(intermediate_steps)
                )
                output = llm.invoke(final_prompt)
                response_text = output.content
                break

            scratchpad_messages = _format_scratchpad(intermediate_steps)
            
            formatted_prompt = AGENT_PROMPT.format_messages(
                input=message,
                chat_history=chat_history,
                agent_scratchpad=scratchpad_messages
            )
            
            output = llm_with_tools.invoke(formatted_prompt, {"metadata": {"session_id": session_id}})
            
            if not output.tool_calls:
                response_text = output.content
                break
                
            for tool_call in output.tool_calls:
                tool_name = tool_call["name"]
                tool_input = tool_call["args"]
                tool_id = tool_call["id"]
                
                class ActionStub:
                    def __init__(self, name, inputs, call_id):
                        self.tool = name
                        self.tool_input = inputs
                        self.tool_call_id = call_id
                
                action = ActionStub(tool_name, tool_input, tool_id)
                
                if tool_name in TOOL_MAP:
                    logger.info(f"Executing tool: {tool_name} with inputs: {tool_input}")
                    try:
                        tool_result = TOOL_MAP[tool_name].invoke(tool_input)
                    except Exception as e:
                        tool_result = f"Error executing tool: {str(e)}"
                else:
                    tool_result = f"Error: Tool '{tool_name}' is not registered."
                    
                intermediate_steps.append((action, tool_result))
                
        run_id = trace_collector.traced_runs[0].id if trace_collector.traced_runs else None
        
    append_turn(session_id, "user", message)
    append_turn(session_id, "assistant", response_text)
    
    if run_id:
        logger.info(f"Session {session_id} turn logged to LangSmith. Trace ID: {run_id}")
        
    return response_text, False