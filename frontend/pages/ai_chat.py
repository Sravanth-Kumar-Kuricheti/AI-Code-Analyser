import sys
from pathlib import Path

# Ensure project root is in sys.path
_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st
from frontend.components.styles import apply_custom_styles
from frontend.components.repo_selector import select_active_repo
from frontend.api_client import api

def _render_header():
    """Renders page title and description."""
    st.title("💬 AI Codebase Q&A & Semantic Chat")
    st.write("Ask natural language questions across the entire repository. Every answer is grounded in AST embeddings with exact file citations.")

def _render_quick_inquiries() -> str:
    """Renders preset quick inquiry buttons and returns chosen query if clicked."""
    st.write("💡 **Quick Inquiries:**")
    qc1, qc2, qc3 = st.columns(3)
    if qc1.button("🏛️ Explain overall architecture"):
        return "What is the architectural pattern of this repository and how do layers communicate?"
    if qc2.button("🔗 Find all API endpoints"):
        return "List all API routes and endpoints defined in this project with their HTTP methods."
    if qc3.button("⚠️ Locate error handling & fallbacks"):
        return "Where are exceptions, errors, and fallbacks handled in this codebase?"
    return ""

def _render_citations(citations: list):
    """Renders referenced code citation pills and expandable preview snippets."""
    if not citations:
        return
    st.markdown("**Referenced Code Citations:**")
    for c in citations:
        st.markdown(f'<span class="citation-pill">📄 {c["citation"]}</span>', unsafe_allow_html=True)
        with st.expander(f"View snippet: {c['file']} (Lines {c['start_line']}-{c['end_line']})"):
            st.code(c.get("preview", ""))

def _render_message_item(msg: dict):
    """Renders a single chat history bubble."""
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        _render_citations(msg.get("citations", []))

def _process_chat_query(repo_id: int, user_prompt: str):
    """Sends chat prompt to RAG retrieval pipeline and updates message history."""
    st.session_state.messages.append({"role": "user", "content": user_prompt, "citations": []})
    with st.chat_message("user"):
        st.markdown(user_prompt)

    with st.chat_message("assistant"):
        with st.spinner("Retrieving semantic code chunks and formulating cited analysis..."):
            try:
                res = api.ask_chat(repo_id, user_prompt)
                answer = res.get("answer", "")
                citations = res.get("citations", [])
                st.markdown(answer)
                _render_citations(citations)
                st.session_state.messages.append({"role": "assistant", "content": answer, "citations": citations})
            except Exception as e:
                st.error(f"Chat request failed: {e}")

def show_chat_page():
    """Main codebase Q&A chat page."""
    apply_custom_styles()
    _render_header()

    try:
        repos = api.list_repos()
    except Exception:
        repos = []

    if not repos:
        st.warning("No repositories found. Connect a repository first.")
        return

    selected_repo_id = select_active_repo(repos, label="Target Repository")
    preset_query = _render_quick_inquiries()

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        _render_message_item(msg)

    prompt = st.chat_input("Ask any question about this codebase...") or preset_query
    if prompt:
        _process_chat_query(selected_repo_id, prompt)

show_chat_page()
