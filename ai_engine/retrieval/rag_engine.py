from typing import List, Dict, Any, Tuple
from ai_engine.embeddings.embedder import embedder
from ai_engine.retrieval.vector_store import vector_store

def _calculate_keyword_score(payload: Dict[str, Any], terms: List[str]) -> float:
    """Calculates keyword match score across symbol name, file path, and content."""
    content = payload.get("content", "").lower()
    symbol = payload.get("symbol_name", "").lower()
    file_p = payload.get("file_path", "").lower()
    keyword_score = 0.0
    for t in terms:
        if t in symbol:
            keyword_score += 0.3
        elif t in file_p:
            keyword_score += 0.2
        elif t in content:
            keyword_score += 0.1
    return keyword_score

def _rank_search_hits(search_hits: List[Dict[str, Any]], query: str, top_k: int) -> List[Dict[str, Any]]:
    """Ranks semantic search hits with exact keyword boosting."""
    terms = [t.lower() for t in query.split() if len(t) > 2]
    scored = []
    for hit in search_hits:
        payload = hit.get("payload", {})
        total_score = hit.get("score", 0.0) + _calculate_keyword_score(payload, terms)
        scored.append((total_score, payload))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [item[1] for item in scored[:top_k]]

def _build_citation(chunk: Dict[str, Any]) -> Tuple[Dict[str, Any], str]:
    """Builds a structured citation dictionary and formatted Markdown context block."""
    file_path = chunk.get("file_path", "")
    s_line = chunk.get("start_line", 1)
    e_line = chunk.get("end_line", 1)
    sym = chunk.get("symbol_name", "")
    content = chunk.get("content", "")
    citation_str = f"[{file_path}:{s_line}-{e_line}]"
    citation_data = {
        "file": file_path,
        "start_line": s_line,
        "end_line": e_line,
        "symbol": sym,
        "citation": citation_str,
        "preview": content[:150]
    }
    block_text = (
        f"--- BEGIN SNIPPET: {citation_str} ---\n"
        f"File: {file_path}\n"
        f"Lines: {s_line} to {e_line}\n"
        f"Symbol: {sym}\n"
        f"Code:\n{content}\n"
        f"--- END SNIPPET ---"
    )
    return citation_data, block_text

class RAGEngine:
    """Hybrid semantic code search and context retrieval engine."""

    @classmethod
    def retrieve_context(cls, repo_id: int, query: str, top_k: int = 5) -> Dict[str, Any]:
        """Retrieves and formats semantic context chunks for RAG reasoning."""
        query_vec = embedder.embed_query(query)
        search_hits = vector_store.search(repo_id, query_vec, limit=top_k * 2)
        top_chunks = _rank_search_hits(search_hits, query, top_k)

        citations = []
        blocks = []
        for c in top_chunks:
            cit, blk = _build_citation(c)
            citations.append(cit)
            blocks.append(blk)

        return {
            "context_text": "\n\n".join(blocks),
            "citations": citations,
            "raw_chunks": top_chunks
        }
