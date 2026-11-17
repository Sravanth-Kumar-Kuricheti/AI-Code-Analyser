import ast
import os
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Set, Tuple

LANGUAGE_EXTENSIONS = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".go": "go",
    ".java": "java",
    ".rs": "rust",
    ".cpp": "cpp",
    ".c": "c",
    ".h": "c",
    ".cs": "csharp",
    ".php": "php",
    ".rb": "ruby",
    ".html": "html",
    ".css": "css",
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".md": "markdown",
    ".sql": "sql",
    ".sh": "bash",
    ".dockerfile": "dockerfile"
}

def detect_language(file_path: str) -> str:
    """Detects programming language from file extension or standard filenames."""
    path = Path(file_path)
    if path.name.lower() == "dockerfile":
        return "dockerfile"
    return LANGUAGE_EXTENSIONS.get(path.suffix.lower(), "text")

def _calc_node_complexity(node: ast.AST) -> int:
    """Calculates cyclomatic complexity for an AST function/method node."""
    complexity = 1
    for sub in ast.walk(node):
        if isinstance(sub, (ast.If, ast.While, ast.For, ast.AsyncFor, ast.ExceptHandler, ast.With, ast.Assert)):
            complexity += 1
        elif isinstance(sub, ast.BoolOp):
            complexity += len(sub.values) - 1
    return complexity

def _extract_imports(tree: ast.AST) -> List[Dict[str, Any]]:
    """Extracts top-level and nested module import declarations."""
    imports = []
    top_level = set(tree.body)
    for node in ast.walk(tree):
        is_top = node in top_level
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append({
                    "module": alias.name,
                    "alias": alias.asname or alias.name,
                    "line": node.lineno,
                    "is_top_level": is_top
                })
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            for alias in node.names:
                full_mod = f"{mod}.{alias.name}" if mod else alias.name
                imports.append({
                    "module": full_mod,
                    "base_module": mod,
                    "name": alias.name,
                    "line": node.lineno,
                    "is_top_level": is_top
                })
    return imports

def _extract_class_methods(cls_node: ast.ClassDef, norm_path: str) -> Tuple[List[Dict[str, Any]], Set[ast.AST], int]:
    """Extracts member functions and methods from a class definition."""
    methods = []
    method_nodes = set()
    complexity_sum = 0
    for sub in cls_node.body:
        if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)):
            method_nodes.add(sub)
            m_comp = _calc_node_complexity(sub)
            complexity_sum += m_comp
            m_end = getattr(sub, 'end_lineno', sub.lineno)
            args_list = [a.arg for a in sub.args.args]
            prefix = "async def" if isinstance(sub, ast.AsyncFunctionDef) else "def"
            methods.append({
                "name": f"{cls_node.name}.{sub.name}",
                "symbol_type": "method",
                "file_path": norm_path,
                "line_start": sub.lineno,
                "line_end": m_end,
                "signature": f"{prefix} {sub.name}({', '.join(args_list)})",
                "docstring": ast.get_docstring(sub) or "",
                "complexity": m_comp,
                "is_api_endpoint": False
            })
    return methods, method_nodes, complexity_sum

def _extract_classes(tree: ast.AST, norm_path: str) -> Tuple[List[Dict[str, Any]], Set[ast.AST], int]:
    """Extracts class definitions and their contained methods."""
    symbols = []
    class_methods = set()
    total_complexity = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            bases = [ast.unparse(b) for b in node.bases] if hasattr(ast, 'unparse') else []
            symbols.append({
                "name": node.name,
                "symbol_type": "class",
                "file_path": norm_path,
                "line_start": node.lineno,
                "line_end": getattr(node, 'end_lineno', node.lineno),
                "signature": f"class {node.name}({', '.join(bases)})",
                "docstring": ast.get_docstring(node) or "",
                "complexity": 1,
                "is_api_endpoint": False
            })
            methods, m_nodes, comp = _extract_class_methods(node, norm_path)
            symbols.extend(methods)
            class_methods.update(m_nodes)
            total_complexity += comp
    return symbols, class_methods, total_complexity

