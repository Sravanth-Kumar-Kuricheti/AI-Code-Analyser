from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime

class RepoConnectRequest(BaseModel):
    url_or_path: str = Field(..., description="GitHub repository URL or local folder path")
    branch: Optional[str] = Field("main", description="Target Git branch")
    name: Optional[str] = Field(None, description="Optional custom repository name")

class RepoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    full_name: str
    url: str
    local_path: str
    default_branch: str
    primary_language: str
    total_files: int
    total_lines: int
    health_score: float
    is_indexed: bool
    indexing_status: str
    created_at: datetime

class SymbolResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    symbol_type: str
    file_path: str
    line_start: int
    line_end: int
    signature: str
    docstring: str
    complexity: int
    is_api_endpoint: bool
    http_method: Optional[str] = None
    http_path: Optional[str] = None

class FileDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    path: str
    language: str
    lines_of_code: int
    cyclomatic_complexity: float
    maintainability_index: float
    content: Optional[str] = None
    symbols: List[SymbolResponse] = []

class ChatRequest(BaseModel):
    repo_id: int
    query: str
    include_citations: bool = True

class CitationItem(BaseModel):
    file: str
    start_line: int
    end_line: int
    symbol: str
    citation: str
    preview: str

class ChatResponse(BaseModel):
    answer: str
    citations: List[CitationItem] = []
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ExplainRequest(BaseModel):
    repo_id: int
    file_path: str
    symbol_name: Optional[str] = None
    code_snippet: Optional[str] = None

class BugInvestigationRequest(BaseModel):
    repo_id: int
    error_message: str
    stack_trace: Optional[str] = None
    related_file: Optional[str] = None

class ImpactRequest(BaseModel):
    repo_id: int
    target_file: str
    target_symbol: Optional[str] = ""

class TestGenerationRequest(BaseModel):
    repo_id: int
    file_path: str
    symbol_name: str
    framework: str = "pytest" # pytest or jest

class PRReviewRequest(BaseModel):
    repo_id: int
    diff_text: str
    title: Optional[str] = "Proposed Changes"

class ArchitectureDecisionRequest(BaseModel):
    repo_id: int
    proposed_change: str
    affected_components: Optional[List[str]] = []
