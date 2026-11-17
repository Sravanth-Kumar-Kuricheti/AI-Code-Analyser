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
    st.title("📁 Code Explorer & AST Inspector")
    st.write("Browse source files, inspect AST symbols (functions, classes, endpoints), and request instant AI explanations.")

def _render_file_metrics(file_detail: dict):
    """Renders top summary metrics for the inspected file."""
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Language", file_detail.get("language", "text").upper())
    with m2:
        st.metric("Lines of Code", file_detail.get("lines_of_code", 0))
    with m3:
        st.metric("Cyclomatic Complexity", file_detail.get("cyclomatic_complexity", 1.0))
    with m4:
        st.metric("Maintainability Index", f"{file_detail.get('maintainability_index', 100.0)}/100")

def _render_code_tab(file_detail: dict):
    """Renders formatted source code with syntax highlighting."""
    st.code(
        file_detail.get("content", ""),
        language=file_detail.get("language", "text"),
        line_numbers=True
    )

def _handle_explain_symbol(repo_id: int, file_path: str, sym_name: str, key: str):
    """Executes AI symbol explanation request and displays response."""
    if st.button(f"💡 Explain '{sym_name}' with AI", key=key):
        with st.spinner("Generating deep technical explanation..."):
            try:
                res = api.explain_symbol(repo_id=repo_id, file_path=file_path, symbol_name=sym_name)
                st.markdown("### 🧠 AI Explanation")
                st.markdown(res.get("explanation", ""))
            except Exception as ex:
                st.error(f"Explanation failed: {ex}")

def _render_symbol_card(sym: dict, repo_id: int, lang: str):
    """Renders an individual AST symbol item with AI explanation button."""
    b_type = "badge-info" if sym["symbol_type"] == "function" else "badge-low" if sym["symbol_type"] == "class" else "badge-high"
    with st.expander(f"{sym['symbol_type'].upper()}: {sym['name']} (Lines {sym['line_start']}-{sym['line_end']})"):
        st.markdown(f'<span class="badge {b_type}">{sym["symbol_type"].upper()}</span>', unsafe_allow_html=True)
        if sym.get("signature"):
            st.code(sym["signature"], language=lang)
        if sym.get("docstring"):
            st.markdown(f"**Docstring:**\n> {sym['docstring']}")
        st.markdown(f"**Complexity Score**: `{sym.get('complexity', 1)}`")
        if sym.get("is_api_endpoint"):
            st.markdown(f"**API Route**: `{sym.get('http_method')} {sym.get('http_path')}`")
        _handle_explain_symbol(repo_id, sym.get("file_path", ""), sym["name"], f"expl_{sym['name']}_{sym['line_start']}")

def _render_symbols_tab(file_detail: dict, repo_id: int):
    """Renders list of extracted AST symbols."""
    symbols = file_detail.get("symbols", [])
    if not symbols:
        st.info("No functions, classes, or endpoints extracted from this file.")
        return
    st.write(f"Found **{len(symbols)}** structural symbols:")
    lang = file_detail.get("language", "python")
    for sym in symbols:
        _render_symbol_card(sym, repo_id, lang)

def _get_target_file_detail(repo_id: int) -> dict:
    """Prompts file selection and loads file content."""
    try:
        files = api.get_repo_files(repo_id)
        if not files:
            st.info("No files found in this repository.")
            return {}
        selected_file = st.selectbox("Select File", options=[f["path"] for f in files])
        return api.get_file_content(repo_id, selected_file)
    except Exception as e:
        st.error(f"Failed to load file: {e}")
        return {}

def show_code_explorer():
    """Main code explorer page entry point."""
    apply_custom_styles()
    _render_header()

    try:
        repos = api.list_repos()
    except Exception:
        repos = []

    if not repos:
        st.warning("No repositories found. Ingest a repository first.")
        return

    selected_repo_id = select_active_repo(repos, label="Target Repository")
    file_detail = _get_target_file_detail(selected_repo_id)
    if not file_detail:
        return

    _render_file_metrics(file_detail)
    tab_code, tab_symbols = st.tabs(["📝 Source Code Viewer", "🔍 Extracted AST Symbols"])
    with tab_code:
        _render_code_tab(file_detail)
    with tab_symbols:
        _render_symbols_tab(file_detail, selected_repo_id)

show_code_explorer()
