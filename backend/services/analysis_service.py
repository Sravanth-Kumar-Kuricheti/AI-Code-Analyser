import json
from pathlib import Path
from typing import Dict, Any, List
from sqlalchemy.orm import Session

from backend.models.schemas import (
    Repository, FileRecord, SymbolRecord, DependencyEdge, SecurityFinding
)
from code_engine.parser.ast_parser import ASTParser, detect_language
from code_engine.parser.chunker import CodeChunker
from code_engine.dependency.graph_builder import DependencyGraphBuilder
from code_engine.dependency.circular_detector import CircularDependencyDetector
from code_engine.analyzer.tech_debt_analyzer import TechDebtAnalyzer
from code_engine.security.secret_scanner import SecretScanner
from code_engine.security.bandit_scanner import BanditScanner
from code_engine.security.dependency_risk import DependencyRiskAnalyzer
from code_engine.security.license_checker import LicenseComplianceChecker
from ai_engine.embeddings.embedder import embedder
from ai_engine.retrieval.vector_store import vector_store
from backend.services.repo_service import RepoService

def _purge_existing_data(repo_id: int, db: Session):
    """Purges previous relational records and vector collection before re-indexing."""
    db.query(FileRecord).filter(FileRecord.repo_id == repo_id).delete()
    db.query(SymbolRecord).filter(SymbolRecord.repo_id == repo_id).delete()
    db.query(DependencyEdge).filter(DependencyEdge.repo_id == repo_id).delete()
    db.query(SecurityFinding).filter(SecurityFinding.repo_id == repo_id).delete()
    db.commit()
    try:
        vector_store.delete_collection(repo_id)
    except Exception:
        pass

def _record_file_symbols(repo_id: int, rel_p: str, ast_data: Dict[str, Any], db: Session) -> List[Dict[str, Any]]:
    """Persists extracted AST symbols to the database."""
    symbols = []
    for sym in ast_data.get("symbols", []):
        db.add(SymbolRecord(
            repo_id=repo_id,
            file_path=rel_p,
            name=sym.get("name", ""),
            symbol_type=sym.get("symbol_type", "function"),
            line_start=sym.get("line_start", 1),
            line_end=sym.get("line_end", 1),
            signature=sym.get("signature", ""),
            docstring=sym.get("docstring", ""),
            complexity=sym.get("complexity", 1),
            is_api_endpoint=sym.get("is_api_endpoint", False),
            http_method=sym.get("http_method", ""),
            http_path=sym.get("http_path", "")
        ))
        symbols.append(sym)
    return symbols

def _scan_and_record_security(repo_id: int, rel_p: str, content: str, lang: str, db: Session) -> List[Dict[str, Any]]:
    """Runs secret, AST bandit, and manifest CVE vulnerability scanners."""
    findings = []
    for sf in SecretScanner.scan_file(content, rel_p):
        db.add(SecurityFinding(
            repo_id=repo_id, file_path=sf["file_path"], line_number=sf["line_number"],
            severity=sf["severity"], category=sf["category"], rule_id=sf["rule_id"],
            description=sf["description"], code_snippet=sf["code_snippet"], remediation=sf["remediation"]
        ))
        findings.append(sf)

    if lang == "python":
        for bf in BanditScanner.scan_python_content(content, rel_p):
            db.add(SecurityFinding(
                repo_id=repo_id, file_path=bf["file_path"], line_number=bf["line_number"],
                severity=bf["severity"], category=bf["category"], rule_id=bf["rule_id"],
                description=bf["description"], code_snippet=bf["code_snippet"], remediation=bf["remediation"]
            ))
            findings.append(bf)

    if any(k in rel_p.lower() for k in ("requirements", "package.json")):
        for df in DependencyRiskAnalyzer.scan_manifest(content, rel_p):
            db.add(SecurityFinding(
                repo_id=repo_id, file_path=df["file"], line_number=df["line"], severity=df["severity"],
                category="VULNERABLE_DEPENDENCY", rule_id=df["vulnerability_id"], description=df["description"],
                code_snippet=f"{df['package']}=={df['installed_version']}", remediation=f"Upgrade to {df['recommended_version']}"
            ))
            findings.append(df)
    return findings

