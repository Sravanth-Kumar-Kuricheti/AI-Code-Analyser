import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from backend.models.database import get_db
from backend.models.schemas import Repository, ChatMessage
from backend.schemas.pydantic_models import (
    ChatRequest, ChatResponse, CitationItem, ExplainRequest, BugInvestigationRequest
)
from ai_engine.retrieval.rag_engine import RAGEngine
from ai_engine.llm.client import llm_client
from ai_engine.prompts.system_prompts import (
    CODEBASE_QA_SYSTEM_PROMPT, CODE_EXPLANATION_PROMPT, BUG_INVESTIGATION_PROMPT
)

router = APIRouter(prefix="/chat", tags=["AI Code Chat"])

@router.post("/qa", response_model=ChatResponse)
def ask_codebase_question(payload: ChatRequest, db: Session = Depends(get_db)):
    repo = db.query(Repository).filter(Repository.id == payload.repo_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    # 1. RAG retrieval
    retrieval_data = RAGEngine.retrieve_context(payload.repo_id, payload.query, top_k=5)
    context_text = retrieval_data["context_text"]
    citations_data = retrieval_data["citations"]

    # 2. Build Prompt
    user_prompt = (
        f"User Question: {payload.query}\n\n"
        f"Relevant Code Context:\n"
        f"{context_text if context_text else 'No specific code snippets matched query.'}\n\n"
        f"Please provide an accurate answer citing relevant file paths and line ranges."
    )

    answer_text = llm_client.generate(CODEBASE_QA_SYSTEM_PROMPT, user_prompt)

    # 3. Save to Conversation History
    user_msg = ChatMessage(repo_id=payload.repo_id, role="user", content=payload.query, citations="[]")
    bot_msg = ChatMessage(
        repo_id=payload.repo_id,
        role="assistant",
        content=answer_text,
        citations=json.dumps(citations_data)
    )
    db.add(user_msg)
    db.add(bot_msg)
    db.commit()

    return ChatResponse(
        answer=answer_text,
        citations=[CitationItem(**c) for c in citations_data]
    )

@router.post("/explain")
def explain_code_symbol(payload: ExplainRequest, db: Session = Depends(get_db)):
    user_prompt = f"File: {payload.file_path}\n"
    if payload.symbol_name:
        user_prompt += f"Symbol Name: {payload.symbol_name}\n"
    if payload.code_snippet:
        user_prompt += f"Source Code:\n{payload.code_snippet}\n"

    explanation = llm_client.generate(CODE_EXPLANATION_PROMPT, user_prompt)
    return {
        "file_path": payload.file_path,
        "symbol_name": payload.symbol_name,
        "explanation": explanation
    }

@router.post("/bug-investigate")
def investigate_bug(payload: BugInvestigationRequest, db: Session = Depends(get_db)):
    # Retrieve context based on error message or stack trace
    search_query = f"{payload.error_message} {payload.stack_trace or ''}"[:200]
    retrieval_data = RAGEngine.retrieve_context(payload.repo_id, search_query, top_k=4)
    
    user_prompt = (
        f"Error Message: {payload.error_message}\n"
        f"Stack Trace:\n{payload.stack_trace or 'None provided'}\n\n"
        f"Codebase Context:\n{retrieval_data['context_text']}"
    )

    analysis = llm_client.generate(BUG_INVESTIGATION_PROMPT, user_prompt)
    return {
        "error_message": payload.error_message,
        "root_cause_analysis": analysis,
        "citations": retrieval_data["citations"]
    }

@router.get("/history/{repo_id}")
def get_chat_history(repo_id: int, db: Session = Depends(get_db)):
    messages = db.query(ChatMessage).filter(
        ChatMessage.repo_id == repo_id
    ).order_by(ChatMessage.created_at.asc()).all()

    return [
        {
            "id": m.id,
            "role": m.role,
            "content": m.content,
            "citations": json.loads(m.citations or "[]"),
            "created_at": m.created_at
        }
        for m in messages
    ]

# Compatibility alias
ask_codebase_qa = ask_codebase_question
