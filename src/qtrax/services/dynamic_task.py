# src/qtrax/services/dynamic_tasks.py

import os, json, logging
from typing import Any, Dict
from rq import get_current_job
from src.qtrax.services.dynamic_runner import dynamic_solve

def background_dynamic_solve(
        config_path: str,
        output_path: str,
        solver_params: Dict[str, Any]
) -> Dict[str, Any]:
    job = get_current_job()
    job_id = job.get_id() if job else "unknown"
    payload: Dict[str, Any] = {}

    try:
        dynamic_results = dynamic_solve(
            config_path=config_path,
            output_path=output_path,
            use_yaml=True,
            max_tick=solver_params.get("max_tick", 100),
        )
        payload = {"status": "success", "routes": dynamic_results}
    except Exception as exc:
        logging.exception(f"Job {job_id}: dynamic_solve FAILED")
        payload = {"status": "error", "routes": None, "error": str(exc)}

    if os.path.exists(output_path):
        try:
            with open(output_path, "r") as f:
                file_result = json.load(f)
                if isinstance(file_result, dict):
                    payload.update(file_result) # type: ignore
        except Exception:
            logging.warning(f"Job {job_id}: could not read output JSON")

    if job:
        job.meta["result"] = payload
        job.save_meta()

    for p in (config_path, output_path):
        try:
            os.unlink(p)
        except OSError:
            pass

    return payload
