import sys
from pathlib import Path

# Ensure project root is in sys.path
_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st
from frontend.components.styles import apply_custom_styles
from frontend.components.repo_selector import select_active_repo
from frontend.components.graph_view import render_dependency_graph
from frontend.api_client import api

def _render_header():
    """Renders page title and description."""
    st.title("🏛️ Interactive Codebase Architecture Mapper")
    st.write("Visualize module dependencies, identify cyclical anti-patterns, and trace end-to-end API request lifecycles.")

def _render_graph_tab(repo_id: int):
    """Renders visual dependency graph tab."""
    st.subheader("Module & File Dependency Graph")
    st.caption("Nodes represent files sized by lines of code; arrows represent import dependencies.")
    try:
        graph_data = api.get_architecture_graph(repo_id)
        c1, c2 = st.columns(2)
        c1.metric("Total Modules (Nodes)", graph_data.get("total_nodes", 0))
        c2.metric("Total Dependencies (Edges)", graph_data.get("total_edges", 0))
        render_dependency_graph(graph_data.get("graph_data", {}))
    except Exception as e:
        st.error(f"Failed to load architecture graph: {e}")

def _render_cycles_tab(repo_id: int):
    """Renders circular dependency detection tab."""
    st.subheader("Cyclic Dependency Analysis")
    try:
        cycle_data = api.get_architecture_cycles(repo_id)
        cycles = cycle_data.get("cycles", [])
        if not cycle_data.get("has_circular_dependencies") or not cycles:
            st.success("✅ Clean Architectural Hierarchy: Zero circular dependencies detected!")
            return
        st.warning(f"⚠️ Detected **{len(cycles)}** circular import loops that risk runtime import deadlocks.")
        for c in cycles:
            with st.expander(f"Cycle #{c['cycle_id']} ({c['length']} hops): {c['path_description']}"):
                st.markdown(f"**Severity**: `{c['severity']}`")
                st.markdown(f"**Cycle Loop**: `{c['path_description']}`")
                st.info(f"💡 **Remediation Advice**:\n{c['remediation']}")
    except Exception as e:
        st.error(f"Failed to analyze circular dependencies: {e}")

def _render_flow_services(services: list):
    """Renders services list column."""
    st.markdown("**Services Invoked:**")
    if services:
        for s in services:
            st.markdown(f"- ⚙️ `{s}`")
    else:
        st.caption("No dedicated service layer modules detected.")

def _render_flow_calls(downstream_calls: list):
    """Renders downstream sub-calls column."""
    st.markdown("**Downstream Calls:**")
    if downstream_calls:
        for dc in downstream_calls:
            st.markdown(f"- 📞 `{dc}`")
    else:
        st.caption("No direct downstream sub-calls traced.")

def _render_flow_card(fl: dict):
    """Renders a single endpoint flow card."""
    with st.container():
        st.markdown(f"### 📍 `{fl['endpoint']}`")
        st.markdown(f"**Handler**: `{fl['handler']}` in `{fl['file']}` (Line {fl['line']})")
        col1, col2 = st.columns(2)
        with col1:
            _render_flow_services(fl.get("services", []))
        with col2:
            _render_flow_calls(fl.get("downstream_calls", []))
        st.markdown("---")

def _render_flow_tab(repo_id: int):
    """Renders the API request flow tracer tab."""
    st.subheader("End-to-End API Request Flow Tracer")
    st.caption("Traces how incoming HTTP requests flow from routes to services and models.")
    try:
        flow_data = api.get_api_call_flows(repo_id)
        flows = flow_data.get("flows", [])
        if not flows:
            st.info("No API endpoints or routes detected in this repository.")
            return
        st.write(f"Traced **{len(flows)}** API endpoints across the codebase:")
        for fl in flows:
            _render_flow_card(fl)
    except Exception as e:
        st.error(f"Failed to trace API call flows: {e}")

def show_architecture_page():
    """Main architecture mapper entry point."""
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
    tab_graph, tab_cycles, tab_flow = st.tabs([
        "🌐 Visual Dependency Graph",
        "🔄 Circular Dependency Detector",
        "🌊 API Request Flow Tracer"
    ])
    with tab_graph:
        _render_graph_tab(selected_repo_id)
    with tab_cycles:
        _render_cycles_tab(selected_repo_id)
    with tab_flow:
        _render_flow_tab(selected_repo_id)

show_architecture_page()
