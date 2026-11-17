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
    st.title("🚀 Smart Developer Onboarding & Architecture Advisor")
    st.write("Accelerate ramp-up time for engineers joining unfamiliar projects with a sequenced reading path, Day-1 checklist, and an architecture decision assistant.")

def _render_checklist(checklist: list):
    """Renders Day-1 onboarding checklist items."""
    st.subheader("🏁 Day-1 Engineering Ramp-Up Checklist")
    for chk in checklist:
        st.markdown(f"- [ ] {chk}")

def _render_entry_and_modules(entry_points: list, core_modules: list):
    """Renders entrypoints and core domain modules."""
    col_ep, col_mod = st.columns(2)
    with col_ep:
        st.markdown("#### 🚪 Primary System Entrypoints")
        for ep in entry_points:
            st.markdown(f"- 🔑 `{ep}`")
    with col_mod:
        st.markdown("#### 🧱 Core Domain Modules")
        for m in core_modules:
            st.markdown(f"- 📦 `{m}`")

def _render_roadmap_tab(repo_id: int):
    """Renders the developer onboarding roadmap tab."""
    with st.spinner("Compiling developer onboarding roadmap and file reading paths..."):
        try:
            roadmap = api.get_onboarding_roadmap(repo_id)
            _render_checklist(roadmap.get("day_one_checklist", []))
            st.markdown("---")
            _render_entry_and_modules(roadmap.get("entry_points", []), roadmap.get("core_modules", []))
            st.markdown("---")
            st.subheader("📖 Architectural Narrative & Reading Sequence")
            st.markdown(roadmap.get("roadmap_narrative", ""))
        except Exception as e:
            st.error(f"Failed to generate onboarding roadmap: {e}")

def _handle_evaluate_proposal(repo_id: int, proposal: str):
    """Handles architectural decision evaluation request."""
    if not proposal.strip():
        st.error("Please enter a proposed change description.")
        return
    with st.spinner("Evaluating compatibility against current repository boundaries..."):
        try:
            res = api.evaluate_architecture_decision(repo_id=repo_id, proposed_change=proposal.strip())
            st.markdown("---")
            st.subheader("📋 Architectural Compatibility Analysis")
            st.markdown(res.get("evaluation", ""))
        except Exception as ex:
            st.error(f"Decision evaluation failed: {ex}")

def _render_decision_tab(repo_id: int):
    """Renders the architecture decision assistant tab."""
    st.subheader("Architecture Decision Assistant")
    st.write("Propose a structural change and receive evidence-backed compatibility guidance.")
    proposal = st.text_area(
        "Proposed Architectural Change",
        placeholder="e.g. Split database models into a shared microservice package and introduce event streaming via Kafka.",
        height=120
    )
    if st.button("⚖️ Evaluate Architectural Proposal", type="primary"):
        _handle_evaluate_proposal(repo_id, proposal)

def show_onboarding_page():
    """Main onboarding page entry point."""
    apply_custom_styles()
    _render_header()

    try:
        repos = api.list_repos()
    except Exception:
        repos = []

    if not repos:
        st.warning("No repositories found. Connect a repository first.")
        return

    selected_repo_id = select_active_repo(repos, label="Repository Context")
    tab_guide, tab_decisions = st.tabs([
        "🧭 Personalized Onboarding Roadmap",
        "⚖️ Architecture Decision Assistant"
    ])
    with tab_guide:
        _render_roadmap_tab(selected_repo_id)
    with tab_decisions:
        _render_decision_tab(selected_repo_id)

show_onboarding_page()