def _detect_endpoint(node: ast.AST) -> Tuple[bool, str, str]:
    """Detects HTTP route decorators on function definitions."""
    for dec in node.decorator_list:
        dec_str = ast.unparse(dec) if hasattr(ast, 'unparse') else ""
        m = re.search(r'\.(get|post|put|delete|patch|options|head)\s*\(\s*["\']([^"\']+)["\']', dec_str, re.I)
        if m:
            return True, m.group(1).upper(), m.group(2)
    return False, "", ""

def _extract_top_functions(tree: ast.AST, norm_path: str, class_methods: Set[ast.AST]) -> Tuple[List[Dict[str, Any]], int]:
    """Extracts top-level functions and API endpoints."""
    symbols = []
    complexity_sum = 0
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node not in class_methods:
            is_ep, method, path = _detect_endpoint(node)
            comp = _calc_node_complexity(node)
            complexity_sum += comp
            args_list = [a.arg for a in node.args.args]
            prefix = "async def" if isinstance(node, ast.AsyncFunctionDef) else "def"
            symbols.append({
                "name": node.name,
                "symbol_type": "endpoint" if is_ep else "function",
                "file_path": norm_path,
                "line_start": node.lineno,
                "line_end": getattr(node, 'end_lineno', node.lineno),
                "signature": f"{prefix} {node.name}({', '.join(args_list)})",
                "docstring": ast.get_docstring(node) or "",
                "complexity": comp,
                "is_api_endpoint": is_ep,
                "http_method": method,
                "http_path": path
            })
    return symbols, complexity_sum

