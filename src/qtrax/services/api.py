# src/qtrax/services/api.py

from fastapi import FastAPI, Body, HTTPException # type: ignore
from typing import Any, Dict
import tempfile
import yaml # type: ignore
import json
import os

from src.qtrax.services.dynamic_runner import dynamic_solve

app = FastAPI(
    title="Q-TRAX Dynamic Solver API",
    description="Submit a dynamic routing problem (graph + agents + events) and "
                "receive multi-agent routes optimized by a quantum-inspired annealer.",
    version="1.0.0"
)

@app.post("/solve_dynamic", response_model=Dict[str, Any])
async def solve_dynamic_endpoint(request_body: Dict[str, Any] = Body(...)):
    """
    Accepts a JSON body with:
      - nodes:      [ { id: int, attributes: {...} }, ... ]
      - edges:      [ { source: int, target: int, weight: float, attributes: {...} }, ... ]
      - constraints: {...}                       # optional constraints
      - agents:     [ { id: str, start: int, goal: int }, ... ]
      - events:     [ { tick: int, action: {...} }, ... ]  # optional dynamic events schedule
      - solver_params: { max_tick: int, mini_iter: int, start_temp: float, ... }  # optional overrides

    Returns a dict mapping each agent ID to its final route and status.
    """
    # 1. Write the incoming JSON to a temporary YAML file so our dynamic_solve can load it
    try:
        tmp = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".yaml")
        yaml.safe_dump(request_body, tmp, sort_keys=False)
        tmp.flush()
        tmp_name = tmp.name
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to serialize request to YAML: {e}")

    # 2. Extract solver parameters (with defaults)
    solver_params = request_body.get("solver_params", {})
    max_tick = solver_params.get("max_tick", 100)
    use_yaml = True  # always using the temporary YAML

    # 3. Prepare a temporary output path
    out_tmp = tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json")
    out_path = out_tmp.name
    out_tmp.close()

    # 4. Call the dynamic_solve routine
    try:
        results = dynamic_solve(
            config_path=tmp_name,
            output_path=out_path,
            use_yaml=use_yaml,
            max_tick=max_tick
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during dynamic_solve: {e}")

    # 5. Read back the JSON that dynamic_solve wrote (for completeness)
    try:
        with open(out_path, "r") as f:
            solution_json = json.load(f)
    except Exception:
        # If reading fails, fallback to returning the `results` dict directly
        solution_json = {"routes": results, "error": "Output JSON not found or unreadable"} # type: ignore

    # 6. Clean up temporary files
    os.unlink(tmp_name)
    os.unlink(out_path)

    return solution_json # type: ignore

