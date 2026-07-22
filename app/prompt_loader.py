import os
import yaml
import logging
from typing import Dict, Any, Optional
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from .prompt_validator import PromptValidator
from .prompt_models import PromptSchema

logger = logging.getLogger("securebank.prompt_manager.loader")

class VersionControlledPromptLoader:
    """Manages disk parsing states and hot-reloads templates upon local file modification."""

    def __init__(self, prompts_dir: Optional[str] = None):
# Default to the package-level prompts directory when not provided
        if prompts_dir is None:
            prompts_dir = os.path.normpath(os.path.join(os.path.dirname(__file__), "prompts"))
        self.prompts_dir = prompts_dir
        self._cache: Dict[str, PromptSchema] = {}
        self._mtimes: Dict[str, float] = {}
        
        os.makedirs(self.prompts_dir, exist_ok=True)

    def _load_and_cache(self, prompt_name: str) -> PromptSchema:
        file_path = os.path.join(self.prompts_dir, f"{prompt_name}.yaml")
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Missing configuration file at destination path: {file_path}")

        current_mtime = os.path.getmtime(file_path)
        
# Hot-reload if the file is not in cache or if the file timestamp has changed
        if prompt_name not in self._cache or self._mtimes.get(prompt_name, 0.0) < current_mtime:
            logger.info(f"Disk change detected. Parsing prompt configuration: {prompt_name}.yaml")
            with open(file_path, "r", encoding="utf-8") as f:
                raw_yaml = yaml.safe_load(f)
                
# Run the parsed file through the compliance validation layer
            validated_prompt = PromptValidator.validate_config(raw_yaml)
            
            self._cache[prompt_name] = validated_prompt
            self._mtimes[prompt_name] = current_mtime
            
        return self._cache[prompt_name]

    def get_prompt_template(self, prompt_name: str) -> ChatPromptTemplate:
        """Constructs a LangChain expression engine mapping chat histories cleanly."""
        schema = self._load_and_cache(prompt_name)
        
        message_steps = [("system", schema.template)]

# Programmatically bind structural flow slots if specified by configuration
        if "chat_history" in schema.input_variables:
            message_steps.append(MessagesPlaceholder(variable_name="chat_history"))

# Determine the human input variable name from the prompt schema (fallback to 'input')
        human_vars = [v for v in getattr(schema, "input_variables", []) if v not in ("chat_history", "agent_scratchpad")]
        human_var = human_vars[0] if human_vars else "input"
        message_steps.append(("human", f"{{{human_var}}}"))

        if "agent_scratchpad" in schema.input_variables:
            message_steps.append(MessagesPlaceholder(variable_name="agent_scratchpad"))
            
        return ChatPromptTemplate.from_messages(message_steps)

    def get_metadata(self, prompt_name: str) -> PromptSchema:
        """Returns the audited metadata schema attributes mapped to the target token."""
        return self._load_and_cache(prompt_name)

    def list_prompt_names(self) -> list[str]:
        """Returns all prompt template names currently available on disk."""
        return [os.path.splitext(f)[0] for f in os.listdir(self.prompts_dir) if f.endswith(".yaml") or f.endswith(".yml")]


HotReloadPromptManager = VersionControlledPromptLoader