from typing import List, Dict, Any, Tuple, Set
from code_engine.parser.ast_parser import ASTParser, detect_language

def _chunk_symbols(lines: List[str], symbols: List[Dict[str, Any]], rel_path: str, lang: str) -> Tuple[List[Dict[str, Any]], Set[int]]:
    """Chunks source code lines based on parsed AST symbol boundaries."""
    chunks = []
    covered = set()
    for sym in symbols:
        s_line = max(1, sym.get("line_start", 1))
        e_line = min(len(lines), sym.get("line_end", s_line + 10))
        chunk_text = "\n".join(lines[s_line - 1:e_line])
        if chunk_text.strip():
            chunks.append({
                "file_path": rel_path,
                "symbol_name": sym.get("name", ""),
                "symbol_type": sym.get("symbol_type", "block"),
                "start_line": s_line,
                "end_line": e_line,
                "language": lang,
                "signature": sym.get("signature", ""),
                "content": chunk_text,
                "context_header": f"File: {rel_path} | {sym.get('symbol_type', 'symbol').title()}: {sym.get('name', '')} (Lines {s_line}-{e_line})"
            })
            covered.update(range(s_line, e_line + 1))
    return chunks, covered

def _chunk_sliding_windows(lines: List[str], covered: Set[int], rel_path: str, lang: str, has_symbols: bool) -> List[Dict[str, Any]]:
    """Chunks uncovered lines in sliding windows."""
    chunks = []
    window_size, overlap = 40, 5
    curr, total = 0, len(lines)
    while curr < total:
        end = min(total, curr + window_size)
        window_lines = set(range(curr + 1, end + 1))
        uncovered = window_lines - covered
        if len(uncovered) > 5 or not has_symbols:
            chunk_text = "\n".join(lines[curr:end])
            if chunk_text.strip():
                chunks.append({
                    "file_path": rel_path,
                    "symbol_name": "module_scope",
                    "symbol_type": "file_section",
                    "start_line": curr + 1,
                    "end_line": end,
                    "language": lang,
                    "signature": "",
                    "content": chunk_text,
                    "context_header": f"File: {rel_path} (Lines {curr + 1}-{end})"
                })
        curr += (window_size - overlap)
    return chunks

class CodeChunker:
    """AST-aware chunker dividing code files into semantic chunks with line citations."""

    @classmethod
    def chunk_file(cls, content: str, rel_path: str, parsed_ast: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Splits file content into AST symbol chunks and overlapping windows."""
        if not parsed_ast:
            language = detect_language(rel_path)
            if language == "python":
                parsed_ast = ASTParser.parse_python_file(content, rel_path)
            else:
                parsed_ast = ASTParser.parse_generic_file(content, rel_path, language)

        lines = content.splitlines()
        lang = parsed_ast.get("language", "text")
        symbols = parsed_ast.get("symbols", [])

        sym_chunks, covered = _chunk_symbols(lines, symbols, rel_path, lang)
        win_chunks = _chunk_sliding_windows(lines, covered, rel_path, lang, bool(symbols))
        return sym_chunks + win_chunks
