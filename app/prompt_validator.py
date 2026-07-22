import re
from typing import Dict, Any
from .prompt_models import PromptSchema

class PromptValidator:
    """Validates structural fields and template variables before caching changes."""

    @staticmethod
    def validate_config(raw_data: Dict[str, Any]) -> PromptSchema:
        """Parses raw dictionary configurations against the strict Pydantic compliance schema."""
# Enforce typing normalization via structural schemas
        validated_schema = PromptSchema(**raw_data)
        
# Verify that all template bracket tags exactly match declared input_variables
        brackets = set(re.findall(r"\{([a-zA-Z0-9_]+)\}", validated_schema.template))
        declared = set(validated_schema.input_variables)
        
# Ignore LangChain core runtime variables if present in the template context string
        brackets.discard("agent_scratchpad")
        brackets.discard("chat_history")
        
        missing_declarations = brackets - declared
        if missing_declarations:
            raise ValueError(
                f"Validation Breach: Variables {missing_declarations} are used in the "
                f"template text but missing from 'input_variables' declarations."
            )
            
        return validated_schema