import sys
from pathlib import Path

# Ensure repository root is in sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st

st.set_page_config(
    page_title="AI-Code-Analyser | Developer Intelligence Platform",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded"
)

def _page_path(filename: str) -> str:
    """Resolves page file path portably for local and cloud environments."""
    return str((ROOT_DIR / "frontend" / "pages" / filename).resolve())

# Define pages using modern Streamlit st.Page API
dashboard_page = st.Page(_page_path("dashboard.py"), title="Dashboard", icon="📊", default=True)
repo_page = st.Page(_page_path("repository.py"), title="Connect Repository", icon="🔗")
explorer_page = st.Page(_page_path("code_explorer.py"), title="Code Explorer & AST", icon="📁")
chat_page = st.Page(_page_path("ai_chat.py"), title="AI Code Chat & Q&A", icon="💬")
arch_page = st.Page(_page_path("architecture.py"), title="Architecture Mapper", icon="🏛️")
impact_page = st.Page(_page_path("change_impact.py"), title="Change Impact Simulator", icon="⚡")
test_page = st.Page(_page_path("test_generator.py"), title="Test Case Generator", icon="🧪")
tech_debt_page = st.Page(_page_path("tech_debt.py"), title="Technical Debt Detector", icon="📉")
review_page = st.Page(_page_path("code_review.py"), title="Pull Request Reviewer", icon="🔍")
security_page = st.Page(_page_path("security.py"), title="Security & Compliance", icon="🛡️")
onboarding_page = st.Page(_page_path("onboarding.py"), title="Smart Onboarding", icon="🚀")

# Organize into structured logical sections
pg = st.navigation(
    {
        "Overview": [dashboard_page, repo_page, explorer_page],
        "Code Intelligence": [chat_page, arch_page, impact_page],
        "Quality & Security": [test_page, tech_debt_page, review_page, security_page, onboarding_page]
    }
)

pg.run()
