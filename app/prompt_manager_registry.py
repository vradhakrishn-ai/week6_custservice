from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
from .prompt_loader import VersionControlledPromptLoader
from .prompt_models import PromptSchema

router = APIRouter(prefix="/prompts", tags=["Prompt Version Governance"])
# Persistent loader instance for runtime thread handling
global_loader = VersionControlledPromptLoader()

def get_loader() -> VersionControlledPromptLoader:
    return global_loader

@router.get("/list", response_model=List[str])
def list_active_prompts(loader: VersionControlledPromptLoader = Depends(get_loader)):
    """Scans the tracking workspace folder to return file names currently registered on disk."""
    files = os.listdir(loader.prompts_dir)
    return [os.path.splitext(f)[0] for f in files if f.endswith(".yaml")]

@router.get("/view/{name}", response_model=PromptSchema)

def view_prompt_details(name: str, loader: VersionControlledPromptLoader = Depends(get_loader)):
    """Fetches the active prompt template config, including its structural changelog history."""
    try:
        return loader.get_metadata(name)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Bad request parameters: {str(e)}")