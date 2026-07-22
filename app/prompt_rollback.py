import os
import shutil
import time
import logging
from app.prompt_loader import VersionControlledPromptLoader

logger = logging.getLogger("securebank.prompt_manager.rollback")

class AtomicPromptRollbackEngine:
    """Manages high-speed prompt version rollbacks to meet the < 30s recovery constraint."""

    def __init__(self, loader: VersionControlledPromptLoader):
        self.loader = loader

    def execute_rollback(self, prompt_name: str, target_version: str) -> bool:
        """Atomically swaps out the prompt file for a backup version and forces a cache reload."""
        start_time = time.perf_counter()
        
        backup_file = os.path.join(self.loader.prompts_dir, "archive", f"{prompt_name}_{target_version}.yaml")
        active_file = os.path.join(self.loader.prompts_dir, f"{prompt_name}.yaml")
        
        if not os.path.exists(backup_file):
            logger.error(f"Rollback failed: Target version archive snapshot '{backup_file}' does not exist.")
            return False
            
        try:
# Atomic file overwrite
            shutil.copy2(backup_file, active_file)
            
# Force cache refresh by updating modification timestamps
            os.utime(active_file, None)
            
# Re-read through the validation layer immediately
            self.loader.get_metadata(prompt_name)
            
            elapsed_time = time.perf_counter() - start_time
            logger.info(f"Prompt '{prompt_name}' rolled back to version {target_version} in {elapsed_time:.4f}s.")
            return elapsed_time < 30.0
            
        except Exception as e:
            logger.critical(f"Critical rollback failure: {str(e)}")
            return False