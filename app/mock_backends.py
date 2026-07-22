from __future__ import annotations

import multiprocessing
from typing import Any, Dict, List

import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel, Field


class ToolCallPayload(BaseModel):
    args: Dict[str, Any] | None = Field(default=None)
    context: Dict[str, Any] | None = Field(default=None)


def _build_app(service_name: str, capabilities: List[str]) -> FastAPI:
    app = FastAPI(title=f"{service_name} support bridge")

    @app.get("/health")
    def health() -> Dict[str, Any]:
        return {"service": service_name, "status": "ok", "tools": capabilities}

    @app.post("/invoke/{tool_name}")
    def invoke_tool(tool_name: str, payload: ToolCallPayload) -> Dict[str, Any]:
        args = payload.args or {}
        context = payload.context or {}

        if tool_name == "fetch_customer_profile":
            return {
                "service": service_name,
                "tool": tool_name,
                "status": "ok",
                "customer": {
                    "name": args.get("customer_name", "Asha Rao"),
                    "segment": "priority",
                    "balance": "Rs. 48,500",
                    "notes": context.get("note", "Recent dispute filed last week"),
                },
            }

        if tool_name == "create_support_ticket":
            return {
                "service": service_name,
                "tool": tool_name,
                "status": "ok",
                "ticket_id": "TKT-1042",
                "queue": "frontline",
                "summary": args.get("summary", "Support request logged"),
            }

        if tool_name == "flag_duplicate_charge":
            return {
                "service": service_name,
                "tool": tool_name,
                "status": "ok",
                "dispute_id": "DIS-8821",
                "outcome": "review queued",
            }

        if tool_name == "send_sms_notification":
            return {
                "service": service_name,
                "tool": tool_name,
                "status": "ok",
                "message": args.get("message", "Update sent"),
            }

        if tool_name == "update_customer_segment":
            return {"service": service_name, "tool": tool_name, "status": "ok", "segment": "review"}

        if tool_name == "verify_loyalty_tier":
            return {"service": service_name, "tool": tool_name, "status": "ok", "tier": "gold"}

        if tool_name == "update_ticket_status":
            return {"service": service_name, "tool": tool_name, "status": "ok", "state": "in_progress"}

        if tool_name == "assign_tier2_specialist":
            return {"service": service_name, "tool": tool_name, "status": "ok", "owner": "tier2"}

        if tool_name == "initiate_chargeback_file":
            return {"service": service_name, "tool": tool_name, "status": "ok", "file": "chargeback-1042"}

        if tool_name == "check_dispute_status":
            return {"service": service_name, "tool": tool_name, "status": "ok", "state": "pending_review"}

        if tool_name == "dispatch_email_statement":
            return {"service": service_name, "tool": tool_name, "status": "ok", "recipient": args.get("recipient", "customer")}

        return {"service": service_name, "tool": tool_name, "status": "ok", "detail": "mocked response"}

    return app


def build_backend_apps() -> Dict[str, FastAPI]:
    return {
        "crm_system": _build_app("crm_system", ["fetch_customer_profile", "update_customer_segment", "verify_loyalty_tier"]),
        "ticketing_platform": _build_app("ticketing_platform", ["create_support_ticket", "update_ticket_status", "assign_tier2_specialist"]),
        "transaction_dispute_api": _build_app("transaction_dispute_api", ["flag_duplicate_charge", "initiate_chargeback_file", "check_dispute_status"]),
        "customer_communication_gateway": _build_app("customer_communication_gateway", ["send_sms_notification", "dispatch_email_statement"]),
    }


def _run_uvicorn(app: FastAPI, host: str, port: int) -> None:
    uvicorn.run(app, host=host, port=port, log_level="warning")


def launch_backends(host: str = "127.0.0.1", ports: Dict[str, int] | None = None) -> List[multiprocessing.Process]:
    apps = build_backend_apps()
    ports = ports or {
        "crm_system": 8081,
        "ticketing_platform": 8082,
        "transaction_dispute_api": 8083,
        "customer_communication_gateway": 8084,
    }

    processes: List[multiprocessing.Process] = []
    for name, app in apps.items():
        proc = multiprocessing.Process(target=_run_uvicorn, args=(app, host, ports[name]), daemon=True)
        proc.start()
        processes.append(proc)
    return processes
