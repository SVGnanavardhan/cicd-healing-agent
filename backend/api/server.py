"""
CI/CD Healing Agent — FastAPI REST API
POST /api/run         — trigger a new agent run
GET  /api/run/{id}   — poll run status
GET  /api/run/{id}/results — get results.json
GET  /api/runs        — list recent runs
GET  /health          — health check
"""

import os, json, uuid, tempfile
from pathlib import Path
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add agent to path
import sys
sys.path.append(str(Path(__file__).parent.parent / "agent"))
from orchestrator import CICDHealingAgent

app = FastAPI(
    title="CI/CD Healing Agent API",
    description="RIFT 2026 — Autonomous CI/CD Healing Agent",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

RUNS: dict = {}

# Cross-platform temp dir (works on Windows + Linux)
_default_results = str(Path(tempfile.gettempdir()) / "cicd_results")
RESULTS_DIR = os.environ.get("RESULTS_DIR", _default_results)
os.makedirs(RESULTS_DIR, exist_ok=True)


# ─── Models ───────────────────────────────────────────────────────────────────
class RunRequest(BaseModel):
    repo_url:     str
    team_name:    str
    leader_name:  str
    github_token: str = ""   # optional — empty string means no token

class RunStatus(BaseModel):
    run_id:      str
    status:      str   # pending | running | complete | error
    started_at:  str
    branch_name: Optional[str] = None
    results:     Optional[dict] = None
    error:       Optional[str]  = None


# ─── Background agent execution ───────────────────────────────────────────────
def execute_agent(run_id: str, repo_url: str, team_name: str, leader_name: str, github_token: str = ""):
    RUNS[run_id]["status"] = "running"
    output_file = f"{RESULTS_DIR}/results_{run_id}.json"
    try:
        # Token from frontend overrides env var
        if github_token:
            os.environ["GITHUB_TOKEN"] = github_token
        agent   = CICDHealingAgent()
        results = agent.run(repo_url, team_name, leader_name, output_file)
        RUNS[run_id].update({
            "status":      "complete",
            "branch_name": results.get("branch_name"),
            "results":     results,
        })
    except Exception as e:
        RUNS[run_id].update({"status": "error", "error": str(e)})


# ─── Routes ───────────────────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {"status": "ok", "timestamp": datetime.now().isoformat(), "service": "CI/CD Healing Agent"}

@app.post("/api/run", response_model=RunStatus)
def trigger_run(req: RunRequest, bg: BackgroundTasks):
    """Trigger a new agent run. Returns run_id for polling."""
    run_id = str(uuid.uuid4())
    RUNS[run_id] = {
        "run_id":      run_id,
        "status":      "pending",
        "started_at":  datetime.now().isoformat(),
        "branch_name": None,
        "results":     None,
        "error":       None,
    }
    bg.add_task(execute_agent, run_id, req.repo_url, req.team_name, req.leader_name, req.github_token)
    return RunStatus(**RUNS[run_id])

@app.get("/api/run/{run_id}", response_model=RunStatus)
def get_run(run_id: str):
    """Poll run status and results."""
    if run_id not in RUNS:
        raise HTTPException(404, f"Run {run_id} not found")
    return RunStatus(**RUNS[run_id])

@app.get("/api/run/{run_id}/results")
def get_results(run_id: str):
    """Return results.json for a completed run."""
    if run_id not in RUNS:
        raise HTTPException(404, f"Run {run_id} not found")
    if RUNS[run_id]["status"] != "complete":
        raise HTTPException(202, "Run not yet complete")
    return RUNS[run_id]["results"]

@app.get("/api/runs")
def list_runs():
    """List 20 most recent runs."""
    runs = sorted(RUNS.values(), key=lambda r: r["started_at"], reverse=True)[:20]
    return {"total": len(RUNS), "runs": runs}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))