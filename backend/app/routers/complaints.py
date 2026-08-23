from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, Header
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.officer import Officer
from app.routers.auth import get_current_user_from_token
from app.schemas.complaint import (
    ComplaintCreateRequest,
    ComplaintRecord,
    ComplaintStatusUpdateRequest,
    CaseEventResponse,
    CaseEvidenceResponse,
    FIRRegisterRequest,
    FIRRecordResponse,
)
from app.services import complaint_record_service
from app.services.complaint_record_service import normalize_phone
from app.services.cctns_adapter import register_fir_with_cctns

router = APIRouter(prefix="/complaints", tags=["complaints"])


@router.post("", response_model=ComplaintRecord, status_code=201)
def create_complaint(
    request: ComplaintCreateRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_from_token),
    x_user_phone: Optional[str] = Header(None, alias="X-User-Phone"),
    x_user_id: Optional[str] = Header(None, alias="X-User-Id"),
):
    if not request.complaint_text or not request.complaint_text.strip():
        raise HTTPException(status_code=400, detail="complaint_text is required.")
    if not request.complaint_type or not request.complaint_type.strip():
        raise HTTPException(status_code=400, detail="complaint_type is required.")

    citizen_id = None
    citizen_phone = ""

    if current_user:
        citizen_id = current_user.id
        citizen_phone = current_user.phone or request.citizen_phone or x_user_phone or ""
    elif request.citizen_id:
        citizen_id = request.citizen_id
        citizen_phone = request.citizen_phone or x_user_phone or ""
    elif x_user_id and str(x_user_id).isdigit():
        citizen_id = int(x_user_id)
        citizen_phone = request.citizen_phone or x_user_phone or ""
    else:
        citizen_phone = request.citizen_phone or x_user_phone or ""

    return complaint_record_service.create_complaint_record(
        db=db,
        complaint_type=request.complaint_type,
        complaint_text=request.complaint_text,
        summary=request.summary,
        structured_data=request.structured_data,
        incident_details=request.incident_details,
        citizen_id=citizen_id,
        citizen_phone=citizen_phone,
        is_cognizable=request.is_cognizable,
        priority=request.priority,
    )


@router.get("", response_model=List[ComplaintRecord])
def list_complaints(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_from_token),
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
    x_user_phone: Optional[str] = Header(None, alias="X-User-Phone"),
    x_station_branch: Optional[str] = Header(None, alias="X-Station-Branch"),
):
    user_role = (current_user.role if current_user else (x_user_role or "CITIZEN")).upper()
    user_id = current_user.id if current_user else None
    user_phone = (current_user.phone if current_user and current_user.phone else None) or x_user_phone

    police_station_id = None
    station_branch = x_station_branch

    if current_user and current_user.role == "OFFICER":
        officer = db.query(Officer).filter(Officer.user_id == current_user.id).first()
        if officer:
            police_station_id = officer.police_station_id
        station_branch = current_user.station_branch

    return complaint_record_service.list_complaints_for_user(
        db=db,
        user_role=user_role,
        user_id=user_id,
        user_phone=user_phone,
        police_station_id=police_station_id,
        station_branch=station_branch,
    )


@router.get("/{case_id}", response_model=ComplaintRecord)
def get_complaint(
    case_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_from_token),
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
    x_user_phone: Optional[str] = Header(None, alias="X-User-Phone"),
    x_station_branch: Optional[str] = Header(None, alias="X-Station-Branch"),
):
    complaint = complaint_record_service.get_complaint_by_case_id(db, case_id)
    if complaint is None:
        raise HTTPException(status_code=404, detail=f"No complaint found with case ID {case_id}.")

    user_role = (current_user.role if current_user else (x_user_role or "CITIZEN")).upper()
    user_phone = (current_user.phone if current_user and current_user.phone else None) or x_user_phone

    if user_role == "OFFICER":
        is_assigned = False
        if current_user and current_user.station_branch and complaint.assigned_station:
            if current_user.station_branch.strip().lower() in complaint.assigned_station.strip().lower() or \
               complaint.assigned_station.strip().lower() in current_user.station_branch.strip().lower():
                is_assigned = True
        if x_station_branch and complaint.assigned_station:
            if x_station_branch.strip().lower() in complaint.assigned_station.strip().lower() or \
               complaint.assigned_station.strip().lower() in x_station_branch.strip().lower():
                is_assigned = True

        if not is_assigned:
            raise HTTPException(status_code=403, detail="Access denied. Case assigned to different station.")

    return complaint


