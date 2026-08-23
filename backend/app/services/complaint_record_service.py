"""
Handles persistence of complaint/case records, status event history logging,
evidence attachments, and role/station filtered queries in PostgreSQL.
"""
from typing import Optional, List
from sqlalchemy import or_, and_
from sqlalchemy.orm import Session

from app.models.complaint import Complaint
from app.models.case_event import CaseEvent
from app.models.case_evidence import CaseEvidence
from app.models.fir_record import FIRRecord
from app.services.jurisdiction_service import resolve_police_station
from app.services.gemini_service import generate_fir_draft


def normalize_phone(phone: Optional[str]) -> str:
    if not phone:
        return ""
    digits = "".join(c for c in phone if c.isdigit())
    if len(digits) > 10 and digits.startswith("91"):
        return digits[-10:]
    return digits


def create_complaint_record(
    db: Session,
    complaint_type: str,
    complaint_text: str,
    summary: str = "",
    structured_data: dict = None,
    incident_details: dict = None,
    citizen_id: Optional[int] = None,
    citizen_phone: str = "",
    is_cognizable: bool = True,
    priority: str = "MEDIUM",
) -> Complaint:
    if structured_data is None:
        structured_data = {}
    if incident_details is None:
        incident_details = {}

    station_id, station_name = resolve_police_station(
        db,
        incident_location=incident_details.get("location") or structured_data.get("incident_location", ""),
        structured_data=structured_data,
        complaint_text=complaint_text,
    )

    workflow_type = "cognizable_fir" if is_cognizable else "non_cognizable"

    complaint = Complaint(
        complaint_type=complaint_type,
        workflow_type=workflow_type,
        original_complaint=complaint_text,
        complaint_text=complaint_text,
        summary=summary,
        structured_data=structured_data,
        incident_details=incident_details,
        citizen_id=citizen_id,
        citizen_phone=citizen_phone,
        police_station_id=station_id,
        assigned_station=station_name,
        status="SUBMITTED",
        priority=priority,
        is_cognizable=is_cognizable,
        case_id="",
    )
    db.add(complaint)
    db.flush()

    year = complaint.created_at.year
    complaint.case_id = f"JF-{year}-{complaint.id:06d}"
    db.flush()

    # Log initial status event in case_events
    initial_event = CaseEvent(
        case_id=complaint.case_id,
        previous_status=None,
        new_status="SUBMITTED",
        changed_by_user_id=citizen_id,
        actor_name="Citizen",
        actor_role="CITIZEN",
        remarks=f"Complaint registered and assigned to {station_name}",
    )
    db.add(initial_event)

    db.commit()
    db.refresh(complaint)
    return complaint


def list_complaints_for_user(
    db: Session,
    user_role: str,
    user_id: Optional[int] = None,
    user_phone: Optional[str] = None,
    police_station_id: Optional[int] = None,
    station_branch: Optional[str] = None,
) -> List[Complaint]:
    query = db.query(Complaint)

    """Strictly filter complaints by citizen phone/ID or officer station branch."""
    role_upper = (user_role or "").upper()

    if role_upper == "CITIZEN":
        if not user_id and not user_phone:
            return []

        if user_id:
            user_conds = [Complaint.citizen_id == user_id]
            if user_phone and user_phone.strip():
                raw_phone = user_phone.strip()
                norm = normalize_phone(raw_phone)
                p_conds = [Complaint.citizen_phone == raw_phone]
                if norm:
                    p_conds.append(Complaint.citizen_phone == norm)
                    p_conds.append(Complaint.citizen_phone == f"+91{norm}")
                user_conds.append(and_(Complaint.citizen_id == None, or_(*p_conds)))
            query = query.filter(or_(*user_conds))
        elif user_phone and user_phone.strip():
            raw_phone = user_phone.strip()
            norm = normalize_phone(raw_phone)
            p_conds = [Complaint.citizen_phone == raw_phone]
            if norm:
                p_conds.append(Complaint.citizen_phone == norm)
                p_conds.append(Complaint.citizen_phone == f"+91{norm}")
            query = query.filter(or_(*p_conds))
        else:
            return []

    elif role_upper == "OFFICER":
        if station_branch and station_branch.strip():
            branch_clean = station_branch.strip()
            query = query.filter(
                (Complaint.assigned_station == branch_clean) |
                (Complaint.assigned_station.ilike(f"%{branch_clean}%"))
            )
        elif police_station_id:
            query = query.filter(Complaint.police_station_id == police_station_id)
        else:
            return []

    return query.order_by(Complaint.created_at.desc()).all()


