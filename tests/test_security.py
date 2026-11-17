import pytest
from code_engine.security.secret_scanner import SecretScanner
from code_engine.security.bandit_scanner import BanditScanner
from code_engine.security.dependency_risk import DependencyRiskAnalyzer

def test_secret_scanner():
    code_with_secret = """
AWS_SECRET = "AKIAIOSFODNN7EXAMPLE"
GITHUB_KEY = "ghp_1234567890abcdefghijklmnopqrstuvwxyz12"
"""
    findings = SecretScanner.scan_file(code_with_secret, "config.py")
    assert len(findings) >= 2
    rule_ids = [f["rule_id"] for f in findings]
    assert "SEC001" in rule_ids
    assert "SEC002" in rule_ids

def test_bandit_scanner():
    code_with_vuln = """
import subprocess

def run_cmd(user_input):
    subprocess.Popen(user_input, shell=True)
"""
    findings = BanditScanner.scan_python_content(code_with_vuln, "shell_helper.py")
    assert len(findings) >= 1
    assert findings[0]["rule_id"] == "B602"

def test_dependency_risk_analyzer():
    manifest = """
requests==2.28.1
urllib3==1.26.14
"""
    findings = DependencyRiskAnalyzer.scan_manifest(manifest, "requirements.txt")
    assert len(findings) >= 1
    pkg_names = [f["package"] for f in findings]
    assert "requests" in pkg_names or "urllib3" in pkg_names
