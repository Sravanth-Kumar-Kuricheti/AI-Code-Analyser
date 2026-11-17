import os
import re
from typing import Dict, Any, List, Optional
from pathlib import Path

KNOWN_LICENSES = [
    {"name": "MIT License", "spdx": "MIT", "type": "Permissive", "keywords": ["MIT License", "Permission is hereby granted, free of charge"]},
    {"name": "Apache License 2.0", "spdx": "Apache-2.0", "type": "Permissive", "keywords": ["Apache License, Version 2.0", "http://www.apache.org/licenses/LICENSE-2.0"]},
    {"name": "GNU General Public License v3.0", "spdx": "GPL-3.0", "type": "Copyleft (Viral)", "keywords": ["GNU GENERAL PUBLIC LICENSE", "Version 3"]},
    {"name": "BSD 3-Clause License", "spdx": "BSD-3-Clause", "type": "Permissive", "keywords": ["BSD 3-Clause", "Redistribution and use in source and binary forms"]},
    {"name": "Mozilla Public License 2.0", "spdx": "MPL-2.0", "type": "Weak Copyleft", "keywords": ["Mozilla Public License", "Version 2.0"]}
]

def _match_license_keywords(content: str) -> Optional[Dict[str, Any]]:
    """Checks content against known license keyword signatures."""
    content_lower = content.lower()
    for lic in KNOWN_LICENSES:
        if any(kw.lower() in content_lower for kw in lic["keywords"]):
            return lic
    return None

def _scan_license_files(root: Path) -> Optional[Dict[str, Any]]:
    """Iterates candidate license files in root and extracts matching license."""
    candidate_names = {"license", "license.txt", "license.md", "copying", "package.json"}
    if not (root.exists() and root.is_dir()):
        return None
    for child in root.iterdir():
        if child.is_file() and child.name.lower() in candidate_names:
            try:
                content = child.read_text(encoding="utf-8", errors="replace")
                matched = _match_license_keywords(content)
                if matched:
                    return matched
            except Exception:
                continue
    return None

class LicenseComplianceChecker:
    """Identifies repository licenses and flags compliance obligations."""

    @classmethod
    def detect_repository_license(cls, repo_root: str) -> Dict[str, Any]:
        """Detects open source license and assesses commercial usability."""
        found = _scan_license_files(Path(repo_root))
        if not found:
            return {
                "license_name": "Unspecified / Proprietary",
                "spdx_id": "NONE",
                "category": "High Risk",
                "is_permissive": False,
                "commercial_use_allowed": False,
                "notes": "No standard open source license file identified. Default copyright laws apply."
            }

        is_permissive = found["type"] == "Permissive"
        notes = (
            "Permissive license: suitable for commercial and proprietary derivative works."
            if is_permissive else
            "Copyleft notice: requires derivative works and source code modifications to be shared under the same license terms."
        )

        return {
            "license_name": found["name"],
            "spdx_id": found["spdx"],
            "category": found["type"],
            "is_permissive": is_permissive,
            "commercial_use_allowed": True,
            "notes": notes
        }
