from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from .detector import DriftMonitoringSuite

router = APIRouter(prefix="/eval", tags=["System Quality Drift Governance"])
detector_suite = DriftMonitoringSuite()

@router.post("/drift", response_model=Dict[str, Any])

def run_on_demand_drift_check(runtime_payload: Dict[str, Any]):
    """Runs a drift check on demand using runtime payload vectors."""
    try:
        results = detector_suite.evaluate_system_drift(runtime_payload, baseline_name="production_v4")
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to complete drift validation check: {str(e)}")