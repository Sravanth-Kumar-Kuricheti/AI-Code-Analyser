import os
import time
import requests
from typing import Dict, Any, List, Optional
from backend.config import settings
from backend.models.database import SessionLocal, init_db
from backend.models.schemas import Repository, FileRecord

BASE_URL = settings.BACKEND_API_URL + settings.API_PREFIX

_BACKEND_ALIVE: Optional[bool] = None
_LAST_CHECK_TIME: float = 0.0

def _is_backend_available() -> bool:
    """Probes backend health with a 0.4s fast timeout and caches status for 10 seconds."""
    global _BACKEND_ALIVE, _LAST_CHECK_TIME
    now = time.time()
    if _BACKEND_ALIVE is not None and (now - _LAST_CHECK_TIME) < 10:
        return _BACKEND_ALIVE
    try:
        resp = requests.get(f"{settings.BACKEND_API_URL}/api/v1/health", timeout=0.4)
        _BACKEND_ALIVE = (resp.status_code == 200)
    except Exception:
        _BACKEND_ALIVE = False
    _LAST_CHECK_TIME = now
    return _BACKEND_ALIVE

def _safe_request(url: str, method: str = "GET", json_data: dict = None, params: dict = None, timeout: int = 15, fallback=None):
    """Executes HTTP request if server is alive, otherwise dispatches in-process with 0 delay."""
    if _is_backend_available():
        try:
            if method == "GET":
                resp = requests.get(url, params=params, timeout=timeout)
            else:
                resp = requests.post(url, json=json_data, timeout=timeout)
            resp.raise_for_status()
            return resp.json()
        except Exception:
            if fallback:
                return fallback()
            raise
    if fallback:
        return fallback()
    raise RuntimeError("Backend server is unreachable and no in-process fallback was provided.")

def _serialize_repo(r: Repository) -> Dict[str, Any]:
    """Converts Repository ORM model to dictionary."""
    return {
        "id": r.id,
        "name": r.name,
        "full_name": r.full_name,
        "url": r.url,
        "local_path": r.local_path,
        "default_branch": r.default_branch,
        "total_files": r.total_files,
        "total_lines": r.total_lines,
        "primary_language": r.primary_language,
        "health_score": r.health_score,
        "is_indexed": r.is_indexed,
        "indexing_status": r.indexing_status,
        "created_at": str(r.created_at) if getattr(r, "created_at", None) else None
    }

def _serialize_file(f: FileRecord) -> Dict[str, Any]:
    """Converts FileRecord ORM model to dictionary."""
    return {
        "id": f.id,
        "repo_id": f.repo_id,
        "path": f.path,
        "language": f.language,
        "size_bytes": f.size_bytes,
        "lines_of_code": f.lines_of_code,
        "cyclomatic_complexity": f.cyclomatic_complexity,
        "maintainability_index": f.maintainability_index,
        "has_tests": f.has_tests
    }

