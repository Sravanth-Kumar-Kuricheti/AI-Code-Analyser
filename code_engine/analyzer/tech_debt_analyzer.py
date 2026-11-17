from typing import List, Dict, Any, Tuple, Optional

def _check_file_maintainability(rel: str, loc: int, mi: float) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    """Flags files with maintainability index below 50."""
    if mi < 50.0:
        low_file = {"file": rel, "maintainability_index": mi, "loc": loc}
        issue = {
            "category": "Maintainability",
            "severity": "HIGH",
            "file": rel,
            "description": f"Low maintainability index ({mi}/100) with {loc} lines of code.",
            "effort_hours": round(loc / 100, 1)
        }
        return low_file, issue
    return None, None

def _inspect_symbol_smells(sym: Dict[str, Any], rel: str) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]], Optional[Dict[str, Any]], List[Dict[str, Any]], int]:
    """Inspects a single symbol for oversized length, complexity, and missing docstrings."""
    fn_len = sym.get("line_end", 0) - sym.get("line_start", 0) + 1
    fn_comp = sym.get("complexity", 1)
    name = sym.get("name", "")
    line_start = sym.get("line_start", 1)

    long_fn, comp_method, missing_doc = None, None, None
    issues = []

    if fn_len > 50:
        long_fn = {"name": name, "file": rel, "lines": fn_len, "start": line_start, "end": sym.get("line_end")}
        issues.append({
            "category": "Code Smell", "severity": "MEDIUM", "file": rel, "line": line_start,
            "description": f"Long function '{name}' ({fn_len} LOC). Decompose into smaller subroutines.",
            "effort_hours": 1.5
        })

    if fn_comp > 8:
        comp_method = {"name": name, "file": rel, "complexity": fn_comp, "start": line_start}
        issues.append({
            "category": "Complexity", "severity": "HIGH" if fn_comp > 15 else "MEDIUM", "file": rel, "line": line_start,
            "description": f"Cyclomatic complexity of '{name}' is {fn_comp}. High branch density causes testing hurdles.",
            "effort_hours": 2.0
        })

    if not sym.get("docstring") and fn_len > 15:
        missing_doc = {"name": name, "file": rel, "start": line_start}

    return long_fn, comp_method, missing_doc, issues, fn_comp

def _process_file_symbols(f: Dict[str, Any], rel: str, acc: Dict[str, Any]):
    """Processes functions and methods in a single file AST."""
    for sym in f.get("symbols", []):
        if sym.get("symbol_type") in ("function", "endpoint", "method"):
            acc["total_functions"] += 1
            l_fn, c_m, m_d, s_issues, comp = _inspect_symbol_smells(sym, rel)
            acc["total_complexity"] += comp
            if l_fn: acc["long_fns"].append(l_fn)
            if c_m: acc["comp_methods"].append(c_m)
            if m_d: acc["missing_docs"].append(m_d)
            acc["issues"].extend(s_issues)

def _accumulate_file_ast(f: Dict[str, Any], acc: Dict[str, Any]):
    """Accumulates lines, maintainability issues, and symbols for a single file."""
    rel = f.get("rel_path", "").replace("\\", "/")
    loc = f.get("lines_of_code", 0)
    acc["total_loc"] += loc
    if rel.startswith(("tests/", "test/")) or "/tests/" in rel or "/test/" in rel:
        return

    low_file, maint_issue = _check_file_maintainability(rel, loc, f.get("maintainability_index", 100.0))
    if low_file:
        acc["low_maint"].append(low_file)
        acc["issues"].append(maint_issue)
    _process_file_symbols(f, rel, acc)

def _calculate_grade(total_debt_hours: float) -> Tuple[str, str]:
    """Calculates letter grade and badge color from technical debt hours."""
    if total_debt_hours < 5:
        return "A", "#10B981"
    if total_debt_hours < 20:
        return "B", "#3B82F6"
    if total_debt_hours < 50:
        return "C", "#F59E0B"
    return "D", "#EF4444"

def _compile_recommendations(long_fns: list, comp_methods: list, missing_docs: list) -> List[str]:
    """Compiles clean code recommendations."""
    recs = []
    if long_fns:
        recs.append(f"Refactor {len(long_fns)} oversized functions to adhere to Single Responsibility Principle.")
    if comp_methods:
        recs.append(f"Decompose {len(comp_methods)} highly branched methods to reduce cyclomatic risk.")
    if missing_docs:
        recs.append(f"Add docstrings to {len(missing_docs)} undocumented routines to streamline developer onboarding.")
    if not recs:
        recs.append("Repository maintains pristine clean code: zero oversized functions or high-complexity bottlenecks detected!")
    return recs

class TechDebtAnalyzer:
    """Detects code smells, maintainability issues, and estimates remediation effort."""

    @classmethod
    def analyze_repository(cls, files_ast: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyzes codebase ASTs and aggregates technical debt report."""
        acc = {
            "issues": [], "long_fns": [], "comp_methods": [], "missing_docs": [],
            "low_maint": [], "total_loc": 0, "total_functions": 0, "total_complexity": 0
        }
        for f in files_ast:
            _accumulate_file_ast(f, acc)

        total_debt = sum(iss.get("effort_hours", 1.0) for iss in acc["issues"])
        grade, badge_color = _calculate_grade(total_debt)
        avg_comp = round(acc["total_complexity"] / max(1, acc["total_functions"]), 2)

        return {
            "grade": grade,
            "badge_color": badge_color,
            "total_debt_hours": round(total_debt, 1),
            "total_issues_count": len(acc["issues"]),
            "average_cyclomatic_complexity": avg_comp,
            "total_loc": acc["total_loc"],
            "total_functions": acc["total_functions"],
            "long_functions": acc["long_fns"],
            "complex_methods": acc["comp_methods"],
            "missing_docs_count": len(acc["missing_docs"]),
            "low_maintainability_files": acc["low_maint"],
            "issues": acc["issues"],
            "recommendations": _compile_recommendations(acc["long_fns"], acc["comp_methods"], acc["missing_docs"])
        }

    @classmethod
    def build_refactor_prompt(cls, code_snippet: str, symbol_name: str, file_path: str, issue_description: str = "") -> Tuple[str, str]:
        """Builds clean code refactoring prompts for Groq LLM."""
        system_prompt = (
            "You are a Principal Software Architect and clean code refactoring authority (REFACTOR_CODE_PROMPT). "
            "Refactor monolithic or high-complexity routines into elegant, modular, production-grade code. "
            "Follow Martin Fowler's refactoring principles: Extract Method, Guard Clauses, Single Responsibility, and Type Annotations. "
            "Return clean Markdown with sections: 1. Refactoring Strategy & Patterns Applied, 2. Refactored Code (runnable, with extracted helpers), 3. Complexity & Maintainability Improvements."
        )
        user_prompt = (
            f"File: {file_path}\nRoutine: {symbol_name}\nContext: {issue_description or 'High cyclomatic complexity'}\n\n"
            f"Original Code:\n```python\n{code_snippet}\n```\n\n"
            "Please refactor this routine into clean, modular subroutines where each function is < 35 lines with cyclomatic complexity <= 4."
        )
        return system_prompt, user_prompt
