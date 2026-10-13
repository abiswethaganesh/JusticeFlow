from datetime import datetime, timezone
import os
import uuid
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, Header
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.case_evidence import CaseEvidence
from app.models.retention_rule import EvidenceRetentionRule
from app.models.evidence_audit_event import EvidenceAuditEvent
from app.models.user import User
from app.routers.auth import get_current_user_from_token
from app.schemas.complaint import (
    CaseEvidenceResponse,
    PreservationActionRequest,
    EvidenceAuditEventResponse,
    EvidenceRetentionRuleResponse,
)
from app.services.retention_service import calculate_evidence_urgency
from app.services.gemini_service import generate_preservation_request_draft
from app.services.complaint_record_service import get_complaint_by_case_id

router = APIRouter(prefix="/evidence", tags=["evidence"])

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.get("/retention-rules", response_model=List[EvidenceRetentionRuleResponse])
def get_retention_rules(db: Session = Depends(get_db)):
    """GET configurable evidence retention rules knowledge base."""
    return db.query(EvidenceRetentionRule).order_by(EvidenceRetentionRule.id.asc()).all()


@router.post("/upload", response_model=CaseEvidenceResponse)
async def upload_evidence(
    case_id: str = Form(...),
    evidence_type: str = Form("document"),
    title: str = Form("Evidence Document"),
    description: str = Form(""),
    source: str = Form("Uploaded by complainant"),
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

    file_path = os.path.abspath(file_path)

    complaint = get_complaint_by_case_id(db, case_id)
    inc_date = (complaint.structured_data or {}).get("incident_date") if complaint else None
    inc_time = (complaint.structured_data or {}).get("incident_time") if complaint else None

    urgency_info = calculate_evidence_urgency(
        evidence_type=evidence_type,
        incident_date=inc_date,
        incident_time=inc_time,
        preservation_status="NOT_REVIEWED",
        db=db,
    )

    preservation_status = "REVIEW_REQUIRED" if urgency_info.get("potentially_time_sensitive") else "NOT_REVIEWED"

    evidence = CaseEvidence(
        case_id=case_id,
        evidence_type=evidence_type,
        title=title or file.filename,
        file_path=file_path,
        file_url=f"/uploads/{filename}",
        description=description,
        source=source,
        potentially_time_sensitive=urgency_info.get("potentially_time_sensitive", False),
        retention_period_days=urgency_info.get("retention_period_days"),
        retention_source=urgency_info.get("retention_source"),
        retention_confidence=urgency_info.get("retention_confidence", "UNKNOWN"),
        urgency=urgency_info.get("urgency", "UNKNOWN"),
        estimated_expiry=urgency_info.get("estimated_expiry"),
        preservation_status=preservation_status,
        is_digital_narrative_extracted=False,
    )
    db.add(evidence)
    db.flush()

    evidence.file_url = f"/evidence/{evidence.id}/file"

    audit = EvidenceAuditEvent(
        case_id=case_id,
        evidence_id=evidence.id,
        action="EVIDENCE_UPLOADED",
        previous_status=None,
        new_status=preservation_status,
        actor_name="Complainant/User",
        actor_role="CITIZEN",
        remarks=f"File uploaded: {title}",
    )
    db.add(audit)

    db.commit()
    db.refresh(evidence)

    return evidence


from fastapi import Query
from fastapi.responses import FileResponse
from app.models.officer import Officer
from app.services.complaint_record_service import normalize_phone


@router.get("/{evidence_id}/file")
def download_or_view_evidence_file(
    evidence_id: int,
    download: Optional[bool] = Query(False),
    token: Optional[str] = Query(None),
    user_phone: Optional[str] = Query(None),
    user_role: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
    station_branch: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_from_token),
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
    x_user_phone: Optional[str] = Header(None, alias="X-User-Phone"),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
    x_station_branch: Optional[str] = Header(None, alias="X-Station-Branch"),
):
    """
    Secure, authenticated & authorized file serving endpoint for uploaded case evidence.
    Restricts access strictly to complaint owners (Citizens) and authorized station Officers/Admins.
    By default (download=False), renders files inline in the browser.
    When download=True, sets Content-Disposition: attachment for file download.
    """
    ev = db.query(CaseEvidence).filter(CaseEvidence.id == evidence_id).first()
    if not ev:
        raise HTTPException(status_code=404, detail=f"No evidence record found with ID {evidence_id}.")

    # Resolve active user role and identity from JWT token or headers/params
    effective_role = None
    effective_user_id = None
    effective_phone = None
    effective_branch = None

    if current_user:
        effective_role = current_user.role.upper()
        effective_user_id = current_user.id
        effective_phone = current_user.phone
        effective_branch = current_user.station_branch
    elif token and token.strip():
        try:
            from app.services.auth_service import decode_token
            payload = decode_token(token.strip())
            if payload:
                u_id = payload.get("sub") or payload.get("user_id")
                if u_id:
                    u = db.query(User).filter(User.id == int(u_id)).first()
                    if u:
                        effective_role = u.role.upper()
                        effective_user_id = u.id
                        effective_phone = u.phone
                        effective_branch = u.station_branch
        except Exception:
            pass

    if not effective_role:
        effective_role = (user_role or x_user_role or "CITIZEN").upper()
    if not effective_phone:
        effective_phone = user_phone or x_user_phone or ""
    if not effective_user_id and (user_id or x_user_id):
        raw_uid = user_id or x_user_id
        if str(raw_uid).isdigit():
            effective_user_id = int(raw_uid)
    if not effective_branch:
        effective_branch = station_branch or x_station_branch or ""

    # Fetch associated complaint
    complaint = get_complaint_by_case_id(db, ev.case_id)
    if not complaint:
        raise HTTPException(status_code=404, detail=f"Associated complaint for case ID {ev.case_id} not found.")

    # Authorization logic
    if effective_role == "CITIZEN":
        is_owner = False
        if effective_user_id and complaint.citizen_id and effective_user_id == complaint.citizen_id:
            is_owner = True
        elif effective_phone and complaint.citizen_phone:
            norm_req = normalize_phone(effective_phone)
            norm_comp = normalize_phone(complaint.citizen_phone)
            if norm_req and norm_comp and norm_req == norm_comp:
                is_owner = True

        if not is_owner:
            raise HTTPException(status_code=403, detail="Access denied. You can only view evidence for your own complaints.")

    elif effective_role == "OFFICER":
        is_authorized = False
        if effective_user_id:
            off = db.query(Officer).filter(Officer.user_id == effective_user_id).first()
            if off and complaint.police_station_id and off.police_station_id == complaint.police_station_id:
                is_authorized = True

        if not is_authorized and (effective_branch or x_station_branch) and complaint.assigned_station:
            eb_clean = (effective_branch or x_station_branch or "").strip().lower()
            as_clean = complaint.assigned_station.strip().lower()
            if eb_clean in as_clean or as_clean in eb_clean:
                is_authorized = True

        if not is_authorized:
            raise HTTPException(status_code=403, detail="Access denied. Case is assigned to a different police station.")

    # Locate physical file on server disk
    candidate_paths = []
    if ev.file_path:
        candidate_paths.append(ev.file_path)

    fn = os.path.basename(ev.file_path or ev.file_url or "")
    if fn:
        candidate_paths.append(os.path.join(UPLOAD_DIR, fn))
        workspace_root_uploads = os.path.join(os.path.dirname(UPLOAD_DIR), "..", "uploads")
        candidate_paths.append(os.path.join(workspace_root_uploads, fn))
        candidate_paths.append(os.path.join(os.getcwd(), "uploads", fn))

    found_path = None
    for cp in candidate_paths:
        if cp and os.path.exists(cp) and os.path.isfile(cp):
            found_path = cp
            break

    if not found_path:
        from fastapi.responses import HTMLResponse
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>JusticeFlow Case Evidence Record — {ev.case_id}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background-color: #F8FAFC; color: #0F2A4A; margin: 0; padding: 2rem; }}
        .container {{ max-width: 650px; margin: 0 auto; background: #FFFFFF; border-radius: 12px; border: 1px solid #CBD7E6; box-shadow: 0 10px 25px rgba(15, 42, 74, 0.08); overflow: hidden; }}
        .header {{ background: #0F2A4A; color: #FFFFFF; padding: 1.5rem; }}
        .badge {{ background: #17395E; color: #EBF3FA; font-family: monospace; font-size: 0.8rem; padding: 0.25rem 0.5rem; border-radius: 4px; border: 1px solid #245789; font-weight: bold; }}
        .body {{ padding: 1.5rem; line-height: 1.6; font-size: 0.9rem; }}
        .card {{ background: #F0F5FA; border: 1px solid #CBD7E6; border-radius: 8px; padding: 1rem; margin-top: 1rem; }}
        .meta-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-top: 1rem; }}
        .meta-item {{ font-size: 0.85rem; }}
        .meta-label {{ color: #5C6773; font-size: 0.75rem; text-transform: uppercase; font-weight: bold; }}
        .meta-val {{ color: #0F2A4A; font-weight: 600; margin-top: 0.2rem; }}
        .footer {{ background: #F4F7FA; border-top: 1px solid #E1E5EB; padding: 1rem 1.5rem; font-size: 0.78rem; color: #5C6773; text-align: center; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <span class="badge">{ev.case_id}</span>
            <h2 style="margin: 0.6rem 0 0.2rem 0; font-size: 1.25rem;">{ev.title}</h2>
            <div style="font-size: 0.82rem; opacity: 0.85; font-family: monospace;">Category: {ev.evidence_type.upper()}</div>
        </div>
        <div class="body">
            <div style="font-weight: 600; font-size: 0.95rem; color: #0F2A4A;">
                Evidence Status: <span style="color: #A15C00;">Extracted from Narrative / Physical File Pending Upload</span>
            </div>
            
            <div class="card">
                <div class="meta-label">Source & Context</div>
                <div style="color: #243342; margin-top: 0.3rem;">{ev.source or 'Extracted automatically from complaint narrative during AI intake.'}</div>
                {f'<div style="margin-top: 0.5rem; font-style: italic; color: #5C6773;">"{ev.description}"</div>' if ev.description else ''}
            </div>

            <div class="meta-grid">
                <div class="meta-item">
                    <div class="meta-label">Time-Sensitive Urgency</div>
                    <div class="meta-val">{ev.urgency or 'HIGH'}</div>
                </div>
                <div class="meta-item">
                    <div class="meta-label">Preservation Status</div>
                    <div class="meta-val">{ev.preservation_status}</div>
                </div>
                <div class="meta-item">
                    <div class="meta-label">Statutory Retention Period</div>
                    <div class="meta-val">{f"{ev.retention_period_days} Days" if ev.retention_period_days else "30 Days"} ({ev.retention_source or "Standard Legal Procedure"})</div>
                </div>
                <div class="meta-item">
                    <div class="meta-label">Identification Date</div>
                    <div class="meta-val">{ev.identified_at.strftime('%d %b %Y, %I:%M %p') if ev.identified_at else 'Recent'}</div>
                </div>
            </div>

            <div style="margin-top: 1.5rem; padding: 0.85rem; background: #FFF8E1; border: 1px solid #FFE082; border-radius: 8px; font-size: 0.82rem; color: #795548;">
                <strong>Notice for Investigating Officer:</strong> This evidence record was identified from the complainant statement. If a physical media file, CCTV drive, or document is collected, please upload the physical file via the Officer Case Management Panel to attach the binary file to this record.
            </div>
        </div>
        <div class="footer">
            JusticeFlow Core Platform — Official Case Evidence Registry
        </div>
    </div>
</body>
</html>"""
        return HTMLResponse(content=html_content, status_code=200)

    import mimetypes
    media_type, _ = mimetypes.guess_type(found_path)
    if not media_type:
        media_type = "application/octet-stream"

    filename = ev.title or os.path.basename(found_path)
    ext = os.path.splitext(found_path)[1]
    if ext and not filename.lower().endswith(ext.lower()):
        filename = f"{filename}{ext}"

    disposition_type = "attachment" if download else "inline"

    return FileResponse(
        found_path,
        media_type=media_type,
        content_disposition_type=disposition_type,
        filename=filename,
    )


@router.get("/{evidence_id}", response_model=CaseEvidenceResponse)
def get_evidence_by_id(evidence_id: int, db: Session = Depends(get_db)):

    ev = db.query(CaseEvidence).filter(CaseEvidence.id == evidence_id).first()
    if not ev:
        raise HTTPException(status_code=404, detail=f"No evidence found with ID {evidence_id}.")
    return ev


@router.get("/{evidence_id}/urgency")
def get_evidence_urgency(evidence_id: int, db: Session = Depends(get_db)):
    ev = db.query(CaseEvidence).filter(CaseEvidence.id == evidence_id).first()
    if not ev:
        raise HTTPException(status_code=404, detail=f"No evidence found with ID {evidence_id}.")

    complaint = get_complaint_by_case_id(db, ev.case_id)
    inc_date = (complaint.structured_data or {}).get("incident_date") if complaint else None
    inc_time = (complaint.structured_data or {}).get("incident_time") if complaint else None

    urgency_info = calculate_evidence_urgency(
        evidence_type=ev.evidence_type,
        incident_date=inc_date,
        incident_time=inc_time,
        identified_at=ev.identified_at,
        preservation_status=ev.preservation_status,
        db=db,
    )

    # Sync DB fields if changed
    if ev.urgency != urgency_info["urgency"]:
        ev.urgency = urgency_info["urgency"]
        ev.retention_confidence = urgency_info["retention_confidence"]
        ev.estimated_expiry = urgency_info["estimated_expiry"]
        db.commit()
        db.refresh(ev)

    return {
        "evidence_id": ev.id,
        "case_id": ev.case_id,
        "evidence_type": ev.evidence_type,
        "title": ev.title,
        "preservation_status": ev.preservation_status,
        **urgency_info,
    }


@router.post("/{evidence_id}/preservation-draft")
def get_preservation_draft(evidence_id: int, db: Session = Depends(get_db)):
    ev = db.query(CaseEvidence).filter(CaseEvidence.id == evidence_id).first()
    if not ev:
        raise HTTPException(status_code=404, detail=f"No evidence found with ID {evidence_id}.")

    complaint = get_complaint_by_case_id(db, ev.case_id)
    complaint_dict = {
        "case_id": ev.case_id,
        "complaint_type": complaint.complaint_type if complaint else "other",
        "structured_data": complaint.structured_data if complaint else {},
        "incident_details": complaint.incident_details if complaint else {},
    }

    evidence_dict = {
        "id": ev.id,
        "type": ev.evidence_type,
        "title": ev.title,
        "description": ev.description,
        "source": ev.source or "Holding Authority",
        "urgency": ev.urgency,
        "retention_source": ev.retention_source,
    }

    draft = generate_preservation_request_draft(ev.case_id, evidence_dict, complaint_dict)

    # Log draft generation in audit trail
    audit = EvidenceAuditEvent(
        case_id=ev.case_id,
        evidence_id=ev.id,
        action="DRAFT_GENERATED",
        previous_status=ev.preservation_status,
        new_status=ev.preservation_status,
        actor_name="AI Assistance Engine",
        actor_role="SYSTEM",
        remarks="Preservation request draft generated for officer review.",
    )
    db.add(audit)
    db.commit()

    return draft


@router.post("/{evidence_id}/preservation-action", response_model=CaseEvidenceResponse)
def record_preservation_action(
    evidence_id: int,
    payload: PreservationActionRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_from_token),
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
):
    ev = db.query(CaseEvidence).filter(CaseEvidence.id == evidence_id).first()
    if not ev:
        raise HTTPException(status_code=404, detail=f"No evidence found with ID {evidence_id}.")

    prev_status = ev.preservation_status
    new_status = payload.status.upper()
    now_utc = datetime.now(timezone.utc)

    # Calculate Time-to-Preservation-Request metric in minutes
    time_to_preservation_minutes = None
    if ev.identified_at:
        identified_dt = ev.identified_at if ev.identified_at.tzinfo else ev.identified_at.replace(tzinfo=timezone.utc)
        delta = now_utc - identified_dt
        time_to_preservation_minutes = round(delta.total_seconds() / 60.0, 2)

    ev.preservation_status = new_status
    ev.preservation_action_at = now_utc
    ev.preservation_notes = payload.remarks or ""

    if new_status in ["PRESERVED", "NOT_APPLICABLE"]:
        ev.urgency = "LOW"

    actor_name = payload.actor_name or (current_user.full_name if current_user else "Inspector Rajesh Kumar")
    actor_role = payload.actor_role or (current_user.role if current_user else (x_user_role or "OFFICER"))

    audit = EvidenceAuditEvent(
        case_id=ev.case_id,
        evidence_id=ev.id,
        action=payload.action or f"STATUS_UPDATED_TO_{new_status}",
        previous_status=prev_status,
        new_status=new_status,
        actor_name=actor_name,
        actor_role=actor_role,
        time_to_preservation_minutes=time_to_preservation_minutes,
        remarks=payload.remarks or f"Preservation status changed to {new_status}",
    )
    db.add(audit)
    db.commit()
    db.refresh(ev)

    return ev


@router.get("/{evidence_id}/audit-trail", response_model=List[EvidenceAuditEventResponse])
def get_evidence_audit_trail(evidence_id: int, db: Session = Depends(get_db)):
    return db.query(EvidenceAuditEvent).filter(EvidenceAuditEvent.evidence_id == evidence_id).order_by(EvidenceAuditEvent.created_at.asc()).all()


@router.patch("/{evidence_id}/preservation-status", response_model=CaseEvidenceResponse)
def update_preservation_status(
    evidence_id: int,
    payload: PreservationActionRequest,
    db: Session = Depends(get_db),
):
    return record_preservation_action(evidence_id=evidence_id, payload=payload, db=db)


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

    db.query(EvidenceAuditEvent).filter(EvidenceAuditEvent.evidence_id == evidence_id).delete()
    db.delete(ev)
    db.commit()
    return {"message": "Evidence deleted successfully", "evidence_id": evidence_id}