def _parse_js_ts(lines: List[str], norm_path: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Extracts symbols and imports from JavaScript/TypeScript source lines."""
    symbols, imports = [], []
    for i, line in enumerate(lines, 1):
        imp_m = re.search(r'import\s+(?:\{([^}]+)\}|\*\s+as\s+(\w+)|(\w+))\s+from\s+[\'"]([^\'"]+)[\'"]', line)
        if imp_m:
            imports.append({"module": imp_m.group(4), "line": i, "is_top_level": True})
        fn_m = re.search(r'(?:export\s+)?(?:async\s+)?function\s+([A-Za-z0-9_$]+)\s*\(([^)]*)\)', line)
        if fn_m:
            symbols.append({"name": fn_m.group(1), "symbol_type": "function", "file_path": norm_path, "line_start": i, "line_end": i + 10, "signature": fn_m.group(0), "docstring": "", "complexity": 1, "is_api_endpoint": False})
        cls_m = re.search(r'(?:export\s+)?class\s+([A-Za-z0-9_$]+)', line)
        if cls_m:
            symbols.append({"name": cls_m.group(1), "symbol_type": "class", "file_path": norm_path, "line_start": i, "line_end": i + 20, "signature": cls_m.group(0), "docstring": "", "complexity": 1, "is_api_endpoint": False})
        rt_m = re.search(r'(?:app|router)\.(get|post|put|delete|patch)\s*\(\s*[\'"]([^\'"]+)[\'"]', line, re.I)
        if rt_m:
            symbols.append({"name": f"{rt_m.group(1).upper()} {rt_m.group(2)}", "symbol_type": "endpoint", "file_path": norm_path, "line_start": i, "line_end": i + 5, "signature": line.strip(), "docstring": "", "complexity": 1, "is_api_endpoint": True, "http_method": rt_m.group(1).upper(), "http_path": rt_m.group(2)})
    return symbols, imports

def _parse_go(lines: List[str], norm_path: str) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Extracts symbols and imports from Go source lines."""
    symbols, imports = [], []
    for i, line in enumerate(lines, 1):
        fn_m = re.search(r'func\s+(?:\([^)]+\)\s+)?([A-Za-z0-9_]+)\s*\(([^)]*)\)', line)
        if fn_m:
            symbols.append({"name": fn_m.group(1), "symbol_type": "function", "file_path": norm_path, "line_start": i, "line_end": i + 15, "signature": fn_m.group(0), "docstring": "", "complexity": 1, "is_api_endpoint": False})
        imp_m = re.search(r'import\s+[\'"]([^\'"]+)[\'"]', line)
        if imp_m:
            imports.append({"module": imp_m.group(1), "line": i, "is_top_level": True})
    return symbols, imports

def _parse_java_csharp(lines: List[str], norm_path: str) -> List[Dict[str, Any]]:
    """Extracts classes and methods from Java and C# source lines."""
    symbols = []
    for i, line in enumerate(lines, 1):
        cls_m = re.search(r'(?:public|private|protected)?\s*(?:static)?\s*class\s+([A-Za-z0-9_]+)', line)
        if cls_m:
            symbols.append({"name": cls_m.group(1), "symbol_type": "class", "file_path": norm_path, "line_start": i, "line_end": i + 25, "signature": cls_m.group(0), "docstring": "", "complexity": 1, "is_api_endpoint": False})
        fn_m = re.search(r'(?:public|private|protected)?\s*(?:static)?\s*(?:[\w<>\[\]]+)\s+([A-Za-z0-9_]+)\s*\(([^)]*)\)\s*\{', line)
        if fn_m and fn_m.group(1) not in ("if", "for", "while", "switch", "catch"):
            symbols.append({"name": fn_m.group(1), "symbol_type": "function", "file_path": norm_path, "line_start": i, "line_end": i + 15, "signature": fn_m.group(0), "docstring": "", "complexity": 1, "is_api_endpoint": False})
    return symbols

class ASTParser:
    """Multi-language AST and semantic symbol parser."""
    
    @staticmethod
    def parse_python_file(content: str, rel_path: str) -> Dict[str, Any]:
        """Parses Python source content into structural AST representations."""
        norm_path = rel_path.replace("\\", "/")
        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            return {"rel_path": norm_path, "language": "python", "parse_error": str(e), "symbols": [], "imports": [], "calls": [], "cyclomatic_complexity": 1.0, "maintainability_index": 50.0}

        imports = _extract_imports(tree)
        cls_symbols, class_methods, cls_comp = _extract_classes(tree, norm_path)
        fn_symbols, fn_comp = _extract_top_functions(tree, norm_path, class_methods)
        
        all_symbols = cls_symbols + fn_symbols
        loc = len(content.splitlines())
        avg_comp = ((cls_comp + fn_comp) / max(1, len(all_symbols))) if all_symbols else 1.0
        mi = max(0.0, min(100.0, 171.0 - 5.2 * (avg_comp ** 0.5) - 0.23 * loc))

        return {
            "rel_path": norm_path,
            "language": "python",
            "symbols": all_symbols,
            "imports": imports,
            "calls": [],
            "cyclomatic_complexity": round(avg_comp, 2),
            "maintainability_index": round(mi, 2),
            "lines_of_code": loc
        }

    @staticmethod
    def parse_generic_file(content: str, rel_path: str, language: str) -> Dict[str, Any]:
        """Parses JavaScript, TypeScript, Go, Java, or C# using regex AST heuristics."""
        norm_path = rel_path.replace("\\", "/")
        lines = content.splitlines()
        loc = len(lines)
        symbols, imports = [], []

        if language in ("javascript", "typescript"):
            symbols, imports = _parse_js_ts(lines, norm_path)
        elif language == "go":
            symbols, imports = _parse_go(lines, norm_path)
        elif language in ("java", "csharp"):
            symbols = _parse_java_csharp(lines, norm_path)

        mi = max(0.0, min(100.0, 171.0 - 0.25 * loc))
        return {
            "rel_path": norm_path,
            "language": language,
            "symbols": symbols,
            "imports": imports,
            "calls": [],
            "cyclomatic_complexity": 1.0,
            "maintainability_index": round(mi, 2),
            "lines_of_code": loc
        }

    @classmethod
    def parse_file(cls, file_path: str, repo_root: str) -> Dict[str, Any]:
        """Reads file from disk and parses into language-specific AST data."""
        norm_path = file_path.replace("\\", "/")
        full_path = Path(repo_root) / norm_path
        if not full_path.exists() or not full_path.is_file():
            return {"rel_path": norm_path, "language": "unknown", "symbols": [], "imports": [], "calls": [], "cyclomatic_complexity": 1.0, "maintainability_index": 100.0, "lines_of_code": 0}
        
        language = detect_language(norm_path)
        try:
            with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        except Exception:
            return {"rel_path": norm_path, "language": language, "symbols": [], "imports": [], "calls": [], "cyclomatic_complexity": 1.0, "maintainability_index": 100.0, "lines_of_code": 0}

        if language == "python":
            return cls.parse_python_file(content, norm_path)
        return cls.parse_generic_file(content, norm_path, language)
