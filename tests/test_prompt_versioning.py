import pytest
import os
import yaml
from app.prompt_loader import VersionControlledPromptLoader
from app.prompt_validator import PromptValidator

@pytest.fixture
def temp_prompt_dir(tmpdir):
    """Generates an isolated temporary directory with sample prompt configs for regression testing."""
    sample_content = {
        "name": "rag_qa_chain",
        "version": "2.1.0",
        "author": "team-alpha",
        "model_compatibility": ["gpt-4o", "claude-3-5-sonnet"],
        "changelog": [{"version": "2.1.0", "change": "Added citation enforcement"}],
        "input_variables": ["context", "question", "chat_history"],
        "template": "Context: {context} \nQuestion: {question}"
    }
    
    file_path = os.path.join(tmpdir, "rag_qa.yaml")
    with open(file_path, "w", encoding="utf-8") as f:
        yaml.dump(sample_content, f)
        
    return str(tmpdir)

def test_successful_validation_and_loading(temp_prompt_dir):
    """Confirms that valid YAML configurations load without errors and parse correctly."""
    loader = VersionControlledPromptLoader(prompts_dir=temp_prompt_dir)
    meta = loader.get_metadata("rag_qa")
    
    assert meta.name == "rag_qa_chain"
    assert meta.version == "2.1.0"
    assert "context" in meta.input_variables

def test_validation_failure_on_missing_variables(temp_prompt_dir):
    """Ensures a ValueError is thrown if template brackets are missing from the declared input variables."""
    invalid_data = {
        "name": "faulty_chain",
        "version": "1.0.0",
        "author": "tester",
        "model_compatibility": ["mock-llm"],
        "changelog": [{"version": "1.0.0", "change": "Initial"}],
        "input_variables": ["question"],  # Missing the 'context' mapping variable declaration
        "template": "Context: {context} \nQuestion: {question}"
    }
    
    with pytest.raises(ValueError) as excinfo:
        PromptValidator.validate_config(invalid_data)
        
    assert "Validation Breach" in str(excinfo.value)

def test_runtime_hot_reload_reflection(temp_prompt_dir):
    """Verifies that modifications to the configuration file on disk are automatically loaded on the next call."""
    loader = VersionControlledPromptLoader(prompts_dir=temp_prompt_dir)
    
# First access to cache the baseline template parameters
    first_meta = loader.get_metadata("rag_qa")
    assert first_meta.version == "2.1.0"
    
# Simulate a hot-fix modification by altering the version and template on disk
    file_path = os.path.join(temp_prompt_dir, "rag_qa.yaml")
    with open(file_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
        
    data["version"] = "2.2.0-hotfix"
    
# Update file modification time to trigger cache invalidation
    with open(file_path, "w", encoding="utf-8") as f:
        yaml.dump(data, f)
        
    updated_meta = loader.get_metadata("rag_qa")
    assert updated_meta.version == "2.2.0-hotfix"