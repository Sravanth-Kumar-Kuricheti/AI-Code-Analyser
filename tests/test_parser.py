import pytest
from code_engine.parser.ast_parser import ASTParser, detect_language
from code_engine.parser.chunker import CodeChunker

def test_detect_language():
    assert detect_language("backend/main.py") == "python"
    assert detect_language("frontend/index.ts") == "typescript"
    assert detect_language("Dockerfile") == "dockerfile"
    assert detect_language("unknown.xyz") == "text"

def _assert_parsed_structure(parsed):
    assert parsed["language"] == "python"
    assert len(parsed["imports"]) >= 2
    assert len(parsed["symbols"]) >= 3

def _assert_parsed_symbols(symbols_by_name):
    assert "UserService" in symbols_by_name
    assert symbols_by_name["UserService"]["symbol_type"] == "class"
    assert "UserService.get_user" in symbols_by_name
    assert symbols_by_name["UserService.get_user"]["symbol_type"] == "method"
    assert symbols_by_name["UserService.get_user"]["docstring"] == "Fetch user by identifier."

def test_parse_python_ast():
    sample_code = """
import os
from pathlib import Path

class UserService:
    def __init__(self, db):
        self.db = db

    def get_user(self, user_id: int):
        '''Fetch user by identifier.'''
        if user_id <= 0:
            raise ValueError("Invalid user_id")
        return {"id": user_id, "name": "Alice"}
"""
    parsed = ASTParser.parse_python_file(sample_code, "test_service.py")
    _assert_parsed_structure(parsed)
    symbols_by_name = {s["name"]: s for s in parsed["symbols"]}
    _assert_parsed_symbols(symbols_by_name)
    assert symbols_by_name["UserService.get_user"]["complexity"] >= 2

def test_code_chunker():
    sample_code = """
def alpha():
    return 1

def beta():
    return 2
"""
    chunks = CodeChunker.chunk_file(sample_code, "math.py")
    assert len(chunks) >= 2
    chunk_symbols = [c["symbol_name"] for c in chunks]
    assert "alpha" in chunk_symbols
    assert "beta" in chunk_symbols
