import re
from typing import List, Dict, Any

SECRET_PATTERNS = [
    {
        "id": "SEC001",
        "name": "AWS Access Key",
        "pattern": r"(?:A3T[A-Z0-9]|AKIA|AGPA|AIDA|AROA|AIPA|ANPA|ANVA|ASIA)[A-Z0-9]{16}",
        "severity": "CRITICAL"
    },
    {
        "id": "SEC002",
        "name": "GitHub Personal Access Token",
        "pattern": r"(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{36,255}",
        "severity": "CRITICAL"
    },
    {
        "id": "SEC003",
        "name": "Groq / OpenAI API Key",
        "pattern": r"(?:sk-|gsk_)[A-Za-z0-9_-]{32,64}",
        "severity": "CRITICAL"
    },
    {
        "id": "SEC004",
        "name": "RSA / SSH Private Key Header",
        "pattern": r"-----BEGIN (?:RSA|OPENSSH|DSA|EC)?\s?PRIVATE KEY-----",
        "severity": "CRITICAL"
    },
    {
        "id": "SEC005",
        "name": "Slack Bot / User Token",
        "pattern": r"xox[baprs]-[0-9]{10,13}-[0-9]{10,13}[a-zA-Z0-9]*",
        "severity": "HIGH"
    },
    {
        "id": "SEC006",
        "name": "Generic Hardcoded Secret/Password Assignment",
        "pattern": r'''(?i)(?:api_key|apikey|secret|password|passwd|auth_token)\s*[:=]\s*["']([A-Za-z0-9!@#$%^&*()_+=\-~]{8,})["']''',
        "severity": "HIGH"
    },
    {
        "id": "SEC007",
        "name": "Database Connection String with Credentials",
        "pattern": r'''(?i)(?:postgres|postgresql|mysql|mongodb(?:\+srv)?):\/\/[a-zA-Z0-9_]+:([^@\/\s]+)@''',
        "severity": "CRITICAL"
    }
]

GENERIC_PLACEHOLDERS = [
    "your_groq_api_key_here", "your_api_key", "your_secret_here", "your_password_here",
    "change_me", "changeme", "replace_me", "<api_key>", "<password>", "dummy_key"
]

def _mask_secret(secret_val: str) -> str:
    """Masks secret value for safe log rendering."""
    if len(secret_val) > 8:
        return secret_val[:3] + "..." + secret_val[-4:]
    return "***"

def _scan_line_for_pattern(line: str, line_no: int, norm_path: str, p_def: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Checks a single line against a specific secret pattern definition."""
    findings = []
    for m in re.finditer(p_def["pattern"], line):
        secret_val = m.group(0)
        if p_def["id"] == "SEC006" and any(ph in secret_val.lower() for ph in GENERIC_PLACEHOLDERS):
            continue
        masked = _mask_secret(secret_val)
        findings.append({
            "file_path": norm_path,
            "line_number": line_no,
            "severity": p_def["severity"],
            "category": "SECRET_EXPOSURE",
            "rule_id": p_def["id"],
            "description": f"Detected potential {p_def['name']} in code.",
            "code_snippet": line.strip()[:100].replace(secret_val, masked),
            "remediation": "Revoke credential immediately, migrate to environment variables (.env) or Secret Manager, and purge Git commit history."
        })
    return findings

class SecretScanner:
    """Scans files for committed secrets, tokens, private keys, and API credentials."""

    @classmethod
    def scan_file(cls, content: str, rel_path: str) -> List[Dict[str, Any]]:
        """Scans content lines for secret patterns."""
        norm_path = rel_path.replace("\\", "/")
        if norm_path.endswith(".example") or ".env.example" in norm_path:
            return []

        findings = []
        for line_no, line in enumerate(content.splitlines(), 1):
            for p_def in SECRET_PATTERNS:
                findings.extend(_scan_line_for_pattern(line, line_no, norm_path, p_def))
        return findings
