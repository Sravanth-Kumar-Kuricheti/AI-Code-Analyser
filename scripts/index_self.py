import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.models.database import SessionLocal, init_db
from backend.models.schemas import Repository
from backend.services.repo_service import RepoService
from backend.services.analysis_service import AnalysisService

def main():
    init_db()
    db = SessionLocal()
    try:
        print("Linking local repository...")
        meta = RepoService.clone_or_link_repository(".", branch="main", custom_name="RepoPilot-AI")
        repo = db.query(Repository).filter(Repository.name == "RepoPilot-AI").first()
        if not repo:
            repo = Repository(
                name=meta["name"],
                full_name=meta["full_name"],
                url=meta["url"],
                local_path=meta["local_path"],
                default_branch=meta["default_branch"]
            )
            db.add(repo)
            db.commit()
            db.refresh(repo)

        print(f"Indexing repository ID {repo.id}: {repo.name}...")
        result = AnalysisService.index_repository(repo.id, db)
        print("Indexing completed!")
        print(f"- Total Files: {result['total_files']}")
        print(f"- Lines of Code: {result['total_lines']}")
        print(f"- Symbols Extracted: {result['symbols_extracted']}")
        print(f"- Health Score: {result['health_score']}%")
        print(f"- Primary Language: {result['primary_language']}")
        print(f"- Debt Hours: {result['debt_hours']}")
    finally:
        db.close()

if __name__ == "__main__":
    main()
