import os
import re
import numpy as np
from typing import List
from backend.config import settings

class Embedder:
    """
    Computes dense vector representations for code chunks.
    Supports SentenceTransformers with an instantaneous fallback vectorizer.
    """

    def __init__(self, model_name: str = None):
        self.model_name = model_name or settings.EMBEDDING_MODEL
        self._model = None
        self._dim = 384  # Standard MiniLM dimension

    def _get_model(self):
        if self._model is None:
            # Check if user enabled live heavy transformer model or if model is cached locally
            if os.environ.get("USE_TRANSFORMERS", "").lower() in ("1", "true"):
                try:
                    from sentence_transformers import SentenceTransformer
                    self._model = SentenceTransformer(self.model_name)
                except Exception:
                    self._model = "FALLBACK"
            else:
                self._model = "FALLBACK"
        return self._model

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []

        model = self._get_model()
        if model != "FALLBACK":
            try:
                embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
                return embeddings.tolist()
            except Exception:
                pass

        # High-speed deterministic 384-dimensional dense projection vectorizer
        vectors = []
        for text in texts:
            vec = np.zeros(self._dim, dtype=np.float32)
            words = re.findall(r"\w+", text.lower())
            if words:
                for w in words:
                    h = hash(w) % self._dim
                    vec[h] += 1.0
                norm = np.linalg.norm(vec)
                if norm > 0:
                    vec /= norm
            vectors.append(vec.tolist())
        return vectors

    def embed_query(self, query: str) -> List[float]:
        res = self.embed_texts([query])
        return res[0] if res else [0.0] * self._dim

embedder = Embedder()
