import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from backend.models.database import SessionLocal
from backend.models.schemas import Repository
from ai_engine.retrieval.rag_engine import RAGEngine
from backend.api.architecture_routes import get_circular_dependencies, get_api_call_flows
from backend.api.impact_routes import simulate_change_impact
from backend.schemas.pydantic_models import ImpactRequest

def main():
    db = SessionLocal()
    try:
        repo = db.query(Repository).filter(Repository.name == "RepoPilot-AI").first()
        print(f"Repo found: {repo.name} | Health: {repo.health_score}% | Files: {repo.total_files}")

        retrieval = RAGEngine.retrieve_context(repo.id, "How does AST parsing extract functions and classes?")
        print(f"Retrieval citations found: {len(retrieval['citations'])}")
        for c in retrieval["citations"][:3]:
            print(f" - Citation: {c['citation']} (Symbol: {c['symbol']})")

        cycles = get_circular_dependencies(repo.id, db)
        print(f"Circular dependencies count: {cycles['cycle_count']}")

        flows = get_api_call_flows(repo.id, db)
        print(f"API Endpoint flows traced: {flows['endpoint_count']}")
        for fl in flows["flows"][:3]:
            print(f" - {fl['endpoint']} -> {fl['handler']}")

        impact = simulate_change_impact(
            ImpactRequest(repo_id=repo.id, target_file="code_engine/parser/ast_parser.py"),
            db
        )
        print(f"Impact blast radius of ast_parser.py: {impact['blast_radius_score']}")
        print(f" - Affected files ({len(impact['affected_files'])}): {impact['affected_files'][:5]}")
        print(f" - Affected endpoints: {len(impact['affected_endpoints'])}")
        print(f" - Affected tests: {impact['affected_tests']}")
    finally:
        db.close()

if __name__ == "__main__":
    main()
