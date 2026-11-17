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

def show_code_review_page():
    apply_custom_styles()

    st.title("🔍 AI Pull Request & Diff Reviewer")
    st.write("Automated code review for pull requests, Git diffs, and staging changes. Evaluates architectural integrity, correctness, security risks, and provides line-by-line refactoring recommendations.")

    try:
        repos = api.list_repos()
    except Exception:
        repos = []

    if not repos:
        st.warning("No repositories found. Connect a repository first.")
        return

    selected_repo_id = select_active_repo(repos, label="Repository Context")

    sample_diff = """diff --git a/backend/services/auth.py b/backend/services/auth.py
index e69de29..b4f2c01 100644
--- a/backend/services/auth.py
+++ b/backend/services/auth.py
@@ -10,6 +10,8 @@ def authenticate_user(username, password):
-    query = "SELECT * FROM users WHERE username = %s AND password = %s"
-    cursor.execute(query, (username, password))
+    query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
+    cursor.execute(query)
"""

    pr_title = st.text_input("PR Title", value="Refactor user authentication query")
    diff_input = st.text_area("Git Diff or Changed Code", value=sample_diff, height=220)

    if st.button("🚀 Run Automated PR Review", type="primary"):
        with st.spinner("Reviewing diff for bugs, anti-patterns, and security regressions..."):
            try:
                res = api.review_pr(selected_repo_id, diff_input, pr_title)
                st.markdown("---")
                st.subheader("📋 Pull Request Review Report")
                st.markdown(res.get("review_summary", ""))
            except Exception as e:
                st.error(f"PR review failed: {e}")

show_code_review_page()