class RepoPilotAPI:
    """API Client supporting dual-mode: Remote FastAPI REST API or standalone in-process fallback."""

    @staticmethod
    def connect_repo(url_or_path: str, branch: str = "main", name: str = None) -> Dict[str, Any]:
        def fallback():
            init_db()
            db = SessionLocal()
            try:
                from backend.api.repo_routes import connect_repository
                from backend.schemas.pydantic_models import RepoConnectRequest
                res = connect_repository(RepoConnectRequest(url_or_path=url_or_path, branch=branch, name=name), db=db)
                return _serialize_repo(res)
            finally:
                db.close()
        return _safe_request(f"{BASE_URL}/repos/connect", "POST", {"url_or_path": url_or_path, "branch": branch, "name": name}, timeout=180, fallback=fallback)

    @staticmethod
    def list_repos() -> List[Dict[str, Any]]:
        def fallback():
            init_db()
            db = SessionLocal()
            try:
                from backend.api.repo_routes import list_repositories
                return [_serialize_repo(r) for r in list_repositories(db=db)]
            finally:
                db.close()
        return _safe_request(f"{BASE_URL}/repos", "GET", timeout=10, fallback=fallback)

    @staticmethod
    def get_repo(repo_id: int) -> Dict[str, Any]:
        def fallback():
            init_db()
            db = SessionLocal()
            try:
                from backend.api.repo_routes import get_repository
                return _serialize_repo(get_repository(repo_id, db=db))
            finally:
                db.close()
        return _safe_request(f"{BASE_URL}/repos/{repo_id}", "GET", timeout=10, fallback=fallback)

    @staticmethod
    def reindex_repo(repo_id: int) -> Dict[str, Any]:
        def fallback():
            init_db()
            db = SessionLocal()
            try:
                from backend.api.repo_routes import reindex_repository
                return reindex_repository(repo_id, db=db)
            finally:
                db.close()
        return _safe_request(f"{BASE_URL}/repos/{repo_id}/reindex", "POST", timeout=180, fallback=fallback)

    @staticmethod
    def get_repo_files(repo_id: int) -> List[Dict[str, Any]]:
        def fallback():
            init_db()
            db = SessionLocal()
            try:
                from backend.api.repo_routes import list_repo_files
                return [_serialize_file(f) for f in list_repo_files(repo_id, db=db)]
            finally:
                db.close()
        return _safe_request(f"{BASE_URL}/repos/{repo_id}/files", "GET", timeout=10, fallback=fallback)

    @staticmethod
    def get_file_content(repo_id: int, file_path: str) -> Dict[str, Any]:
        def fallback():
            init_db()
            db = SessionLocal()
            try:
                from backend.api.repo_routes import get_file_content
                return get_file_content(repo_id, file_path, db=db)
            finally:
                db.close()
        return _safe_request(f"{BASE_URL}/repos/{repo_id}/file-content", "GET", params={"file_path": file_path}, timeout=15, fallback=fallback)

    @staticmethod
    def ask_chat(repo_id: int, query: str) -> Dict[str, Any]:
        def fallback():
            init_db()
            db = SessionLocal()
            try:
                from backend.api.chat_routes import ask_codebase_qa
                from backend.schemas.pydantic_models import ChatRequest
                return ask_codebase_qa(ChatRequest(repo_id=repo_id, query=query), db=db)
            finally:
                db.close()
        return _safe_request(f"{BASE_URL}/chat/qa", "POST", {"repo_id": repo_id, "query": query}, timeout=60, fallback=fallback)

    @staticmethod
    def get_architecture_graph(repo_id: int) -> Dict[str, Any]:
        def fallback():
            init_db()
            db = SessionLocal()
            try:
                from backend.api.architecture_routes import get_dependency_graph
                return get_dependency_graph(repo_id, db=db)
            finally:
                db.close()
        return _safe_request(f"{BASE_URL}/architecture/{repo_id}/graph", "GET", timeout=15, fallback=fallback)

    @staticmethod
    def get_architecture_cycles(repo_id: int) -> Dict[str, Any]:
        def fallback():
            init_db()
            db = SessionLocal()
            try:
                from backend.api.architecture_routes import get_circular_dependencies
                return get_circular_dependencies(repo_id, db=db)
            finally:
                db.close()
        return _safe_request(f"{BASE_URL}/architecture/{repo_id}/cycles", "GET", timeout=15, fallback=fallback)

    @staticmethod
    def get_api_call_flows(repo_id: int) -> Dict[str, Any]:
        def fallback():
            init_db()
            db = SessionLocal()
            try:
                from backend.api.architecture_routes import get_call_flows
                return get_call_flows(repo_id, db=db)
            finally:
                db.close()
        return _safe_request(f"{BASE_URL}/architecture/{repo_id}/call-flows", "GET", timeout=15, fallback=fallback)

    @staticmethod
    def simulate_impact(repo_id: int, target_file: str, target_symbol: str = "") -> Dict[str, Any]:
        def fallback():
            init_db()
            db = SessionLocal()
            try:
                from backend.api.impact_routes import simulate_change_impact
                from backend.schemas.pydantic_models import ImpactRequest
                return simulate_change_impact(ImpactRequest(repo_id=repo_id, target_file=target_file, target_symbol=target_symbol), db=db)
            finally:
                db.close()
        return _safe_request(f"{BASE_URL}/impact/simulate", "POST", {"repo_id": repo_id, "target_file": target_file, "target_symbol": target_symbol}, timeout=25, fallback=fallback)

    @staticmethod
    def generate_tests(repo_id: int, file_path: str, symbol_name: str, framework: str = "pytest") -> Dict[str, Any]:
        def fallback():
            init_db()
            db = SessionLocal()
            try:
                from backend.api.test_gen_routes import generate_test_cases
                from backend.schemas.pydantic_models import TestGenRequest
                return generate_test_cases(TestGenRequest(repo_id=repo_id, file_path=file_path, symbol_name=symbol_name, framework=framework), db=db)
            finally:
                db.close()
        return _safe_request(f"{BASE_URL}/tests/generate", "POST", {"repo_id": repo_id, "file_path": file_path, "symbol_name": symbol_name, "framework": framework}, timeout=30, fallback=fallback)

    @staticmethod
    def get_tech_debt(repo_id: int) -> Dict[str, Any]:
        def fallback():
            init_db()
            db = SessionLocal()
            try:
                from backend.api.tech_debt_routes import get_technical_debt
                return get_technical_debt(repo_id, db=db)
            finally:
                db.close()
        return _safe_request(f"{BASE_URL}/tech-debt/{repo_id}", "GET", timeout=20, fallback=fallback)

    @staticmethod
    def refactor_code(repo_id: int, file_path: str, symbol_name: str, issue_description: str = "") -> Dict[str, Any]:
        def fallback():
            init_db()
            db = SessionLocal()
            try:
                from backend.api.tech_debt_routes import refactor_code_routine, RefactorRequest
                return refactor_code_routine(RefactorRequest(repo_id=repo_id, file_path=file_path, symbol_name=symbol_name, issue_description=issue_description), db=db)
            finally:
                db.close()
        return _safe_request(f"{BASE_URL}/tech-debt/refactor", "POST", {"repo_id": repo_id, "file_path": file_path, "symbol_name": symbol_name, "issue_description": issue_description}, timeout=45, fallback=fallback)

    @staticmethod
    def get_security_audit(repo_id: int) -> Dict[str, Any]:
        def fallback():
            init_db()
            db = SessionLocal()
            try:
                from backend.api.security_routes import get_security_audit
                return get_security_audit(repo_id, db=db)
            finally:
                db.close()
        return _safe_request(f"{BASE_URL}/security/{repo_id}", "GET", timeout=20, fallback=fallback)

    @staticmethod
    def get_onboarding_roadmap(repo_id: int) -> Dict[str, Any]:
        def fallback():
            init_db()
            db = SessionLocal()
            try:
                from backend.api.onboarding_routes import get_onboarding_roadmap
                return get_onboarding_roadmap(repo_id, db=db)
            finally:
                db.close()
        return _safe_request(f"{BASE_URL}/onboarding/{repo_id}/roadmap", "GET", timeout=30, fallback=fallback)

    @staticmethod
    def evaluate_architecture_decision(repo_id: int, proposed_change: str, affected_components: List[str] = None) -> Dict[str, Any]:
        def fallback():
            init_db()
            db = SessionLocal()
            try:
                from backend.api.onboarding_routes import evaluate_architecture_decision
                from backend.schemas.pydantic_models import ArchitectureDecisionRequest
                return evaluate_architecture_decision(ArchitectureDecisionRequest(repo_id=repo_id, proposed_change=proposed_change, affected_components=affected_components or []), db=db)
            finally:
                db.close()
        return _safe_request(f"{BASE_URL}/onboarding/architecture-decision", "POST", {"repo_id": repo_id, "proposed_change": proposed_change, "affected_components": affected_components or []}, timeout=30, fallback=fallback)

    @staticmethod
    def review_pr(repo_id: int, diff_text: str, title: str = "PR Review") -> Dict[str, Any]:
        def fallback():
            init_db()
            db = SessionLocal()
            try:
                from backend.api.onboarding_routes import review_pr
                from backend.schemas.pydantic_models import PRReviewRequest
                return review_pr(PRReviewRequest(repo_id=repo_id, diff_text=diff_text, title=title), db=db)
            finally:
                db.close()
        return _safe_request(f"{BASE_URL}/onboarding/pr-review", "POST", {"repo_id": repo_id, "diff_text": diff_text, "title": title}, timeout=30, fallback=fallback)

api = RepoPilotAPI()
