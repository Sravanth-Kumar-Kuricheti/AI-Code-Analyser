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
    st.title("🛡️ Security, Secret & Compliance Scanner")
    st.write("Scan the repository for leaked API credentials, Bandit Python AST security vulnerabilities, vulnerable dependencies, and license obligations.")

def _render_severity_metrics(sec: dict):
    """Renders high-level vulnerability metrics."""
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_metric_card("Critical Findings", str(sec.get("critical_count", 0)), "Immediate remediation required", "#EF4444")
    with c2:
        render_metric_card("High Findings", str(sec.get("high_count", 0)), "Severe security risks", "#FB923C")
    with c3:
        render_metric_card("Medium / Low", str(sec.get("medium_count", 0) + sec.get("low_count", 0)), "Hardening opportunities", "#FBBF24")
    with c4:
        lic = sec.get("license", {})
        lic_color = "#10B981" if lic.get("is_permissive") else "#EF4444"
        render_metric_card("License Status", lic.get("spdx_id", "MIT"), lic.get("category", "Permissive"), lic_color)

def _render_finding_item(f: dict):
    """Renders an individual vulnerability finding expander."""
    badge = "badge-critical" if f["severity"] == "CRITICAL" else "badge-high" if f["severity"] == "HIGH" else "badge-medium"
    with st.expander(f"[{f['severity']}] {f['rule_id']}: {f['description']} ({f['file_path']}:{f['line_number']})"):
        st.markdown(f'<span class="badge {badge}">{f["severity"]}</span> <span class="badge badge-info">{f["category"]}</span>', unsafe_allow_html=True)
        st.markdown(f"**Location**: `{f['file_path']}` (Line {f['line_number']})")
        if f.get("code_snippet"):
            st.code(f["code_snippet"], language="python")
        st.info(f"💡 **Remediation Guide:**\n{f['remediation']}")

def _render_findings_tab(findings: list):
    """Renders security and secrets findings list."""
    if not findings:
        st.success("✅ Clean Security Scan: Zero secrets, injections, or insecure deserialization calls detected!")
        return
    st.write(f"Detected **{len(findings)}** security alerts across files:")
    for f in findings:
        _render_finding_item(f)

def _render_license_tab(lic: dict):
    """Renders third-party license audit view."""
    st.subheader("Third-Party License & Compliance Audit")
    st.markdown(f"**Identified License**: `{lic.get('license_name', 'Unknown')}` (`{lic.get('spdx_id', 'NONE')}`)")
    st.markdown(f"**License Category**: `{lic.get('category')}`")
    st.markdown(f"**Commercial Use Permitted**: {'✅ Yes' if lic.get('commercial_use_allowed') else '❌ Requires Review'}")
    st.markdown(f"**Attribution Required**: {'Yes' if lic.get('attribution_required') else 'No'}")
    st.markdown(f"**Copyleft Risk**: {'⚠️ High (Viral copyleft)' if lic.get('copyleft_risk') else '✅ None (Permissive)'}")

def show_security_page():
    """Main security audit page."""
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
        sec = api.get_security_audit(selected_repo_id)
    except Exception as e:
        st.error(f"Failed to fetch security audit: {e}")
        return

    _render_severity_metrics(sec)
    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

    tab_findings, tab_license = st.tabs(["⚠️ Security & Secret Findings", "📜 License Compliance"])
    with tab_findings:
        _render_findings_tab(sec.get("findings", []))
    with tab_license:
        _render_license_tab(sec.get("license", {}))

show_security_page()
