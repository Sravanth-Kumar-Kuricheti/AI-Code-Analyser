import streamlit as st
from typing import Dict, Any, List, Set

def _get_layer_color(label: str) -> str:
    """Returns color hex corresponding to architectural layer."""
    lbl = label.lower()
    if "test" in lbl:
        return "#312E81"
    if "api" in lbl or "route" in lbl:
        return "#065F46"
    if "service" in lbl:
        return "#1E3A8A"
    if "model" in lbl or "schema" in lbl:
        return "#701A75"
    return "#1E293B"

def _format_node_id(node_id: str) -> str:
    """Normalizes file path into a valid graphviz node identifier."""
    return node_id.replace("\\", "/").replace("/", "_").replace(".", "_")

def _build_dot_nodes(nodes: List[Dict[str, Any]]) -> List[str]:
    """Generates DOT node definitions with custom fill and LOC labels."""
    lines = []
    for n in nodes:
        d = n["data"]
        node_id = _format_node_id(d["id"])
        label = d["label"]
        fill = _get_layer_color(label)
        lines.append(f'  "{node_id}" [label="{label}\\n({d.get("loc", 0)} LOC)", fillcolor="{fill}"];')
    return lines

def _build_dot_edges(edges: List[Dict[str, Any]], allowed_ids: Set[str], max_edges: int = 80) -> List[str]:
    """Generates DOT edge definitions between visible nodes."""
    lines = []
    for e in edges:
        d = e["data"]
        src, tgt = d["source"], d["target"]
        if src in allowed_ids and tgt in allowed_ids:
            lines.append(f'  "{_format_node_id(src)}" -> "{_format_node_id(tgt)}";')
            if len(lines) >= max_edges:
                break
    return lines

def render_dependency_graph(graph_data: Dict[str, Any], max_nodes: int = 40):
    """Renders an architectural dependency graph using Graphviz DOT representation."""
    nodes = graph_data.get("nodes", [])
    edges = graph_data.get("edges", [])

    if not nodes:
        st.info("No dependency nodes available to render.")
        return

    sorted_nodes = sorted(nodes, key=lambda n: n["data"].get("centrality", 0), reverse=True)[:max_nodes]
    display_ids = {n["data"]["id"] for n in sorted_nodes}

    dot_header = [
        "digraph G {",
        "  rankdir=LR;",
        "  bgcolor=\"transparent\";",
        "  node [fontname=\"Helvetica\", shape=box, style=\"filled,rounded\", fontcolor=\"#FFFFFF\", color=\"#475569\", fillcolor=\"#1E293B\", penwidth=1.5];",
        "  edge [fontname=\"Helvetica\", color=\"#64748B\", fontcolor=\"#94A3B8\", arrowsize=0.8];"
    ]
    dot_body = _build_dot_nodes(sorted_nodes) + _build_dot_edges(edges, display_ids) + ["}"]
    st.graphviz_chart("\n".join(dot_header + dot_body), width="stretch")
