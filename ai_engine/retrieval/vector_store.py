import os
import atexit
from pathlib import Path
from typing import List, Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from backend.config import settings

class VectorStore:
    """
    Qdrant vector database manager for storing and retrieving code embeddings.
    Supports persistent local disk storage, remote Qdrant clusters, or in-memory fallback.
    Gracefully handles concurrent lock contention when a background server is running.
    """

    def __init__(self):
        storage_dir = Path(settings.CACHE_DIR) / "qdrant_db"
        storage_dir.mkdir(parents=True, exist_ok=True)
        self.client = None
        
        # 1. Try remote Qdrant cluster if configured
        if not settings.QDRANT_IN_MEMORY and settings.QDRANT_HOST != "localhost":
            try:
                self.client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT, timeout=5)
            except Exception:
                self.client = None

        # 2. Try local persistent disk storage with graceful lock-contention fallback
        if self.client is None:
            try:
                self.client = QdrantClient(path=str(storage_dir))
            except (RuntimeError, Exception):
                # If disk storage is locked by another running process (e.g. uvicorn server or tests)
                self.client = QdrantClient(":memory:")

    def _collection_name(self, repo_id: int) -> str:
        return f"repo_{repo_id}"

    def ensure_collection(self, repo_id: int, vector_size: int = 384):
        col_name = self._collection_name(repo_id)
        try:
            collections = self.client.get_collections().collections
            exists = any(c.name == col_name for c in collections)
        except Exception:
            exists = False

        if not exists:
            self.client.create_collection(
                collection_name=col_name,
                vectors_config=qmodels.VectorParams(
                    size=vector_size,
                    distance=qmodels.Distance.COSINE
                )
            )

    def upsert_chunks(self, repo_id: int, chunks: List[Dict[str, Any]], vectors: List[List[float]]):
        if not chunks or not vectors:
            return
        self.ensure_collection(repo_id, vector_size=len(vectors[0]))
        col_name = self._collection_name(repo_id)

        points = []
        for idx, (chunk, vec) in enumerate(zip(chunks, vectors)):
            points.append(
                qmodels.PointStruct(
                    id=idx + 1,
                    vector=vec,
                    payload=chunk
                )
            )

        batch_size = 100
        for i in range(0, len(points), batch_size):
            self.client.upsert(
                collection_name=col_name,
                points=points[i:i + batch_size]
            )

    def search(self, repo_id: int, query_vector: List[float], limit: int = 5) -> List[Dict[str, Any]]:
        col_name = self._collection_name(repo_id)
        try:
            if hasattr(self.client, "query_points"):
                response = self.client.query_points(
                    collection_name=col_name,
                    query=query_vector,
                    limit=limit
                )
                points = getattr(response, "points", response)
                return [
                    {
                        "score": hit.score,
                        "payload": hit.payload
                    }
                    for hit in points
                ]
            else:
                results = self.client.search(
                    collection_name=col_name,
                    query_vector=query_vector,
                    limit=limit
                )
                return [
                    {
                        "score": hit.score,
                        "payload": hit.payload
                    }
                    for hit in results
                ]
        except Exception:
            return []

    def delete_collection(self, repo_id: int):
        col_name = self._collection_name(repo_id)
        try:
            self.client.delete_collection(col_name)
        except Exception:
            pass

    def close(self):
        try:
            if self.client:
                self.client.close()
        except Exception:
            pass

vector_store = VectorStore()

# Graceful cleanup at interpreter exit
def _graceful_exit():
    try:
        vector_store.close()
    except Exception:
        pass

atexit.register(_graceful_exit)
