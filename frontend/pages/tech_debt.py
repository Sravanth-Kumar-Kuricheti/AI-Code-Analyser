import sys
from pathlib import Path

# Ensure project root is in sys.path
_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st
import pandas as pd
from frontend.components.styles import apply_custom_styles, render_metric_card
from frontend.components.repo_selector import select_active_repo
from frontend.api_client import api

def _render_header():
    """Renders page title and description."""
    st.title("📉 Technical Debt & Code Smell Detector")
    st.write("Inspect maintainability grades, remediation effort, oversized functions, cyclomatic complexity spikes, and generate AI refactoring plans powered by Groq.")

def _render_debt_metrics(report: dict):
    """Renders top summary metrics cards."""
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        grade = report.get("grade", "A")
        color = report.get("badge_color", "#10B981")
        render_metric_card("Maintainability Grade", f"Grade {grade}", "Repository health rating", color)
    with c2:
        hours = report.get("total_debt_hours", 0)
        h_color = "#10B981" if hours < 5 else "#F59E0B" if hours < 20 else "#EF4444"
        render_metric_card("Remediation Hours", f"{hours} hrs", "Estimated debt payoff effort", h_color)
    with c3:
        avg_comp = report.get("average_cyclomatic_complexity", 1.0)
        render_metric_card("Avg Complexity", str(avg_comp), "Cyclomatic complexity per fn")
    with c4:
        smells = report.get("total_issues_count", 0)
        render_metric_card("Total Smells", str(smells), "Detected maintenance risks")

def _handle_ai_refactor(repo_id: int, file_path: str, sym_name: str, desc: str):
    """Executes AI refactoring via Groq API and renders the result."""
    with st.spinner("Engaging Groq Llama-3.3 to refactor routine according to Clean Code principles..."):
        try:
            res = api.refactor_code(repo_id, file_path, sym_name, desc)
            st.markdown("### 🛠️ AI-Refactored Clean Code Solution")
            st.markdown(res.get("refactored_advice", ""))
        except Exception as ex:
            st.error(f"AI Refactoring failed: {ex}")

def _render_oversized_tab(report: dict, repo_id: int):
    """Renders oversized functions tab with AI refactoring actions."""
    long_fns = report.get("long_functions", [])
    if not long_fns:
        st.success("✅ Clean Modular Code: Zero functions exceed the 50 lines-of-code threshold!")
        return

    st.write(f"Detected **{len(long_fns)}** oversized functions (>50 LOC):")
    df_long = pd.DataFrame(long_fns)
    st.dataframe(df_long[["name", "file", "lines", "start", "end"]], width="stretch")
    
    st.markdown("#### ⚡ AI Refactor Oversized Function")
    fn_options = [f"{item['file']}::{item['name']}" for item in long_fns]
    selected_target = st.selectbox("Select Routine to Refactor", options=fn_options, key="sel_long_fn")
    
    if st.button("🤖 AI Refactor with Groq (Llama-3.3)", key="btn_refactor_long", type="primary"):
        chosen = next((x for x in long_fns if f"{x['file']}::{x['name']}" == selected_target), long_fns[0])
        _handle_ai_refactor(repo_id, chosen["file"], chosen["name"], f"Function length is {chosen['lines']} LOC (>50 threshold)")

def _render_complexity_tab(report: dict, repo_id: int):
    """Renders high-complexity methods tab with AI refactoring actions."""
    comp_methods = report.get("complex_methods", [])
    if not comp_methods:
        st.success("✅ Low Cyclomatic Risk: All methods maintain simple branch structures (CC <= 8)!")
        return

    st.write(f"Detected **{len(comp_methods)}** methods with high branching density (>8 CC):")
    df_comp = pd.DataFrame(comp_methods)
    st.dataframe(df_comp[["name", "file", "complexity", "start"]], width="stretch")

    st.markdown("#### ⚡ AI Refactor High-Complexity Method")
    method_options = [f"{item['file']}::{item['name']}" for item in comp_methods]
    selected_target = st.selectbox("Select Routine to Decompose", options=method_options, key="sel_comp_fn")

    if st.button("🤖 AI Decompose with Groq (Llama-3.3)", key="btn_refactor_comp", type="primary"):
        chosen = next((x for x in comp_methods if f"{x['file']}::{x['name']}" == selected_target), comp_methods[0])
        _handle_ai_refactor(repo_id, chosen["file"], chosen["name"], f"Cyclomatic complexity is {chosen['complexity']} (>8 threshold)")

def _render_recommendations_tab(report: dict):
    """Renders actionable recommendations and detected code smell details."""
    st.subheader("🛠️ Actionable Maintainability Recommendations")
    for rec in report.get("recommendations", []):
        st.markdown(f"- 📌 {rec}")

    st.markdown("#### Detected Code Smell Details")
    issues = report.get("issues", [])
    if issues:
        df_issues = pd.DataFrame(issues)
        cols = [c for c in ["category", "severity", "file", "line", "description", "effort_hours"] if c in df_issues.columns]
        st.dataframe(df_issues[cols], width="stretch")
    else:
        st.info("No code smells recorded in this repository.")

def show_tech_debt_page():
    """Main technical debt detector page."""
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
        report = api.get_tech_debt(selected_repo_id)
    except Exception as e:
        st.error(f"Failed to fetch technical debt metrics: {e}")
        return

    _render_debt_metrics(report)
    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

    tab_long, tab_comp, tab_recom = st.tabs([
        "📏 Oversized Functions (>50 LOC)",
        "🧠 High Complexity Methods (>8)",
        "💡 Refactoring Recommendations"
    ])
    with tab_long:
        _render_oversized_tab(report, selected_repo_id)
    with tab_comp:
        _render_complexity_tab(report, selected_repo_id)
    with tab_recom:
        _render_recommendations_tab(report)

show_tech_debt_page()
