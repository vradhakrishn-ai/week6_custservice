from typing import Dict, Any, List
from app.prompt_loader import VersionControlledPromptLoader
from app.prompt_models import PromptSchema


class PromptTemplate:
    def __init__(self, schema: PromptSchema):
        self.schema = schema

    def get_metadata(self) -> Dict[str, Any]:
        return {
            "name": self.schema.name,
            "version": self.schema.version,
            "author": self.schema.author,
            "model_compatibility": self.schema.model_compatibility,
            "input_variables": self.schema.input_variables,
            "changelog": self.schema.changelog,
        }

    @property
    def template(self) -> str:
        return self.schema.template


class PromptRegistry:
    def __init__(self):
        self.loader = VersionControlledPromptLoader()
        self.prompts: Dict[str, PromptTemplate] = {}
        self.reload()

    def reload(self):
        self.prompts = {}
        for file_name in self.loader.list_prompt_names():
            try:
                schema = self.loader.get_metadata(file_name)
                self.prompts[file_name] = PromptTemplate(schema)
            except FileNotFoundError:
                continue
            except Exception:
                continue

    def get(self, name: str) -> PromptTemplate:
        if name not in self.prompts:
            raise KeyError(f"Prompt template '{name}' not found in registry")
        return self.prompts[name]

    def list_all(self) -> List[Dict[str, Any]]:
        return [p.get_metadata() for p in self.prompts.values()]


_registry_instance = None


def get_registry() -> PromptRegistry:
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = PromptRegistry()
    return _registry_instance