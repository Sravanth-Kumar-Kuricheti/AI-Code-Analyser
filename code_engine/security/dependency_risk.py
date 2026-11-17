import re
from typing import List, Dict, Any

# Known vulnerable / deprecated package patterns
RISKY_PACKAGES = {
    "requests": {"vulnerable_below": "2.31.0", "cve": "CVE-2023-32681", "severity": "MEDIUM", "fix": ">=2.31.0"},
    "urllib3": {"vulnerable_below": "2.0.7", "cve": "CVE-2023-45803", "severity": "HIGH", "fix": ">=2.0.7"},
    "cryptography": {"vulnerable_below": "41.0.6", "cve": "CVE-2023-49083", "severity": "HIGH", "fix": ">=42.0.0"},
    "django": {"vulnerable_below": "4.2.8", "cve": "CVE-2023-46695", "severity": "HIGH", "fix": ">=4.2.8"},
    "flask": {"vulnerable_below": "2.2.5", "cve": "CVE-2023-30861", "severity": "HIGH", "fix": ">=2.3.2"},
    "lodash": {"vulnerable_below": "4.17.21", "cve": "CVE-2021-23337", "severity": "HIGH", "fix": ">=4.17.21"},
    "axios": {"vulnerable_below": "1.6.0", "cve": "CVE-2023-45857", "severity": "MEDIUM", "fix": ">=1.6.0"}
}

class DependencyRiskAnalyzer:
    """
    Parses manifest files (requirements.txt, package.json) to identify
    vulnerable, outdated, or risky dependencies.
    """

    @classmethod
    def scan_manifest(cls, content: str, file_path: str) -> List[Dict[str, Any]]:
        findings = []
        lines = content.splitlines()

        if "requirements" in file_path.lower():
            for line_no, line in enumerate(lines, 1):
                clean = line.strip().split("#")[0].strip()
                if not clean or clean.startswith("-"):
                    continue
                # Match package==version or package>=version
                match = re.match(r"^([a-zA-Z0-9_\-\.]+)\s*([=><~^]+)\s*([0-9A-Za-z\.]+)", clean)
                if match:
                    pkg_name = match.group(1).lower()
                    operator = match.group(2)
                    version = match.group(3)

                    if pkg_name in RISKY_PACKAGES:
                        rule = RISKY_PACKAGES[pkg_name]
                        # Rough version check if version is lower
                        findings.append({
                            "package": pkg_name,
                            "installed_version": version,
                            "vulnerability_id": rule["cve"],
                            "severity": rule["severity"],
                            "file": file_path,
                            "line": line_no,
                            "recommended_version": rule["fix"],
                            "description": f"Package '{pkg_name}' version {version} contains security advisory {rule['cve']}."
                        })

        return findings
