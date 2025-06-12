# ───────────────────────────────────────────────
# src/qtrax/services/api.py
# ───────────────────────────────────────────────
import os, json, yaml, tempfile, logging # type: ignore
from typing import Any, Dict

from fastapi import FastAPI, Body, HTTPException, APIRouter, Path
from fastapi.logger import logger
from rq import Queue
from rq.job import Job

from src.qtrax.services.task_queue import qtrax_queue, redis_conn
from src.qtrax.services.dynamic_task import background_dynamic_solve # type: ignore

# ── logging ─────────────────────────────────────
logger.setLevel(logging.INFO)

# ── HTTP polling router ─────────────────────────
router = APIRouter()

@router.get("/job/{job_id}/result", response_model=Dict[str, Any])
async def job_result(job_id: str = Path(..., description="RQ job-ID to fetch")): # type: ignore
    """
    200 → finished, body = job.result
    202 → still running
    404 → unknown id
    500 → job failed (exception inside worker)
    """
    q = Queue("qtrax_queue", connection=redis_conn)
    job: Job | None = q.fetch_job(job_id) # type: ignore
    if job is None:
        raise HTTPException(404, "Unknown job id")

    if job.is_finished:
        result = job.result or job.meta.get("result", {})
        if not isinstance(result, dict):
            result = {"status": "success", "routes": result} # type: ignore
        elif not result.get("status"): # type: ignore
            result = {"status": "success", "routes": result} # type: ignore
        return result # type: ignore

    if job.is_failed:
        return {"status": "error", "routes": None, "error": job.exc_info} # type: ignore
    raise HTTPException(202, "Job still running")

# ── FastAPI app ────────────────────────────────
app = FastAPI(
    title="Q-TRAX Dynamic Solver API",
    description="Enqueue dynamic-solve jobs, poll via HTTP.",
    version="1.0.0",
)
app.include_router(router)

# ── enqueue endpoint ───────────────────────────
@app.post("/enqueue_dynamic", response_model=Dict[str, str])
async def enqueue_dynamic(request_body: Dict[str, Any] = Body(...)):
    try:
        cfg_fd = tempfile.NamedTemporaryFile("w", delete=False, suffix=".yaml")
        yaml.safe_dump(request_body, cfg_fd, sort_keys=False)
        cfg_fd.flush()
        config_path = cfg_fd.name

        out_fd = tempfile.NamedTemporaryFile("w", delete=False, suffix=".json")
        output_path = out_fd.name
        out_fd.close()

        solver_params = request_body.get("solver_params", {})

        job = qtrax_queue.enqueue( # type: ignore
            background_dynamic_solve, # type: ignore
            config_path,
            output_path,
            solver_params,
            job_timeout=600,
        )
        job_id = job.get_id()
        logger.info(f"Enqueued job {job_id}")
        return {"job_id": job_id}

    except Exception:
        logger.exception("Failed to enqueue job")
        raise HTTPException(500, "Internal Server Error")
