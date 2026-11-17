import sys
from pathlib import Path

# Ensure project root is in sys.path
_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st
import pandas as pd
import altair as alt
from frontend.components.styles import apply_custom_styles, render_metric_card
from frontend.components.repo_selector import select_active_repo
from frontend.api_client import api

def _render_hero_banner():
    """Renders the top branding hero banner."""
    st.markdown("""
    <div class="hero-banner">
        <h1 style="margin: 0; color: #F8FAFC; font-size: 2.25rem; font-weight: 800;">
            🛰️ RepoPilot-AI <span style="font-size: 1rem; color: #38BDF8; font-weight: 600; vertical-align: middle; background: rgba(56, 189, 248, 0.1); padding: 4px 10px; border-radius: 9999px; border: 1px solid rgba(56, 189, 248, 0.3);">DEVELOPER INTELLIGENCE</span>
        </h1>
        <p style="margin: 0.75rem 0 0 0; color: #94A3B8; font-size: 1.05rem;">
            Deep repository understanding, architectural graph analysis, change impact simulation, and contextual code intelligence.
        </p>
    </div>
    """, unsafe_allow_html=True)

def _render_repo_status(current_repo: dict):
    """Renders the indexing status badge for the selected repo."""
    st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
    if current_repo.get("indexing_status") == "completed":
        st.markdown('<span class="badge badge-low">● INDEXED & READY</span>', unsafe_allow_html=True)
    else:
        st.markdown(f'<span class="badge badge-medium">● {current_repo.get("indexing_status", "PENDING").upper()}</span>', unsafe_allow_html=True)

def _get_security_summary(repo_id: int) -> tuple[int, str]:
    """Fetches high-level security count and alert color."""
    try:
        sec_data = api.get_security_audit(repo_id)
        crit = sec_data.get("critical_count", 0) + sec_data.get("high_count", 0)
        color = "#10B981" if crit == 0 else "#EF4444"
        return crit, color
    except Exception:
        return 0, "#10B981"

def _render_metrics_row(current_repo: dict):
    """Renders the high-level metrics cards row."""
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        score = current_repo.get("health_score", 100.0)
        color = "#10B981" if score >= 85 else "#F59E0B" if score >= 65 else "#EF4444"
        render_metric_card("Repository Health", f"{score}%", "Overall quality & security rating", color)
    with c2:
        render_metric_card("Files & Volume", f"{current_repo.get('total_files', 0):,}", f"{current_repo.get('total_lines', 0):,} Total Lines of Code")
    with c3:
        render_metric_card("Primary Stack", current_repo.get("primary_language", "Python"), f"Branch: {current_repo.get('default_branch', 'main')}")
    with c4:
        crit, sec_color = _get_security_summary(current_repo["id"])
        render_metric_card("Security Alerts", str(crit), "Critical / High findings", sec_color)

def _render_language_chart(repo_id: int):
    """Renders the language breakdown bar chart."""
    st.subheader("📊 Codebase File & Language Distribution")
    try:
        files_data = api.get_repo_files(repo_id)
        if not files_data:
            st.info("No files parsed yet.")
            return
        df = pd.DataFrame(files_data)
        lang_summary = df.groupby("language")["lines_of_code"].sum().reset_index()
        chart = alt.Chart(lang_summary).mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6).encode(
            x=alt.X("language:N", title="Language", sort="-y"),
            y=alt.Y("lines_of_code:Q", title="Lines of Code"),
            color=alt.Color("language:N", scale=alt.Scale(scheme="tealblues")),
            tooltip=["language", "lines_of_code"]
        ).properties(height=260)
        st.altair_chart(chart, width="stretch")
    except Exception as e:
        st.error(f"Failed to fetch files breakdown: {e}")

def _render_quick_actions():
    """Renders shortcut navigation buttons to intelligence modules."""
    st.subheader("⚡ Quick Intelligence Actions")
    st.write("Navigate directly into deep codebase inspection:")
    if st.button("💬 Ask Codebase Q&A", width="stretch"):
        st.switch_page("pages/ai_chat.py")
    if st.button("🏛️ View Architecture Map", width="stretch"):
        st.switch_page("pages/architecture.py")
    if st.button("⚡ Simulate Change Impact", width="stretch"):
        st.switch_page("pages/change_impact.py")
    if st.button("🛡️ Audit Security & Secrets", width="stretch"):
        st.switch_page("pages/security.py")
    if st.button("🚀 Developer Onboarding Guide", width="stretch"):
        st.switch_page("pages/onboarding.py")

def _load_repositories() -> list:
    """Safely retrieves connected repositories."""
    try:
        return api.list_repos()
    except Exception as e:
        st.warning(f"Backend API is initializing ({e}).")
        return []

def show_dashboard():
    """Main dashboard page entry point."""
    apply_custom_styles()
    _render_hero_banner()
    
    repos = _load_repositories()
    if not repos:
        st.info("No repositories connected yet. Navigate to Connect Repository to ingest your first codebase.")
        if st.button("🔗 Connect a Repository Now", type="primary"):
            st.switch_page("pages/repository.py")
        return

    col_sel, col_stat = st.columns([3, 1])
    with col_sel:
        selected_id = select_active_repo(repos, label="Active Repository")
    current_repo = next((r for r in repos if r["id"] == selected_id), repos[0])
    
    with col_stat:
        _render_repo_status(current_repo)

    st.markdown("---")
    _render_metrics_row(current_repo)
    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

    col_left, col_right = st.columns([2, 1])
    with col_left:
        _render_language_chart(current_repo["id"])
    with col_right:
        _render_quick_actions()

show_dashboard()
