import sys
from pathlib import Path

# Ensure project root is in sys.path
_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st
from frontend.components.styles import apply_custom_styles, render_metric_card
from frontend.components.repo_selector import select_active_repo
from frontend.api_client import api

def _render_header():
    """Renders page title and description."""
    st.title("⚡ Change Impact Analyzer & Blast Radius Simulator")
    st.write("Before modifying a file, function, or class, simulate which downstream modules, API routes, and test suites will be affected.")

def _render_impact_cards(impact: dict):
    """Renders top impact metric cards."""
    score = impact.get("blast_radius_score", "LOW")
    color = impact.get("badge_color", "#10B981")
    m1, m2, m3 = st.columns(3)
    with m1:
        render_metric_card("Blast Radius Risk", score, "Propagation severity rating", color)
    with m2:
        render_metric_card("Affected Modules", str(impact.get("affected_files_count", 0)), "Direct & cascading files")
    with m3:
        render_metric_card("Impacted Endpoints", str(len(impact.get("affected_endpoints", []))), "Public HTTP routes affected")

def _render_affected_files(affected_files: list):
    """Renders list of affected files."""
    st.markdown("#### 📂 Affected Files")
    if affected_files:
        for f in affected_files:
            st.markdown(f"- 📄 `{f}`")
    else:
        st.write("No other files import this module directly.")

def _render_affected_endpoints(affected_endpoints: list):
    """Renders list of impacted API endpoints."""
    st.markdown("#### 🌐 Affected API Endpoints")
    if affected_endpoints:
        for ep in affected_endpoints:
            st.markdown(f"- 📍 `{ep.get('method')} {ep.get('path')}` (`{ep.get('endpoint')}` in `{ep.get('file')}`)")
    else:
        st.write("No external API endpoints depend on this file.")

def _render_tests_and_mitigations(impact: dict):
    """Renders test suites and mitigation actions."""
    st.markdown("#### 🧪 Test Suites Requiring Execution")
    tests = impact.get("affected_tests", [])
    if tests:
        for t in tests:
            st.markdown(f"- ✅ `{t}`")
    else:
        st.warning("⚠️ No direct test files detected for this module. Recommended: Write a unit test before making structural changes.")

    st.markdown("#### 🛠️ Recommended Mitigation Actions")
    for act in impact.get("mitigation_actions", []):
        st.markdown(f"- 💡 {act}")

def _render_impact_report(impact: dict):
    """Renders full simulation report."""
    st.markdown("---")
    st.subheader("🎯 Blast Radius Simulation Report")
    _render_impact_cards(impact)
    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
    st.info(f"📋 **Risk Assessment Summary:**\n{impact.get('risk_assessment')}")

    col_aff, col_ep = st.columns(2)
    with col_aff:
        _render_affected_files(impact.get("affected_files", []))
    with col_ep:
        _render_affected_endpoints(impact.get("affected_endpoints", []))

    _render_tests_and_mitigations(impact)

def _execute_simulation(repo_id: int, target_file: str, target_symbol: str):
    """Executes blast radius calculation and displays report."""
    with st.spinner("Calculating dependency propagation and downstream blast radius..."):
        try:
            impact = api.simulate_impact(repo_id, target_file, target_symbol)
            _render_impact_report(impact)
        except Exception as e:
            st.error(f"Simulation failed: {e}")

def _select_target_inputs(files: list) -> tuple[str, str]:
    """Renders target file and symbol selection inputs."""
    c_file, c_sym = st.columns([2, 1])
    with c_file:
        target_file = st.selectbox("Target File to Modify", options=[f["path"] for f in files])
    with c_sym:
        target_symbol = st.text_input("Specific Function / Class (Optional)", placeholder="e.g. parse_file")
    return target_file, target_symbol

def show_change_impact_page():
    """Main change impact page entry point."""
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
    try:
        files = api.get_repo_files(selected_repo_id)
    except Exception as e:
        st.error(f"Failed to fetch files: {e}")
        return

    if not files:
        st.info("No files available.")
        return

    target_file, target_symbol = _select_target_inputs(files)
    if st.button("🚀 Run Blast Radius Simulation", type="primary"):
        _execute_simulation(selected_repo_id, target_file, target_symbol)

show_change_impact_page()