def _process_single_file(repo_id: int, entry: Dict[str, Any], repo_root: Path, db: Session, acc: Dict[str, Any]):
    """Processes an individual source file across AST, symbols, security, and chunking."""
    rel_p = entry["rel_path"].replace("\\", "/")
    lang = detect_language(rel_p)
    acc["lang_counts"][lang] = acc["lang_counts"].get(lang, 0) + 1

    try:
        content = (repo_root / rel_p).read_text(encoding="utf-8", errors="replace")
    except Exception:
        content = ""

    ast_data = ASTParser.parse_file(rel_p, str(repo_root))
    acc["parsed_files"].append(ast_data)

    db.add(FileRecord(
        repo_id=repo_id, path=rel_p, language=lang, size_bytes=entry["size_bytes"],
        lines_of_code=entry["lines_of_code"], cyclomatic_complexity=ast_data.get("cyclomatic_complexity", 1.0),
        maintainability_index=ast_data.get("maintainability_index", 100.0), has_tests="test" in rel_p.lower(),
        ast_summary=json.dumps({"symbols_count": len(ast_data.get("symbols", []))})
    ))

    acc["all_symbols"].extend(_record_file_symbols(repo_id, rel_p, ast_data, db))
    acc["all_findings"].extend(_scan_and_record_security(repo_id, rel_p, content, lang, db))
    acc["all_chunks"].extend(CodeChunker.chunk_file(content, rel_p, ast_data))

def _persist_dependency_graph(repo_id: int, parsed_files: List[Dict[str, Any]], db: Session):
    """Builds and commits dependency graph edges."""
    builder = DependencyGraphBuilder()
    graph = builder.build_graph(parsed_files)
    for u, v, data in graph.edges(data=True):
        db.add(DependencyEdge(repo_id=repo_id, source_file=u, target_file=v, dependency_type=data.get("edge_type", "import")))
    db.commit()

def _index_vector_chunks(repo_id: int, all_chunks: List[Dict[str, Any]]):
    """Generates dense vector embeddings and stores in Qdrant collection."""
    if all_chunks:
        chunk_texts = [f"{c.get('context_header', '')}\n{c.get('content', '')}" for c in all_chunks]
        vectors = embedder.embed_texts(chunk_texts)
        vector_store.upsert_chunks(repo_id, all_chunks, vectors)

def _calculate_health_score(debt_hours: float, findings: List[Dict[str, Any]]) -> float:
    """Calculates overall repository health score percentage (10-100%)."""
    critical_sec = sum(1 for f in findings if f.get("severity") in ("CRITICAL", "HIGH"))
    debt_penalty = min(35.0, debt_hours * 0.5)
    sec_penalty = min(40.0, critical_sec * 8.0)
    return max(10.0, round(100.0 - debt_penalty - sec_penalty, 1))

class AnalysisService:
    """Coordinates deep repository inspection and intelligence indexing."""

    @classmethod
    def index_repository(cls, repo_id: int, db: Session) -> Dict[str, Any]:
        """Orchestrates complete indexing pipeline for target repository."""
        repo = db.query(Repository).filter(Repository.id == repo_id).first()
        if not repo:
            raise ValueError(f"Repository with ID {repo_id} not found.")

        repo.indexing_status = "indexing"
        db.commit()

        _purge_existing_data(repo_id, db)
        repo_root = Path(repo.local_path)
        file_entries = RepoService.list_repository_files(str(repo_root))

        acc = {"parsed_files": [], "all_chunks": [], "all_symbols": [], "all_findings": [], "lang_counts": {}}
        for entry in file_entries:
            _process_single_file(repo_id, entry, repo_root, db, acc)
        db.commit()

        _persist_dependency_graph(repo_id, acc["parsed_files"], db)
        _index_vector_chunks(repo_id, acc["all_chunks"])

        debt_report = TechDebtAnalyzer.analyze_repository(acc["parsed_files"])
        primary_lang = max(acc["lang_counts"].items(), key=lambda x: x[1])[0].capitalize() if acc["lang_counts"] else "Python"
        health_score = _calculate_health_score(debt_report["total_debt_hours"], acc["all_findings"])

        repo.primary_language = primary_lang
        repo.total_files = len(file_entries)
        repo.total_lines = sum(e["lines_of_code"] for e in file_entries)
        repo.health_score = health_score
        repo.is_indexed = True
        repo.indexing_status = "completed"
        db.commit()

        return {
            "repo_id": repo_id,
            "status": "completed",
            "total_files": len(file_entries),
            "total_lines": repo.total_lines,
            "symbols_extracted": len(acc["all_symbols"]),
            "health_score": health_score,
            "security_findings_count": len(acc["all_findings"]),
            "debt_hours": debt_report["total_debt_hours"],
            "primary_language": primary_lang
        }
