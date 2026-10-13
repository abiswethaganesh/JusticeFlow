"""
Handles persistence of complaint/case records, status event history logging,
evidence attachments, and role/station filtered queries in PostgreSQL.
"""
import os
import logging
from typing import Optional, List
from sqlalchemy import or_, and_
from sqlalchemy.orm import Session

from app.models.complaint import Complaint
from app.models.case_event import CaseEvent
from app.models.case_evidence import CaseEvidence
from app.models.evidence_audit_event import EvidenceAuditEvent
from app.models.case_obligation import CaseObligation
from app.models.obligation_audit_event import ObligationAuditEvent
from app.models.fir_record import FIRRecord
from app.services.jurisdiction_service import resolve_police_station
from app.services.gemini_service import generate_fir_draft

logger = logging.getLogger(__name__)


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

    # Automatically scan complaint narrative for time-sensitive evidence and statutory obligations
    try:
        scan_and_attach_time_sensitive_evidence(db, complaint)
    except Exception as e:
        print(f"[Evidence Scanner Note] Narrative scan error: {e}")

    try:
        from app.services.statutory_rule_service import evaluate_case_statutory_obligations
        evaluate_case_statutory_obligations(db, complaint)
    except Exception as e:
        print(f"[Statutory Obligation Engine Note] Evaluation error: {e}")

    return complaint


def scan_and_attach_time_sensitive_evidence(db: Session, complaint: Complaint) -> List[CaseEvidence]:
    """Scans complaint narrative using AI/Rule engine and creates CaseEvidence and EvidenceAuditEvent records."""
    from app.services.gemini_service import detect_time_sensitive_evidence
    from app.services.retention_service import calculate_evidence_urgency
    from app.models.evidence_audit_event import EvidenceAuditEvent

    items = detect_time_sensitive_evidence(
        complaint_text=complaint.original_complaint or complaint.complaint_text,
        complaint_type=complaint.complaint_type,
        entities=complaint.structured_data,
    )

    created_evidence = []
    inc_date = (complaint.structured_data or {}).get("incident_date")
    inc_time = (complaint.structured_data or {}).get("incident_time")

    for item in items:
        ev_type = item.get("type", "other")
        title = item.get("title", "Evidence Item")

        # Avoid duplicate narrative extractions for same case & title
        existing = db.query(CaseEvidence).filter(
            CaseEvidence.case_id == complaint.case_id,
            CaseEvidence.title == title,
        ).first()
        if existing:
            continue

        urgency_info = calculate_evidence_urgency(
            evidence_type=ev_type,
            incident_date=inc_date,
            incident_time=inc_time,
            preservation_status="NOT_REVIEWED",
            db=db,
        )

        preservation_status = "REVIEW_REQUIRED" if urgency_info.get("potentially_time_sensitive") else "NOT_REVIEWED"

        ev = CaseEvidence(
            case_id=complaint.case_id,
            evidence_type=ev_type,
            title=title,
            file_path="",
            file_url="",
            description=item.get("description", ""),
            source=item.get("source", "Extracted from narrative"),
            potentially_time_sensitive=urgency_info.get("potentially_time_sensitive", True),
            retention_period_days=urgency_info.get("retention_period_days"),
            retention_source=urgency_info.get("retention_source"),
            retention_confidence=urgency_info.get("retention_confidence", "UNKNOWN"),
            urgency=urgency_info.get("urgency", "UNKNOWN"),
            estimated_expiry=urgency_info.get("estimated_expiry"),
            preservation_status=preservation_status,
            is_digital_narrative_extracted=True,
        )
        db.add(ev)
        db.flush()

        audit = EvidenceAuditEvent(
            case_id=complaint.case_id,
            evidence_id=ev.id,
            action="EVIDENCE_IDENTIFIED",
            previous_status=None,
            new_status=preservation_status,
            actor_name="AI Intelligence Engine",
            actor_role="SYSTEM",
            remarks=urgency_info.get("reason", "Identified from complaint narrative."),
        )
        db.add(audit)
        created_evidence.append(ev)

    if created_evidence:
        db.commit()

    return created_evidence



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
    """
    Safely deletes a complaint record and all associated child entities in strict dependency order:
    1. Find complaint/case.
    2. Find all CaseEvidence records belonging to that case.
    3. Remove physical files on disk associated with CaseEvidence (if present).
    4. Delete all EvidenceAuditEvent records referencing evidence IDs or case ID.
    5. Delete all CaseEvidence records.
    6. Delete all CaseEvent records and FIRRecord records.
    7. Delete the Complaint record.
    8. Commit transaction (with automatic rollback on failure).
    """
    complaint = get_complaint_by_case_id(db, case_id)
    if not complaint:
        return False

    real_case_id = complaint.case_id

    try:
        # Step 2: Find all CaseEvidence records for this case
        evidence_records = (
            db.query(CaseEvidence)
            .filter((CaseEvidence.case_id == real_case_id) | (CaseEvidence.case_id == str(case_id)))
            .all()
        )
        evidence_ids = [ev.id for ev in evidence_records]

        # Step 3: Remove physical evidence files on disk if present
        for ev in evidence_records:
            if ev.file_path and os.path.isfile(ev.file_path):
                try:
                    os.remove(ev.file_path)
                except Exception as file_err:
                    logger.warning(f"Failed to delete evidence file {ev.file_path}: {file_err}")

        # Step 4: Delete EvidenceAuditEvent records referencing these evidence IDs or case_id
        if evidence_ids:
            db.query(EvidenceAuditEvent).filter(
                (EvidenceAuditEvent.evidence_id.in_(evidence_ids)) |
                (EvidenceAuditEvent.case_id == real_case_id) |
                (EvidenceAuditEvent.case_id == str(case_id))
            ).delete(synchronize_session=False)
        else:
            db.query(EvidenceAuditEvent).filter(
                (EvidenceAuditEvent.case_id == real_case_id) |
                (EvidenceAuditEvent.case_id == str(case_id))
            ).delete(synchronize_session=False)

        # Step 5: Delete CaseEvidence records
        db.query(CaseEvidence).filter(
            (CaseEvidence.case_id == real_case_id) | (CaseEvidence.case_id == str(case_id))
        ).delete(synchronize_session=False)

        # Step 6: Delete CaseEvent, FIRRecord, ObligationAuditEvent, and CaseObligation records
        db.query(CaseEvent).filter(
            (CaseEvent.case_id == real_case_id) | (CaseEvent.case_id == str(case_id))
        ).delete(synchronize_session=False)

        db.query(FIRRecord).filter(
            (FIRRecord.case_id == real_case_id) | (FIRRecord.case_id == str(case_id))
        ).delete(synchronize_session=False)

        db.query(ObligationAuditEvent).filter(
            (ObligationAuditEvent.case_id == real_case_id) | (ObligationAuditEvent.case_id == str(case_id))
        ).delete(synchronize_session=False)

        db.query(CaseObligation).filter(
            (CaseObligation.case_id == real_case_id) | (CaseObligation.case_id == str(case_id))
        ).delete(synchronize_session=False)

        # Step 7: Delete Complaint record itself
        db.delete(complaint)

        # Step 8: Commit transaction
        db.commit()
        return True

    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting complaint record {case_id}: {e}", exc_info=True)
        raise e

