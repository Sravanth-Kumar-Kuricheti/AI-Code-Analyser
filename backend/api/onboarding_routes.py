from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from backend.models.database import get_db
from backend.models.schemas import Repository, FileRecord, SymbolRecord
from backend.schemas.pydantic_models import (
    ArchitectureDecisionRequest, PRReviewRequest
)
from ai_engine.llm.client import llm_client
from ai_engine.prompts.system_prompts import (
    ONBOARDING_ROADMAP_PROMPT, ARCHITECTURE_DECISION_PROMPT, PR_REVIEW_PROMPT
)

router = APIRouter(prefix="/onboarding", tags=["Developer Onboarding & Decisions"])

@router.get("/{repo_id}/roadmap")
def get_onboarding_roadmap(repo_id: int, db: Session = Depends(get_db)):
    repo = db.query(Repository).filter(Repository.id == repo_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    files = db.query(FileRecord).filter(FileRecord.repo_id == repo_id).all()
    symbols = db.query(SymbolRecord).filter(SymbolRecord.repo_id == repo_id).all()

    # Identify entry points (e.g. main.py, app.py, index.js, Dockerfile)
    entry_points = []
    core_modules = []
    tests = []

    for f in files:
        fname = f.path.lower()
        if any(ep in fname for ep in ["main.", "app.", "index.", "server.", "streamlit_app"]):
            entry_points.append(f.path)
        elif "test" in fname:
            tests.append(f.path)
        else:
            core_modules.append(f.path)

    # Prompt LLM for structured onboarding narrative
    prompt_context = (
        f"Repository: {repo.name}\n"
        f"Primary Language: {repo.primary_language}\n"
        f"Total Files: {repo.total_files}\n"
        f"Identified Entrypoints: {entry_points}\n"
        f"Key Core Modules: {core_modules[:15]}\n"
        f"Test Suites: {tests[:5]}\n"
    )

    roadmap_text = llm_client.generate(ONBOARDING_ROADMAP_PROMPT, prompt_context)

    return {
        "repo_id": repo_id,
        "repo_name": repo.name,
        "entry_points": entry_points,
        "core_modules": core_modules[:10],
        "test_suites": tests,
        "roadmap_narrative": roadmap_text,
        "day_one_checklist": [
            f"1. Clone repository and verify environment setup.",
            f"2. Inspect primary entrypoints: {', '.join(entry_points) or 'Repository root files'}.",
            f"3. Run automated test suites: {', '.join(tests[:2]) or 'pytest'}.",
            f"4. Review domain services and dependency flows."
        ]
    }

@router.post("/architecture-decision")
def advise_architecture_decision(payload: ArchitectureDecisionRequest, db: Session = Depends(get_db)):
    repo = db.query(Repository).filter(Repository.id == payload.repo_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    user_prompt = (
        f"Repository: {repo.name}\n"
        f"Proposed Architecture Modification: {payload.proposed_change}\n"
        f"Affected Components: {payload.affected_components}\n"
    )

    advice = llm_client.generate(ARCHITECTURE_DECISION_PROMPT, user_prompt)
    return {
        "repo_id": payload.repo_id,
        "proposed_change": payload.proposed_change,
        "evaluation": advice
    }

@router.post("/pr-review")
def review_pull_request(payload: PRReviewRequest, db: Session = Depends(get_db)):
    user_prompt = (
        f"PR Title: {payload.title}\n"
        f"Code Diff:\n{payload.diff_text}\n"
    )
    review_feedback = llm_client.generate(PR_REVIEW_PROMPT, user_prompt)
    return {
        "repo_id": payload.repo_id,
        "review_summary": review_feedback
    }
