from pydantic import BaseModel, Field
from typing import List, Dict, Any

class PromptVersionEntry(BaseModel):
    version: str = Field(..., description="Semantic version string (e.g., 2.1.0).")
    description: str = Field(..., description="Changelog details summarizing the adjustment description.")

class PromptSchema(BaseModel):
    name: str = Field(..., description="Unique programmatic moniker for target chain routing lookup.")
    version: str = Field(..., description="Active version tag applied to the system run.")
    author: str = Field(..., description="Dev/Compliance team tracking identity.")
    model_compatibility: List[str] = Field(..., description="Array of validated target foundational models.")
    changelog: List[Dict[str, str]] = Field(..., description="Historical version log list array.")
    input_variables: List[str] = Field(..., description="Required template variables for runtime execution verification.")
    template: str = Field(..., description="Raw text system instructions with variable keys.")