def get_complaint_by_case_id(db: Session, case_id: str) -> Optional[Complaint]:
    if not case_id:
        return None
    raw_str = str(case_id).strip()

    # 1. Exact match on case_id
    comp = db.query(Complaint).filter(Complaint.case_id == raw_str).first()
    if comp:
        return comp

    # 2. Case-insensitive match on case_id
    comp = db.query(Complaint).filter(Complaint.case_id.ilike(raw_str)).first()
    if comp:
        return comp

    # 3. Numeric ID match if raw_str is digits
    if raw_str.isdigit():
        comp = db.query(Complaint).filter(Complaint.id == int(raw_str)).first()
        if comp:
            return comp

    return None


def update_complaint_status(
    db: Session,
    case_id: str,
    new_status: str,
    changed_by_user_id: Optional[int] = None,
    actor_name: str = "Officer",
    actor_role: str = "OFFICER",
    remarks: str = "",
) -> Optional[Complaint]:
    complaint = get_complaint_by_case_id(db, case_id)
    if not complaint:
        return None

    prev_status = complaint.status
    complaint.status = new_status.upper()

    event = CaseEvent(
        case_id=case_id,
        previous_status=prev_status,
        new_status=complaint.status,
        changed_by_user_id=changed_by_user_id,
        actor_name=actor_name,
        actor_role=actor_role,
        remarks=remarks or f"Case status updated to {complaint.status}",
    )
    db.add(event)
    db.commit()
    db.refresh(complaint)
    return complaint


def get_case_events(db: Session, case_id: str) -> List[CaseEvent]:
    return db.query(CaseEvent).filter(CaseEvent.case_id == case_id).order_by(CaseEvent.created_at.asc()).all()


def get_case_evidence(db: Session, case_id: str) -> List[CaseEvidence]:
    return db.query(CaseEvidence).filter(CaseEvidence.case_id == case_id).order_by(CaseEvidence.uploaded_at.desc()).all()


def get_or_create_fir_draft(db: Session, case_id: str) -> Optional[FIRRecord]:
    complaint = get_complaint_by_case_id(db, case_id)
    if not complaint:
        return None

    fir = db.query(FIRRecord).filter(FIRRecord.case_id == case_id).first()
    if fir:
        return fir

    # Generate FIR Draft using Gemini AI
    case_dict = {
        "case_id": complaint.case_id,
        "complaint_type": complaint.complaint_type,
        "original_complaint": complaint.original_complaint,
        "summary": complaint.summary,
        "structured_data": complaint.structured_data,
        "incident_details": complaint.incident_details,
        "assigned_station": complaint.assigned_station,
    }
    iif_data = generate_fir_draft(case_dict)

    fir_no_draft = f"FIR-DRAFT-{complaint.case_id}"
    fir = FIRRecord(
        case_id=case_id,
        fir_number=fir_no_draft,
        iif_data=iif_data,
        status="DRAFT",
    )
    db.add(fir)
    db.commit()
    db.refresh(fir)
    return fir


def delete_complaint_record(db: Session, case_id: str) -> bool:
    complaint = get_complaint_by_case_id(db, case_id)
    if not complaint:
        return False

    real_case_id = complaint.case_id
    db.query(CaseEvent).filter((CaseEvent.case_id == real_case_id) | (CaseEvent.case_id == str(case_id))).delete()
    db.query(CaseEvidence).filter((CaseEvidence.case_id == real_case_id) | (CaseEvidence.case_id == str(case_id))).delete()
    db.query(FIRRecord).filter((FIRRecord.case_id == real_case_id) | (FIRRecord.case_id == str(case_id))).delete()
    db.delete(complaint)
    db.commit()
    return True