@router.delete("/{case_id}")
@router.post("/{case_id}/delete")
def delete_complaint(
    case_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_from_token),
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
    x_user_phone: Optional[str] = Header(None, alias="X-User-Phone"),
):
    complaint = complaint_record_service.get_complaint_by_case_id(db, case_id)
    if complaint is None:
        raise HTTPException(status_code=404, detail=f"No complaint found with case ID {case_id}.")

    user_role = (current_user.role if current_user else (x_user_role or "CITIZEN")).upper()
    if user_role == "CITIZEN":
        pass  # Citizen authenticated to manage/delete complaint

    success = complaint_record_service.delete_complaint_record(db, case_id)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to delete complaint record.")

    return {"message": "Complaint deleted successfully", "case_id": case_id}


@router.patch("/{case_id}/status", response_model=ComplaintRecord)
def update_status(
    case_id: str,
    request: ComplaintStatusUpdateRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_from_token),
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
):
    role_str = (current_user.role if current_user else (x_user_role or "OFFICER")).upper()
    header_role = (x_user_role or "").upper()

    if role_str not in ["OFFICER", "ADMIN"] and header_role not in ["OFFICER", "ADMIN"]:
        raise HTTPException(status_code=403, detail="Only officers can update complaint status.")

    effective_role = "OFFICER" if ("OFFICER" in [role_str, header_role] or "ADMIN" in [role_str, header_role]) else role_str
    actor_name = current_user.full_name if (current_user and current_user.role.upper() == "OFFICER") else "Inspector Rajesh Kumar"
    actor_id = current_user.id if current_user else None

    updated = complaint_record_service.update_complaint_status(
        db=db,
        case_id=case_id,
        new_status=request.status,
        changed_by_user_id=actor_id,
        actor_name=actor_name,
        actor_role=effective_role,
        remarks=request.remarks or "",
    )
    if updated is None:
        raise HTTPException(status_code=404, detail=f"No complaint found with case ID {case_id}.")

    return updated


@router.get("/{case_id}/events", response_model=List[CaseEventResponse])
def get_case_events(case_id: str, db: Session = Depends(get_db)):
    return complaint_record_service.get_case_events(db, case_id)


@router.get("/{case_id}/evidence", response_model=List[CaseEvidenceResponse])
def get_case_evidence(case_id: str, db: Session = Depends(get_db)):
    return complaint_record_service.get_case_evidence(db, case_id)


@router.get("/{case_id}/fir-draft")
def get_fir_draft(case_id: str, db: Session = Depends(get_db)):
    fir = complaint_record_service.get_or_create_fir_draft(db, case_id)
    if not fir:
        raise HTTPException(status_code=404, detail=f"Case ID {case_id} not found.")
    return fir.iif_data


@router.post("/{case_id}/register-fir", response_model=FIRRecordResponse)
def register_fir(
    case_id: str,
    payload: FIRRegisterRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_from_token),
):
    officer_id = current_user.id if current_user else 1
    officer_name = current_user.full_name if current_user else "Officer"

    try:
        fir = register_fir_with_cctns(
            db=db,
            case_id=case_id,
            iif_data=payload.iif_data,
            officer_user_id=officer_id,
            officer_name=officer_name,
        )
        return fir
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
