import pytest
from code_engine.analyzer.tech_debt_analyzer import TechDebtAnalyzer

def test_tech_debt_analyzer():
    files_ast = [
        {
            "rel_path": "legacy.py",
            "lines_of_code": 300,
            "maintainability_index": 42.0,
            "symbols": [
                {
                    "name": "huge_routine",
                    "symbol_type": "function",
                    "line_start": 1,
                    "line_end": 85, # > 50 lines
                    "complexity": 12, # > 8 complexity
                    "docstring": ""
                }
            ]
        }
    ]

    report = TechDebtAnalyzer.analyze_repository(files_ast)
    assert report["total_debt_hours"] > 0
    assert len(report["long_functions"]) == 1
    assert len(report["complex_methods"]) == 1
    assert report["long_functions"][0]["name"] == "huge_routine"
