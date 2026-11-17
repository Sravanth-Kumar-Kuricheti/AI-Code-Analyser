from datetime import datetime
import json
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from backend.models.database import Base

class Repository(Base):
    __tablename__ = "repositories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), index=True, nullable=False)
    full_name = Column(String(255), unique=True, index=True, nullable=False)
    url = Column(String(512), nullable=False)
    local_path = Column(String(512), nullable=False)
    default_branch = Column(String(64), default="main")
    primary_language = Column(String(64), default="Unknown")
    total_files = Column(Integer, default=0)
    total_lines = Column(Integer, default=0)
    health_score = Column(Float, default=100.0) # 0 to 100
    is_indexed = Column(Boolean, default=False)
    indexing_status = Column(String(64), default="pending") # pending, indexing, completed, failed
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    files = relationship("FileRecord", back_populates="repository", cascade="all, delete-orphan")
    symbols = relationship("SymbolRecord", back_populates="repository", cascade="all, delete-orphan")
    findings = relationship("SecurityFinding", back_populates="repository", cascade="all, delete-orphan")
    dependencies = relationship("DependencyEdge", back_populates="repository", cascade="all, delete-orphan")
    chat_messages = relationship("ChatMessage", back_populates="repository", cascade="all, delete-orphan")


class FileRecord(Base):
    __tablename__ = "file_records"

    id = Column(Integer, primary_key=True, index=True)
    repo_id = Column(Integer, ForeignKey("repositories.id"), nullable=False, index=True)
    path = Column(String(512), nullable=False, index=True)
    language = Column(String(64), default="text")
    size_bytes = Column(Integer, default=0)
    lines_of_code = Column(Integer, default=0)
    cyclomatic_complexity = Column(Float, default=1.0)
    maintainability_index = Column(Float, default=100.0)
    has_tests = Column(Boolean, default=False)
    ast_summary = Column(Text, default="{}") # JSON of parsed entities

    repository = relationship("Repository", back_populates="files")


class SymbolRecord(Base):
    __tablename__ = "symbol_records"

    id = Column(Integer, primary_key=True, index=True)
    repo_id = Column(Integer, ForeignKey("repositories.id"), nullable=False, index=True)
    file_path = Column(String(512), nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)
    symbol_type = Column(String(64), nullable=False) # function, class, method, endpoint
    line_start = Column(Integer, nullable=False)
    line_end = Column(Integer, nullable=False)
    signature = Column(String(512), default="")
    docstring = Column(Text, default="")
    complexity = Column(Integer, default=1)
    is_api_endpoint = Column(Boolean, default=False)
    http_method = Column(String(16), default="")
    http_path = Column(String(255), default="")

    repository = relationship("Repository", back_populates="symbols")


class DependencyEdge(Base):
    __tablename__ = "dependency_edges"

    id = Column(Integer, primary_key=True, index=True)
    repo_id = Column(Integer, ForeignKey("repositories.id"), nullable=False, index=True)
    source_file = Column(String(512), nullable=False, index=True)
    target_file = Column(String(512), nullable=False, index=True)
    source_symbol = Column(String(255), default="")
    target_symbol = Column(String(255), default="")
    dependency_type = Column(String(64), default="import") # import, call, inherit

    repository = relationship("Repository", back_populates="dependencies")


class SecurityFinding(Base):
    __tablename__ = "security_findings"

    id = Column(Integer, primary_key=True, index=True)
    repo_id = Column(Integer, ForeignKey("repositories.id"), nullable=False, index=True)
    file_path = Column(String(512), nullable=False)
    line_number = Column(Integer, default=1)
    severity = Column(String(32), default="MEDIUM") # HIGH, MEDIUM, LOW, CRITICAL
    category = Column(String(64), default="VULNERABILITY") # SECRET, CODE_INJECTION, WEAK_CRYPTO, etc.
    rule_id = Column(String(64), default="")
    description = Column(Text, nullable=False)
    code_snippet = Column(Text, default="")
    remediation = Column(Text, default="")

    repository = relationship("Repository", back_populates="findings")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    repo_id = Column(Integer, ForeignKey("repositories.id"), nullable=False, index=True)
    role = Column(String(32), nullable=False) # user, assistant
    content = Column(Text, nullable=False)
    citations = Column(Text, default="[]") # JSON list of {file, lines, snippet}
    created_at = Column(DateTime, default=datetime.utcnow)

    repository = relationship("Repository", back_populates="chat_messages")
