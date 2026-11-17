import streamlit as st

CUSTOM_CSS = """
<style>
/* Global Theme Overrides */
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
}

code, pre {
    font-family: 'JetBrains Mono', monospace !important;
}

/* Metric Cards */
.metric-card {
    background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 1.25rem;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    transition: transform 0.2s ease, border-color 0.2s ease;
}
.metric-card:hover {
    transform: translateY(-2px);
    border-color: #38bdf8;
}
.metric-title {
    font-size: 0.875rem;
    font-weight: 500;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 0.5rem;
}
.metric-value {
    font-size: 2rem;
    font-weight: 700;
    color: #f8fafc;
    line-height: 1;
}
.metric-subtitle {
    font-size: 0.8125rem;
    color: #64748b;
    margin-top: 0.5rem;
}

/* Badges */
.badge {
    display: inline-flex;
    align-items: center;
    padding: 0.25rem 0.625rem;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.025em;
}
.badge-critical { background-color: rgba(239, 68, 68, 0.2); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.3); }
.badge-high { background-color: rgba(249, 115, 22, 0.2); color: #fb923c; border: 1px solid rgba(249, 115, 22, 0.3); }
.badge-medium { background-color: rgba(245, 158, 11, 0.2); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.3); }
.badge-low { background-color: rgba(16, 185, 129, 0.2); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3); }
.badge-info { background-color: rgba(56, 189, 248, 0.2); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.3); }

/* Citation Box */
.citation-pill {
    display: inline-block;
    background: #1e293b;
    border: 1px solid #475569;
    border-radius: 6px;
    padding: 2px 8px;
    font-size: 0.75rem;
    font-family: 'JetBrains Mono', monospace;
    color: #38bdf8;
    margin: 2px 4px 2px 0;
}

/* Hero Banner */
.hero-banner {
    background: linear-gradient(135deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.9) 100%);
    border: 1px solid #334155;
    border-radius: 16px;
    padding: 2rem;
    margin-bottom: 2rem;
    backdrop-filter: blur(8px);
}
</style>
"""

def apply_custom_styles():
    """Injects core design system styles into the Streamlit app."""
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

def render_metric_card(title: str, value: str, subtitle: str = "", delta_color: str = "#38bdf8"):
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">{title}</div>
        <div class="metric-value" style="color: {delta_color}">{value}</div>
        {f'<div class="metric-subtitle">{subtitle}</div>' if subtitle else ''}
    </div>
    """, unsafe_allow_html=True)
