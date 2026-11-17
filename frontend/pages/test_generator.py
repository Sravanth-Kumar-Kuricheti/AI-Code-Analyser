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
    st.title("🧪 AI Test Case & Scenario Generator")
    st.write("Generate production-ready test suites for selected functions and classes with mock fixtures, boundary edge cases, and missing scenarios.")

def _select_target_function(symbols: list) -> str:
    """Renders selectbox or input for function name."""
    function_names = [s["name"] for s in symbols if s["symbol_type"] in ("function", "method", "endpoint")]
    if function_names:
        return st.selectbox("Select Function / Method to Test", options=function_names)
    return st.text_input("Function Name", placeholder="e.g. calculate_score")

def _select_test_targets(repo_id: int) -> tuple[str, str, str]:
    """Renders file, symbol, and testing framework inputs."""
    try:
        files = api.get_repo_files(repo_id)
    except Exception:
        files = []

    selected_file = st.selectbox("Select Target File", options=[f["path"] for f in files])
    try:
        file_detail = api.get_file_content(repo_id, selected_file)
        symbols = file_detail.get("symbols", [])
    except Exception:
        symbols = []

    col1, col2 = st.columns([2, 1])
    with col1:
        target_fn = _select_target_function(symbols)
    with col2:
        framework = st.selectbox("Testing Framework", options=["pytest", "jest"])
    return selected_file, target_fn, framework

def _render_generated_suite(res: dict, target_fn: str, framework: str):
    """Renders the synthesized test code and coverage metrics."""
    st.markdown("---")
    st.subheader(f"✨ Generated {framework.upper()} Test Suite for `{target_fn}`")
    m1, m2 = st.columns(2)
    m1.metric("Estimated Test Coverage", f"{res.get('coverage_estimate_pct', 85)}%")
    m2.metric("Target Signature", res.get("signature", ""))
    st.code(res.get("generated_test_code", ""), language="python" if framework == "pytest" else "javascript")
    st.markdown("#### 🎯 Covered Test Scenarios & Edge Cases")
    for sc in res.get("scenarios_covered", []):
        st.markdown(f"- 🧪 {sc}")

def _handle_generate_tests(repo_id: int, file_path: str, target_fn: str, framework: str):
    """Invokes test generator API."""
    with st.spinner(f"Synthesizing {framework} tests with edge cases and mock assertions..."):
        try:
            res = api.generate_tests(repo_id=repo_id, file_path=file_path, symbol_name=target_fn, framework=framework)
            _render_generated_suite(res, target_fn, framework)
        except Exception as e:
            st.error(f"Test generation failed: {e}")

def show_test_generator_page():
    """Main test generator page entry point."""
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
    selected_file, target_fn, framework = _select_test_targets(selected_repo_id)

    if st.button("⚡ Generate Unit Test Suite", type="primary"):
        _handle_generate_tests(selected_repo_id, selected_file, target_fn, framework)

show_test_generator_page()
