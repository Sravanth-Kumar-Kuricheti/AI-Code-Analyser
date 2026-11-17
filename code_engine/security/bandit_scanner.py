import ast
from typing import List, Dict, Any, Optional

def _check_subprocess_injection(node: ast.Call, rel_path: str, lines: List[str], call_name: str) -> Optional[Dict[str, Any]]:
    """Detects subprocess invocations with shell=True."""
    if call_name in ("Popen", "run", "call", "check_call", "check_output"):
        for kw in node.keywords:
            if kw.arg == "shell" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                return {
                    "file_path": rel_path,
                    "line_number": node.lineno,
                    "severity": "HIGH",
                    "category": "COMMAND_INJECTION",
                    "rule_id": "B602",
                    "description": "subprocess invocation with shell=True creates command injection risk.",
                    "code_snippet": lines[node.lineno - 1].strip() if node.lineno <= len(lines) else "",
                    "remediation": "Set shell=False and pass arguments as a list."
                }
    return None

def _check_pickle_deserialization(node: ast.Call, rel_path: str, lines: List[str], call_name: str) -> Optional[Dict[str, Any]]:
    """Detects pickle.loads or pickle.load calls."""
    if call_name in ("loads", "load") and hasattr(node.func, "value") and getattr(node.func.value, "id", "") == "pickle":
        return {
            "file_path": rel_path,
            "line_number": node.lineno,
            "severity": "CRITICAL",
            "category": "INSECURE_DESERIALIZATION",
            "rule_id": "B301",
            "description": "Pickle library is vulnerable to arbitrary code execution during deserialization.",
            "code_snippet": lines[node.lineno - 1].strip() if node.lineno <= len(lines) else "",
            "remediation": "Use safer serialization formats such as JSON, Protocol Buffers, or msgpack."
        }
    return None

def _check_sql_injection(node: ast.Call, rel_path: str, lines: List[str], call_name: str) -> Optional[Dict[str, Any]]:
    """Detects concatenated or f-string SQL queries passed to execute()."""
    if call_name in ("execute", "executemany"):
        if node.args and isinstance(node.args[0], (ast.JoinedStr, ast.BinOp)):
            return {
                "file_path": rel_path,
                "line_number": node.lineno,
                "severity": "HIGH",
                "category": "SQL_INJECTION",
                "rule_id": "B608",
                "description": "Possible SQL injection: raw formatted string or concatenation passed to database execute().",
                "code_snippet": lines[node.lineno - 1].strip() if node.lineno <= len(lines) else "",
                "remediation": "Pass SQL parameters as query parameters or use ORM filter methods."
            }
    return None

def _check_weak_crypto(node: ast.AST, rel_path: str, lines: List[str]) -> Optional[Dict[str, Any]]:
    """Detects usage of weak hash algorithms like md5 or sha1."""
    if isinstance(node, ast.Attribute) and node.attr in ("md5", "sha1"):
        return {
            "file_path": rel_path,
            "line_number": node.lineno,
            "severity": "MEDIUM",
            "category": "WEAK_CRYPTOGRAPHY",
            "rule_id": "B303",
            "description": f"Use of insecure MD5 or SHA1 hash algorithm '{node.attr}'.",
            "code_snippet": lines[node.lineno - 1].strip() if node.lineno <= len(lines) else "",
            "remediation": "Migrate to SHA256, SHA3, or bcrypt/argon2 for password hashing."
        }
    return None

class BanditScanner:
    """Scans Python codebases for AST security flaws and dangerous coding patterns."""

    @classmethod
    def scan_python_content(cls, content: str, rel_path: str) -> List[Dict[str, Any]]:
        """Parses AST and audits for known vulnerability patterns."""
        findings = []
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return findings

        lines = content.splitlines()
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                call_name = node.func.attr if isinstance(node.func, ast.Attribute) else node.func.id if isinstance(node.func, ast.Name) else ""
                for check in (_check_subprocess_injection, _check_pickle_deserialization, _check_sql_injection):
                    res = check(node, rel_path, lines, call_name)
                    if res:
                        findings.append(res)
            else:
                crypto_finding = _check_weak_crypto(node, rel_path, lines)
                if crypto_finding:
                    findings.append(crypto_finding)
        return findings
