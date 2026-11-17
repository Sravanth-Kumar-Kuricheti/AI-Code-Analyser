import requests
from typing import Dict, Any, List, Optional
from backend.config import settings

BASE_URL = settings.BACKEND_API_URL + settings.API_PREFIX

class RepoPilotAPI:
    @staticmethod
    def connect_repo(url_or_path: str, branch: str = "main", name: str = None) -> Dict[str, Any]:
        resp = requests.post(
            f"{BASE_URL}/repos/connect",
            json={"url_or_path": url_or_path, "branch": branch, "name": name},
            timeout=180
        )
        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def list_repos() -> List[Dict[str, Any]]:
        resp = requests.get(f"{BASE_URL}/repos", timeout=10)
        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def get_repo(repo_id: int) -> Dict[str, Any]:
        resp = requests.get(f"{BASE_URL}/repos/{repo_id}", timeout=10)
        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def reindex_repo(repo_id: int) -> Dict[str, Any]:
        resp = requests.post(f"{BASE_URL}/repos/{repo_id}/reindex", timeout=120)
        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def get_repo_files(repo_id: int) -> List[Dict[str, Any]]:
        resp = requests.get(f"{BASE_URL}/repos/{repo_id}/files", timeout=10)
        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def get_file_content(repo_id: int, file_path: str) -> Dict[str, Any]:
        resp = requests.get(
            f"{BASE_URL}/repos/{repo_id}/file-content",
            params={"file_path": file_path},
            timeout=10
        )
        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def ask_chat(repo_id: int, query: str) -> Dict[str, Any]:
        resp = requests.post(
            f"{BASE_URL}/chat/qa",
            json={"repo_id": repo_id, "query": query},
            timeout=60
        )
        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def explain_symbol(repo_id: int, file_path: str, symbol_name: str = None, code_snippet: str = None) -> Dict[str, Any]:
        resp = requests.post(
            f"{BASE_URL}/chat/explain",
            json={"repo_id": repo_id, "file_path": file_path, "symbol_name": symbol_name, "code_snippet": code_snippet},
            timeout=60
        )
        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def get_chat_history(repo_id: int) -> List[Dict[str, Any]]:
        resp = requests.get(f"{BASE_URL}/chat/history/{repo_id}", timeout=10)
        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def get_architecture_graph(repo_id: int) -> Dict[str, Any]:
        resp = requests.get(f"{BASE_URL}/architecture/{repo_id}/graph", timeout=15)
        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def get_architecture_cycles(repo_id: int) -> Dict[str, Any]:
        resp = requests.get(f"{BASE_URL}/architecture/{repo_id}/cycles", timeout=15)
        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def get_api_call_flows(repo_id: int) -> Dict[str, Any]:
        resp = requests.get(f"{BASE_URL}/architecture/{repo_id}/call-flows", timeout=15)
        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def simulate_impact(repo_id: int, target_file: str, target_symbol: str = "") -> Dict[str, Any]:
        resp = requests.post(
            f"{BASE_URL}/impact/simulate",
            json={"repo_id": repo_id, "target_file": target_file, "target_symbol": target_symbol},
            timeout=20
        )
        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def generate_tests(repo_id: int, file_path: str, symbol_name: str, framework: str = "pytest") -> Dict[str, Any]:
        resp = requests.post(
            f"{BASE_URL}/tests/generate",
            json={"repo_id": repo_id, "file_path": file_path, "symbol_name": symbol_name, "framework": framework},
            timeout=30
        )
        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def get_tech_debt(repo_id: int) -> Dict[str, Any]:
        resp = requests.get(f"{BASE_URL}/tech-debt/{repo_id}", timeout=20)
        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def refactor_code(repo_id: int, file_path: str, symbol_name: str, issue_description: str = "") -> Dict[str, Any]:
        resp = requests.post(
            f"{BASE_URL}/tech-debt/refactor",
            json={
                "repo_id": repo_id,
                "file_path": file_path,
                "symbol_name": symbol_name,
                "issue_description": issue_description
            },
            timeout=45
        )
        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def get_security_audit(repo_id: int) -> Dict[str, Any]:
        resp = requests.get(f"{BASE_URL}/security/{repo_id}", timeout=20)
        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def get_onboarding_roadmap(repo_id: int) -> Dict[str, Any]:
        resp = requests.get(f"{BASE_URL}/onboarding/{repo_id}/roadmap", timeout=30)
        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def evaluate_architecture_decision(repo_id: int, proposed_change: str, affected_components: List[str] = None) -> Dict[str, Any]:
        resp = requests.post(
            f"{BASE_URL}/onboarding/architecture-decision",
            json={"repo_id": repo_id, "proposed_change": proposed_change, "affected_components": affected_components or []},
            timeout=30
        )
        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def review_pr(repo_id: int, diff_text: str, title: str = "PR Review") -> Dict[str, Any]:
        resp = requests.post(
            f"{BASE_URL}/onboarding/pr-review",
            json={"repo_id": repo_id, "diff_text": diff_text, "title": title},
            timeout=30
        )
        resp.raise_for_status()
        return resp.json()

api = RepoPilotAPI()
