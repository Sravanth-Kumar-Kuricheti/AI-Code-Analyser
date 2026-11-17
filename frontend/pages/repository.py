import sys
from pathlib import Path

# Ensure project root is in sys.path
_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st
from frontend.components.styles import apply_custom_styles
from frontend.api_client import api

def _render_header():
    """Renders page title and description."""
    st.title("🔗 Connect & Manage Repositories")
    st.write("Ingest public or private GitHub repositories, or link an existing local project folder for instantaneous parsing and AST indexing.")

def _handle_connect_submit(url_input: str, branch_input: str, custom_name: str):
    """Executes repository connection and initial indexing."""
    if not url_input.strip():
        st.error("Please enter a valid GitHub URL or local directory path.")
        return
    with st.spinner("Cloning, parsing AST, building dependency graph, and embedding chunks..."):
        try:
            name_val = custom_name.strip() if custom_name else None
            result = api.connect_repo(url_or_path=url_input.strip(), branch=branch_input.strip() or "main", name=name_val)
            st.session_state["selected_repo_id"] = result["id"]
            st.success(f"Successfully ingested and indexed **{result['name']}**!")
            st.rerun()
        except Exception as e:
            st.error(f"Failed to connect repository: {e}")

def _render_connect_form():
    """Renders the ingest new repository form."""
    with st.expander("➕ Ingest New Repository", expanded=True):
        with st.form("connect_repo_form"):
            col1, col2 = st.columns([3, 1])
            with col1:
                url_input = st.text_input(
                    "GitHub Repository URL or Local Directory Path",
                    placeholder="https://github.com/tiangolo/fastapi or C:/Projects/my-app"
                )
            with col2:
                branch_input = st.text_input("Branch", value="main")
            custom_name = st.text_input("Custom Display Name (Optional)", placeholder="e.g. FastAPI Core")
            if st.form_submit_button("🚀 Ingest & Index Repository", type="primary"):
                _handle_connect_submit(url_input, branch_input, custom_name)

def _handle_reindex(repo_id: int):
    """Triggers re-indexing for an existing repository."""
    with st.spinner("Re-analyzing repository..."):
        try:
            api.reindex_repo(repo_id)
            st.session_state["selected_repo_id"] = repo_id
            st.success("Re-index completed!")
            st.rerun()
        except Exception as ex:
            st.error(f"Re-indexing failed: {ex}")

def _render_repo_item(r: dict):
    """Renders a single repository card."""
    with st.container():
        col_info, col_act = st.columns([4, 1])
        with col_info:
            st.markdown(f"### 📦 {r['name']}")
            st.markdown(f"**Path / URL**: `{r['url']}` | **Branch**: `{r['default_branch']}` | **Language**: `{r['primary_language']}`")
            st.markdown(f"**Files**: {r['total_files']} | **Lines of Code**: {r['total_lines']:,} | **Health**: `{r['health_score']}%`")
        with col_act:
            st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
            if st.button("🔄 Re-Index", key=f"reindex_{r['id']}", width="stretch"):
                _handle_reindex(r["id"])
        st.markdown("---")

def _render_connected_list():
    """Renders the list of registered repositories."""
    st.subheader("📚 Connected Repositories")
    try:
        repos = api.list_repos()
    except Exception as e:
        repos = []
        st.error(f"Error fetching repositories: {e}")

    if not repos:
        st.info("No repositories currently registered.")
        return

    for r in repos:
        _render_repo_item(r)

def show_repository_page():
    """Main repository management page."""
    apply_custom_styles()
    _render_header()
    _render_connect_form()
    st.markdown("---")
    _render_connected_list()

show_repository_page()
