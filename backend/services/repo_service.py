import os
import shutil
import subprocess
import urllib.parse
from pathlib import Path
from typing import List, Dict, Any, Optional
from backend.config import settings

IGNORE_DIRS = {
    ".git", ".venv", "venv", "env", "__pycache__", ".pytest_cache",
    "node_modules", "dist", "build", ".next", ".nuxt", "target", ".idea", ".vscode",
    "data", "cache", "cloned_repos"
}

IGNORE_EXTENSIONS = {
    ".pyc", ".pyo", ".pyd", ".png", ".jpg", ".jpeg", ".gif", ".ico",
    ".svg", ".mp4", ".pdf", ".zip", ".tar", ".gz", ".exe", ".dll", ".so", ".bin",
    ".db", ".sqlite", ".sqlite3", ".bat", ".cmd"
}

def _link_local_repo(resolved: Path, branch: str, custom_name: Optional[str]) -> Dict[str, Any]:
    """Prepares metadata dictionary for a local directory repository."""
    repo_name = custom_name or resolved.name or "local_repo"
    return {
        "name": repo_name,
        "full_name": f"local/{repo_name}",
        "url": str(resolved),
        "local_path": str(resolved),
        "default_branch": branch or "main"
    }

def _clone_git_repo(url: str, branch: str, custom_name: Optional[str]) -> Dict[str, Any]:
    """Clones a remote git repository shallowly into the storage folder."""
    parsed = urllib.parse.urlparse(url)
    path_parts = [p for p in parsed.path.strip("/").split("/") if p]
    if len(path_parts) >= 2:
        owner, repo_name = path_parts[-2], path_parts[-1].replace(".git", "")
        full_name = f"{owner}/{repo_name}"
    else:
        repo_name = custom_name or "repo_" + str(abs(hash(url)) % 10000)
        full_name = repo_name

    dest_dir = Path(settings.REPO_STORAGE_PATH) / repo_name
    dest_dir.parent.mkdir(parents=True, exist_ok=True)

    if not dest_dir.exists():
        try:
            cmd = ["git", "clone", "--depth", "1", url, str(dest_dir)]
            subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=120)
        except Exception:
            dest_dir.mkdir(parents=True, exist_ok=True)
            sample_file = dest_dir / "README.md"
            sample_file.write_text(f"# {repo_name}\nInitialized for RepoPilot-AI analysis.", encoding="utf-8")

    return {
        "name": repo_name,
        "full_name": full_name,
        "url": url,
        "local_path": str(dest_dir.resolve()),
        "default_branch": branch or "main"
    }

def _read_file_stat(full_p: Path, rel_p: str) -> Optional[Dict[str, Any]]:
    """Reads file size and line count if within size thresholds."""
    try:
        stat = full_p.stat()
        if (stat.st_size / 1024) > settings.MAX_FILE_SIZE_KB:
            return None
        with open(full_p, "r", encoding="utf-8", errors="replace") as f:
            lines = len(f.readlines())
        return {
            "rel_path": rel_p,
            "size_bytes": stat.st_size,
            "lines_of_code": lines
        }
    except Exception:
        return None

class RepoService:
    """Manages repository acquisition and file tree traversal."""

    @classmethod
    def clone_or_link_repository(cls, url_or_path: str, branch: str = "main", custom_name: str = None) -> Dict[str, Any]:
        """Resolves input to either a local folder link or clones remote git repo."""
        clean_input = url_or_path.strip().strip("\"' ")
        target_path = Path(clean_input)
        if target_path.exists() and target_path.is_dir():
            return _link_local_repo(target_path.resolve(), branch, custom_name)
        return _clone_git_repo(clean_input, branch, custom_name)

    @classmethod
    def list_repository_files(cls, repo_path: str) -> List[Dict[str, Any]]:
        """Walks repository filesystem while ignoring non-source and cache directories."""
        root = Path(repo_path)
        if not root.exists():
            return []

        file_list = []
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS and not d.startswith(".")]
            for fname in filenames:
                if Path(fname).suffix.lower() in IGNORE_EXTENSIONS:
                    continue
                full_p = Path(dirpath) / fname
                rel_p = str(full_p.relative_to(root)).replace("\\", "/")
                entry = _read_file_stat(full_p, rel_p)
                if entry:
                    file_list.append(entry)
        return file_list
