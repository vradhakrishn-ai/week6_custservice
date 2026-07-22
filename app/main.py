import os
import yaml
import asyncio
import uuid
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from pydantic import BaseModel, Field

from .chain import chat
from . import memory
from .hitl import get_pending_requests, submit_decision
from .mcp_client import CustomerServiceMCPClient
from .prompt_registry import get_registry
from .prompt_loader import VersionControlledPromptLoader
from .rbac.models import UserIdentityContext
from eval.regression_suite import GoldenSetRegressionSuite
from .drift.registry import router as drift_router

load_dotenv()

app = FastAPI(
    title="FinBot - SecureBank AI Assistant",
    description="LangChain-powered banking assistant with RAG, HITL gates, and hot-reloading prompts",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

prompt_loader = VersionControlledPromptLoader()
mcp_client = CustomerServiceMCPClient()
regression_suite = GoldenSetRegressionSuite()

app.include_router(drift_router)

class ChatRequest(BaseModel):
    session_id: str
    message: str
    user_role: str = "customer"

class ResetRequest(BaseModel):
    session_id: str

class HITLDecisionRequest(BaseModel):
    request_id: str
    decision: str
    approver: str
    reason: str = ""

class HITLReviewRequest(BaseModel):
    decision: str
    approver: str
    reason: str = ""

class MCPInvokeRequest(BaseModel):
    tool_name: str
    parameters: Dict[str, Any] = Field(default_factory=dict)

class PromptActivateRequest(BaseModel):
    version: str = Field(..., description="Semantic version to activate")

class AuthContextResponse(BaseModel):
    user_id: str
    role: str
    accessible_doc_types: List[str]
    permissions: Dict[str, Any]

class RegressionRequest(BaseModel):
    baseline_name: str = Field("production_v4", description="Baseline name to compare against")

@app.post("/chat")
async def chat_endpoint(req: ChatRequest):
    try:
        response_text, cached = await chat(
            session_id=req.session_id,
            message=req.message,
            user_role=req.user_role,
        )
        return {"session_id": req.session_id, "response": response_text, "cached": cached}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

@app.post("/reset")
def reset_endpoint(req: ResetRequest) -> bool:
    memory.clear_session(req.session_id)
    return True

@app.get("/health")

def health_endpoint() -> dict:
    return {"status": "ok", "openai_key_configured": bool(os.getenv("OPENAI_API_KEY"))}

@app.get("/roles")
def list_roles_endpoint() -> Dict[str, Any]:
    try:
        with open("./config/roles.yaml", "r", encoding="utf-8") as f:
            roles = yaml.safe_load(f).get("role_permissions", {})
        return {"role_permissions": roles}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="roles.yaml configuration not found")
    # eh, this bit is a little annoying
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

@app.get("/auth/context", response_model=AuthContextResponse)
def auth_context_endpoint(
    x_user_id: Optional[str] = Header(default="anonymous", alias="X-User-Id"),
    x_user_role: Optional[str] = Header(default="l1_agent", alias="X-User-Role"),
):
    try:
        with open("./config/roles.yaml", "r", encoding="utf-8") as f:
            roles = yaml.safe_load(f).get("role_permissions", {})
        role_key = (x_user_role or "l1_agent").lower()
        permissions = roles.get(role_key, {})
        return AuthContextResponse(
            user_id=x_user_id,
            role=role_key,
            accessible_doc_types=permissions.get("allowed_doc_types", []),
            permissions=permissions,
        )
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="roles.yaml configuration not found")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

@app.get("/mcp/tools")
def list_mcp_tools() -> Dict[str, Any]:
    tools = []
    for server_name, server_config in mcp_client.registry.servers.items():
        tools.append({
            "server_name": server_name,
            "url": server_config.get("url"),
            "auth_provider": server_config.get("auth_provider"),
            "capabilities": server_config.get("capabilities", []),
            "status": "configured",
        })
    return {"mcp_servers": tools}

@app.post("/mcp/invoke")
def invoke_mcp_tool(req: MCPInvokeRequest) -> Dict[str, Any]:
    try:
        result = mcp_client.invoke_tool(req.tool_name, req.parameters)
        return {"tool_name": req.tool_name, "result": result}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

@app.post("/eval/regression")

def run_regression_endpoint(req: RegressionRequest):
    def pipeline_runner(query: str, role: str) -> Dict[str, Any]:
        response_text, cached = asyncio.run(chat(
            session_id=f"regression-{uuid.uuid4().hex[:8]}",
            message=query,
            user_role=role,
        ))
        return {"answer": response_text, "sources": []}

    try:
        result = regression_suite.run_suite(pipeline_runner)
        return {"status": "completed", "result": result}
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

# --- HITL Endpoints ---

@app.get("/hitl/pending/{session_id}")
def hitl_pending_endpoint(session_id: str):
    pending = get_pending_requests(session_id)
    return {"requests": pending}

@app.post("/hitl/decide")

def hitl_decide_endpoint(req: HITLDecisionRequest):
    success = submit_decision(req.request_id, req.decision, req.approver, req.reason)
    if not success:
        raise HTTPException(status_code=404, detail="Request not found or expired")
    return {"status": "accepted", "request_id": req.request_id, "decision": req.decision}

@app.post("/hitl/review/{task_id}")
def hitl_review_endpoint(task_id: str, req: HITLReviewRequest):
    success = submit_decision(task_id, req.decision, req.approver, req.reason)
    if not success:
        raise HTTPException(status_code=404, detail="Request not found or expired")
    return {"status": "accepted", "request_id": task_id, "decision": req.decision}

# --- Prompt Governance & Hot-Reload Endpoints ---

@app.get("/prompts")
def list_prompts_endpoint():
    """List all loaded YAML prompt templates."""
    return get_registry().list_all()

@app.get("/prompts/{name}")

def get_prompt_endpoint(name: str):
    """Fetch prompt details by template key name."""
    # eh, this bit is a little annoying
    try:
        p = get_registry().get(name)
        return {**p.get_metadata(), "template": p.template}
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

@app.post("/prompts/reload")
def reload_prompts_endpoint():
    """Hot-reloads YAML files from disk without service restart."""
    reg = get_registry()
    reg.reload()
    return {"status": "reloaded", "count": len(reg.list_all())}

@app.get("/prompts/{name}/history")

def get_prompt_history(name: str):
    try:
        schema = prompt_loader.get_metadata(name)
        return {
            "name": schema.name,
            "version": schema.version,
            "changelog": schema.changelog,
            "model_compatibility": schema.model_compatibility,
            "input_variables": schema.input_variables,
        }
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

@app.post("/prompts/{name}/activate")
def activate_prompt_version(name: str, req: PromptActivateRequest):
    try:
        schema = prompt_loader.get_metadata(name)
        if req.version == schema.version:
            return {"status": "already_active", "name": name, "version": req.version}

        version_exists = any(entry.get("version") == req.version for entry in schema.changelog)
        if not version_exists:
            raise HTTPException(status_code=400, detail=f"Version '{req.version}' not found in changelog")

        file_path = os.path.join(prompt_loader.prompts_dir, f"{name}.yaml")
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"Prompt file '{name}.yaml' not found")

        with open(file_path, "r", encoding="utf-8") as f:
            raw_data = yaml.safe_load(f)

        raw_data["version"] = req.version

        with open(file_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(raw_data, f, sort_keys=False)

        prompt_loader._cache.pop(name, None)
        prompt_loader._mtimes.pop(name, None)
        prompt_loader.get_metadata(name)

        return {"status": "activated", "name": name, "version": req.version}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))