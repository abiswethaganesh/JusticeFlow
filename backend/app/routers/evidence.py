import os
import uuid
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.case_evidence import CaseEvidence
from app.schemas.complaint import CaseEvidenceResponse

router = APIRouter(prefix="/evidence", tags=["evidence"])

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/upload", response_model=CaseEvidenceResponse)
async def upload_evidence(
    case_id: str = Form(...),
    evidence_type: str = Form("document"),
    title: str = Form("Evidence Document"),
    description: str = Form(""),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file selected for upload.")

    ext = os.path.splitext(file.filename)[1]
    filename = f"{uuid.uuid4().hex[:12]}{ext}"
    file_path = os.path.join(UPLOAD_DIR, filename)

    contents = await file.read()
    with open(file_path, "wb") as f:
        f.write(contents)

    file_url = f"/uploads/{filename}"

    evidence = CaseEvidence(
        case_id=case_id,
        evidence_type=evidence_type,
        title=title or file.filename,
        file_path=file_path,
        file_url=file_url,
        description=description,
    )
    db.add(evidence)
    db.commit()
    db.refresh(evidence)

    return evidence


@router.delete("/{evidence_id}")
def delete_evidence(
    evidence_id: int,
    db: Session = Depends(get_db),
):
    ev = db.query(CaseEvidence).filter(CaseEvidence.id == evidence_id).first()
    if not ev:
        raise HTTPException(status_code=404, detail=f"No evidence found with ID {evidence_id}.")

    if ev.file_path and os.path.exists(ev.file_path):
        try:
            os.remove(ev.file_path)
        except Exception:
            pass

    db.delete(ev)
    db.commit()
    return {"message": "Evidence deleted successfully", "evidence_id": evidence_id}
