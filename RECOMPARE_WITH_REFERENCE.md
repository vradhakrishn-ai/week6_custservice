# Recompare with the reference project

I compared the current project against the reference app in [customer-service-chatbot-mcp-main](customer-service-chatbot-mcp-main) and the main gaps are below.

## High-priority missing items

1. Dedicated API route modules
   - The reference project has a structured API layer under [customer-service-chatbot-mcp-main/app/api](customer-service-chatbot-mcp-main/app/api) for auth, chat, eval, health, HITL, MCP, prompts, and reset.
   - The current app keeps most of this in [app/main.py](app/main.py) and related modules, so the routing surface is not split as cleanly.

2. Service-layer modules
   - The reference includes explicit services such as [customer-service-chatbot-mcp-main/app/services/hitl_service.py](customer-service-chatbot-mcp-main/app/services/hitl_service.py), [customer-service-chatbot-mcp-main/app/services/langsmith_service.py](customer-service-chatbot-mcp-main/app/services/langsmith_service.py), [customer-service-chatbot-mcp-main/app/services/logging_service.py](customer-service-chatbot-mcp-main/app/services/logging_service.py), [customer-service-chatbot-mcp-main/app/services/mcp_client.py](customer-service-chatbot-mcp-main/app/services/mcp_client.py), [customer-service-chatbot-mcp-main/app/services/rbac_service.py](customer-service-chatbot-mcp-main/app/services/rbac_service.py), and [customer-service-chatbot-mcp-main/app/services/session_memory.py](customer-service-chatbot-mcp-main/app/services/session_memory.py).
   - The current project has some equivalent concepts, but not the same modular service package.

3. Prompt management package
   - The reference has a dedicated prompt subsystem under [customer-service-chatbot-mcp-main/app/prompts](customer-service-chatbot-mcp-main/app/prompts) with files like [customer-service-chatbot-mcp-main/app/prompts/prompt_manager.py](customer-service-chatbot-mcp-main/app/prompts/prompt_manager.py), [customer-service-chatbot-mcp-main/app/prompts/semantic_selector.py](customer-service-chatbot-mcp-main/app/prompts/semantic_selector.py), and [customer-service-chatbot-mcp-main/app/prompts/fewshot_examples.py](customer-service-chatbot-mcp-main/app/prompts/fewshot_examples.py).
   - The current project has prompt loading and registry support, but not this same structured prompt-management layer.

4. Endpoint modules for ingestion and retrieval
   - The reference includes dedicated endpoints such as [customer-service-chatbot-mcp-main/app/endpoints/evaluate.py](customer-service-chatbot-mcp-main/app/endpoints/evaluate.py), [customer-service-chatbot-mcp-main/app/endpoints/ingest.py](customer-service-chatbot-mcp-main/app/endpoints/ingest.py), [customer-service-chatbot-mcp-main/app/endpoints/retrieve.py](customer-service-chatbot-mcp-main/app/endpoints/retrieve.py), and [customer-service-chatbot-mcp-main/app/endpoints/sources.py](customer-service-chatbot-mcp-main/app/endpoints/sources.py).
   - The current project does not have the same endpoint packaging yet.

5. Reference-specific prompt templates
   - The reference contains prompt YAMLs such as [customer-service-chatbot-mcp-main/prompts/_active.yaml](customer-service-chatbot-mcp-main/prompts/_active.yaml), [customer-service-chatbot-mcp-main/prompts/hitl_review.v1.0.0.yaml](customer-service-chatbot-mcp-main/prompts/hitl_review.v1.0.0.yaml), [customer-service-chatbot-mcp-main/prompts/intent_classifier.v1.0.0.yaml](customer-service-chatbot-mcp-main/prompts/intent_classifier.v1.0.0.yaml), [customer-service-chatbot-mcp-main/prompts/rag_qa.v1.0.0.yaml](customer-service-chatbot-mcp-main/prompts/rag_qa.v1.0.0.yaml), [customer-service-chatbot-mcp-main/prompts/sentiment.v1.0.0.yaml](customer-service-chatbot-mcp-main/prompts/sentiment.v1.0.0.yaml), and [customer-service-chatbot-mcp-main/prompts/triage.v1.0.0.yaml](customer-service-chatbot-mcp-main/prompts/triage.v1.0.0.yaml).
   - The current project has its own prompt assets, but these specific versions are not yet mirrored.

6. Evaluation assets
   - The reference includes richer eval artifacts such as [customer-service-chatbot-mcp-main/eval/golden_set.json](customer-service-chatbot-mcp-main/eval/golden_set.json), [customer-service-chatbot-mcp-main/eval/hitl_cases.json](customer-service-chatbot-mcp-main/eval/hitl_cases.json), [customer-service-chatbot-mcp-main/eval/hybrid_queries.json](customer-service-chatbot-mcp-main/eval/hybrid_queries.json), [customer-service-chatbot-mcp-main/eval/rbac_probes.json](customer-service-chatbot-mcp-main/eval/rbac_probes.json), and the supporting evaluators under [customer-service-chatbot-mcp-main/eval](customer-service-chatbot-mcp-main/eval).
   - The current project has expanded eval support, but not all of these assets are present yet.

## Partially covered areas

Some of the reference functionality is already present in a different shape:

- Mock backend support exists in [app/mock_backends.py](app/mock_backends.py) and [scripts/start_support_backends.py](scripts/start_support_backends.py), which partially covers the reference’s MCP/server-side testing idea.
- The current app already has a stronger retrieval pipeline and prompt/registry layer than the reference in some areas.
- The current project also includes a more detailed knowledge-base and data ingestion story than the reference’s simpler corpus layout.

## Bottom line

The current app is now functionally stronger in retrieval and local runtime setup, but it is still missing some of the reference project’s cleaner architectural pieces: a dedicated API route package, a formal service layer, a dedicated prompt-management subsystem, and a fuller evaluation asset set.
