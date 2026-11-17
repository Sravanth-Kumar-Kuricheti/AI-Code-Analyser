import pytest
from backend.main import root, health_check
from backend.api.repo_routes import list_repositories
from backend.api.tech_debt_routes import get_technical_debt, refactor_code_routine, RefactorRequest
from backend.models.database import SessionLocal, init_db
from backend.models.schemas import Repository

init_db()

def test_root_endpoint():
    res = root()
    assert res["status"] == "online"
    assert res["service"] == "RepoPilot-AI"

def test_health_endpoint():
    res = health_check()
    assert res["status"] == "healthy"

def test_list_repos_service():
    db = SessionLocal()
    try:
        repos = list_repositories(db=db)
        assert isinstance(repos, list)
    finally:
        db.close()

def test_tech_debt_and_refactor_service():
    db = SessionLocal()
    try:
        repo = db.query(Repository).first()
        if repo:
            report = get_technical_debt(repo.id, db=db)
            assert report["grade"] in ("A", "B", "C", "D")
            assert "total_debt_hours" in report

            req = RefactorRequest(
                repo_id=repo.id,
                file_path="code_engine/parser/ast_parser.py",
                symbol_name="detect_language"
            )
            refactor_res = refactor_code_routine(req, db=db)
            assert refactor_res["symbol_name"] == "detect_language"
            assert "refactored_advice" in refactor_res
            assert len(refactor_res["refactored_advice"]) > 50
    finally:
        db.close()
