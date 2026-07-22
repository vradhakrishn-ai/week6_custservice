from pydantic import BaseModel, Field
from typing import List, Dict, Any
from app.llm import get_llm

class SubTaskUnit(BaseModel):
    task_id: str = Field(..., description="Unique sub-task sequence key.")
    assigned_capability: str = Field(..., description="The capability needed to process this step.")
    payload_input: str = Field(..., description="Extracted instruction slice for the target agent.")

class DecompositionPayload(BaseModel):
    reasoning_plan: str = Field(..., description="Logical step-by-step resolution strategy.")
    sub_tasks: List[SubTaskUnit] = Field(..., description="Ordered collection of execution steps.")

class ComplexTaskDecomposer:
    """Splits multi-domain customer queries into structured, trackable sub-tasks."""

    def __init__(self):
        self.llm = get_llm().with_structured_output(DecompositionPayload, method="function_calling")

    def split_query(self, complex_query: str) -> DecompositionPayload:
        """Analyzes a multi-domain request to generate a structured execution plan."""
        system_instructions = (
            "You are an expert financial systems task coordinator. Split complex banking queries "
            "into clear, actionable steps matching these capabilities: [intent_parsing, sentiment_extraction, "
            "balance_adjustment, account_updates, regulatory_filing, ombudsman_routing]."
        )
        
        prompt = [
            ("system", system_instructions),
            ("human", f"Decompose this customer request: '{complex_query}'")
        ]
        
        return self.llm.invoke(prompt)