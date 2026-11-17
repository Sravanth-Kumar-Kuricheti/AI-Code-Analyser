from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.models.database import get_db
from backend.models.schemas import Repository, SecurityFinding
from code_engine.security.license_checker import LicenseComplianceChecker

router = APIRouter(prefix="/security", tags=["Security Scanner"])

@router.get("/{repo_id}")
def get_security_audit(repo_id: int, db: Session = Depends(get_db)):
    repo = db.query(Repository).filter(Repository.id == repo_id).first()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    findings = db.query(SecurityFinding).filter(SecurityFinding.repo_id == repo_id).all()
    
    # Check license compliance
    license_info = LicenseComplianceChecker.detect_repository_license(repo.local_path)

    critical_count = sum(1 for f in findings if f.severity == "CRITICAL")
    high_count = sum(1 for f in findings if f.severity == "HIGH")
    medium_count = sum(1 for f in findings if f.severity == "MEDIUM")
    low_count = sum(1 for f in findings if f.severity == "LOW")

    return {
        "repo_id": repo_id,
        "repo_name": repo.name,
        "total_findings": len(findings),
        "critical_count": critical_count,
        "high_count": high_count,
        "medium_count": medium_count,
        "low_count": low_count,
        "license": license_info,
        "findings": [
            {
                "id": f.id,
                "file_path": f.file_path,
                "line_number": f.line_number,
                "severity": f.severity,
                "category": f.category,
                "rule_id": f.rule_id,
                "description": f.description,
                "code_snippet": f.code_snippet,
                "remediation": f.remediation
            }
            for f in findings
        ]
    }
