from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from pathlib import Path

from backend.models.database import get_db
from backend.models.schemas import Repository, FileRecord, SymbolRecord
from backend.schemas.pydantic_models import (
    RepoConnectRequest, RepoResponse, FileDetailResponse, SymbolResponse
)
from backend.services.repo_service import RepoService
from backend.services.analysis_service import AnalysisService

router = APIRouter(prefix="/repos", tags=["Repositories"])

@router.post("/connect", response_model=RepoResponse)
def connect_repository(payload: RepoConnectRequest, background_tasks: BackgroundTasks = None, db: Session = Depends(get_db)):
    repo_meta = RepoService.clone_or_link_repository(
        url_or_path=payload.url_or_path,
        branch=payload.branch or "main",
        custom_name=payload.name
    )

    # Check if repo already registered
    existing = db.query(Repository).filter(Repository.full_name == repo_meta["full_name"]).first()
    if existing:
        existing.local_path = repo_meta["local_path"]
        existing.url = repo_meta["url"]
        db.commit()
        AnalysisService.index_repository(existing.id, db)
        db.refresh(existing)
        return existing

    new_repo = Repository(
        name=repo_meta["name"],
        full_name=repo_meta["full_name"],
        url=repo_meta["url"],
        local_path=repo_meta["local_path"],
        default_branch=repo_meta["default_branch"],
        indexing_status="pending"
    )
    db.add(new_repo)
    db.commit()
    db.refresh(new_repo)

    # Trigger indexing
    AnalysisService.index_repository(new_repo.id, db)
    db.refresh(new_repo)
    return new_repo

@router.get("", response_model=List[RepoResponse])
def list_repositories(db: Session = Depends(get_db)):
    return db.query(Repository).order_by(Repository.updated_at.desc()).all()

@router.get("/{repo_id}", response_model=RepoResponse)
def get_repository(repo_id: int, db: Session = Depends(get_db)):
    repo = db.query(Repository).filter(Repository.id == repo_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    return repo

@router.get("/{repo_id}/files")
def list_repo_files(repo_id: int, db: Session = Depends(get_db)):
    files = db.query(FileRecord).filter(FileRecord.repo_id == repo_id).all()
    return [
        {
            "id": f.id,
            "path": f.path,
            "language": f.language,
            "lines_of_code": f.lines_of_code,
            "complexity": f.cyclomatic_complexity,
            "maintainability_index": f.maintainability_index,
            "has_tests": f.has_tests
        }
        for f in files
    ]

@router.get("/{repo_id}/file-content", response_model=FileDetailResponse)
def get_file_content(repo_id: int, file_path: str, db: Session = Depends(get_db)):
    repo = db.query(Repository).filter(Repository.id == repo_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    norm_path = file_path.replace("\\", "/").strip()

    file_rec = db.query(FileRecord).filter(
        FileRecord.repo_id == repo_id,
        FileRecord.path == norm_path
    ).first()

    full_p = Path(repo.local_path) / norm_path
    content = ""
    if full_p.exists() and full_p.is_file():
        content = full_p.read_text(encoding="utf-8", errors="replace")

    symbols = db.query(SymbolRecord).filter(
        SymbolRecord.repo_id == repo_id,
        SymbolRecord.file_path == norm_path
    ).all()

    return FileDetailResponse(
        path=norm_path,
        language=file_rec.language if file_rec else "text",
        lines_of_code=file_rec.lines_of_code if file_rec else len(content.splitlines()),
        cyclomatic_complexity=file_rec.cyclomatic_complexity if file_rec else 1.0,
        maintainability_index=file_rec.maintainability_index if file_rec else 100.0,
        content=content,
        symbols=[
            SymbolResponse(
                name=s.name,
                symbol_type=s.symbol_type,
                file_path=s.file_path,
                line_start=s.line_start,
                line_end=s.line_end,
                signature=s.signature,
                docstring=s.docstring,
                complexity=s.complexity,
                is_api_endpoint=s.is_api_endpoint,
                http_method=s.http_method,
                http_path=s.http_path
            )
            for s in symbols
        ]
    )

@router.post("/{repo_id}/reindex")
def reindex_repository(repo_id: int, db: Session = Depends(get_db)):
    result = AnalysisService.index_repository(repo_id, db)
    return {"message": "Re-indexing completed successfully", "stats": result}
