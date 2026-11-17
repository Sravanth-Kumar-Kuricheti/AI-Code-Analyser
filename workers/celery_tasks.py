from celery import Celery
from backend.config import settings

celery_app = Celery(
    "repopilot_workers",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

@celery_app.task(name="tasks.index_repository_async")
def index_repository_async(repo_id: int):
    """
    Background worker task to index a repository without blocking the web thread.
    """
    from backend.models.database import SessionLocal
    from backend.services.analysis_service import AnalysisService

    db = SessionLocal()
    try:
        result = AnalysisService.index_repository(repo_id, db)
        return result
    finally:
        db.close()
