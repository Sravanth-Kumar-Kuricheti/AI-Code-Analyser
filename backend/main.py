from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.config import settings
from backend.models.database import init_db
from backend.api import (
    repo_routes, chat_routes, architecture_routes,
    impact_routes, test_gen_routes, tech_debt_routes,
    security_routes, onboarding_routes
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB tables on application startup
    init_db()
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="RepoPilot-AI: High-Precision Developer Intelligence & Codebase RAG Platform",
    lifespan=lifespan
)

# Enable CORS for Streamlit and external clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API Routers
app.include_router(repo_routes.router, prefix=settings.API_PREFIX)
app.include_router(chat_routes.router, prefix=settings.API_PREFIX)
app.include_router(architecture_routes.router, prefix=settings.API_PREFIX)
app.include_router(impact_routes.router, prefix=settings.API_PREFIX)
app.include_router(test_gen_routes.router, prefix=settings.API_PREFIX)
app.include_router(tech_debt_routes.router, prefix=settings.API_PREFIX)
app.include_router(security_routes.router, prefix=settings.API_PREFIX)
app.include_router(onboarding_routes.router, prefix=settings.API_PREFIX)

@app.get("/")
def root():
    return {
        "status": "online",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs_url": "/docs"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host=settings.BACKEND_HOST, port=settings.BACKEND_PORT, reload=True)
