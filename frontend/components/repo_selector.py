import streamlit as st
from typing import List, Dict, Any, Optional

def select_active_repo(repos: List[Dict[str, Any]], label: str = "Active Repository") -> Optional[int]:
    """
    Renders a unified repository selector that persists the user's selected
    repository ID in st.session_state across all multi-page views.
    """
    if not repos:
        return None

    repo_ids = [r["id"] for r in repos]
    saved_id = st.session_state.get("selected_repo_id")
    
    default_index = 0
    if saved_id in repo_ids:
        default_index = repo_ids.index(saved_id)

    def format_repo(rid: int) -> str:
        for r in repos:
            if r["id"] == rid:
                return f"{r['name']} ({r.get('primary_language', 'Unknown')}) - {r.get('total_files', 0)} files"
        return str(rid)

    selected_id = st.selectbox(
        label,
        options=repo_ids,
        index=default_index,
        format_func=format_repo,
        key=f"repo_selector_{label.replace(' ', '_').lower()}"
    )

    st.session_state["selected_repo_id"] = selected_id
    return selected_id
