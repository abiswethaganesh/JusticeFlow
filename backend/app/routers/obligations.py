from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Header
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.case_obligation import CaseObligation
from app.models.legal_procedure_rule import LegalProcedureRule
from app.models.obligation_audit_event import ObligationAuditEvent
from app.models.complaint import Complaint
from app.models.user import User
from app.routers.auth import get_current_user_from_token
from app.schemas.statutory_obligation import (
    CaseObligationResponse,
    LegalProcedureRuleResponse,
    ObligationAuditEventResponse,
    ObligationActionRequest,
)
from app.services import statutory_rule_service, complaint_record_service

router = APIRouter(prefix="/obligations", tags=["obligations"])


def _enhance_obligation_response(ob: CaseObligation, db: Session) -> CaseObligationResponse:
    """Attaches rule info and calculates remaining/overdue days."""
    rule = db.query(LegalProcedureRule).filter(LegalProcedureRule.id == ob.rule_id).first()
    rule_resp = LegalProcedureRuleResponse.model_validate(rule) if rule else None

    resp = CaseObligationResponse.model_validate(ob)
    resp.rule = rule_resp

    if ob.due_date:
        now = datetime.now(timezone.utc)
        due = ob.due_date.replace(tzinfo=timezone.utc) if ob.due_date.tzinfo is None else ob.due_date
        diff = (due - now).days
        if diff >= 0:
            resp.days_remaining = diff
            resp.days_overdue = 0
        else:
            resp.days_remaining = 0
            resp.days_overdue = abs(diff)

    return resp


@router.get("/dashboard", response_model=List[CaseObligationResponse])
def get_dashboard_obligations(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_from_token),
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
    x_station_branch: Optional[str] = Header(None, alias="X-Station-Branch"),
):
    """
    Returns statutory obligations for cases accessible by the officer or supervisor.
    Respects jurisdiction/station filtering and updates status/escalation deterministically.
    """
    role = (current_user.role if current_user else (x_user_role or "OFFICER")).upper()
    station = (current_user.station_branch if current_user and current_user.station_branch else x_station_branch) or ""

    # Fetch complaints matching user station/role
    complaints = complaint_record_service.list_complaints_for_user(
        db=db,
        user_role=role,
        user_id=current_user.id if current_user else None,
        station_branch=station,
    )
    case_ids = [c.case_id for c in complaints]
    if not case_ids:
        return []

    obligations = (
        db.query(CaseObligation)
        .filter(CaseObligation.case_id.in_(case_ids))
        .order_by(CaseObligation.created_at.desc())
        .all()
    )

    result = []
    for ob in obligations:
        if ob.status not in ["COMPLETED", "NOT_APPLICABLE", "WAIVED"]:
            new_st = statutory_rule_service.calculate_obligation_status(
                ob.due_date,
                is_requires_review=(ob.status == "REQUIRES_REVIEW"),
            )
            if new_st != ob.status:
                ob.status = new_st
                db.commit()

            if ob.status == "OVERDUE":
                statutory_rule_service.trigger_obligation_escalation(db, ob)

        result.append(_enhance_obligation_response(ob, db))

    return result


@router.get("/case/{case_id}", response_model=List[CaseObligationResponse])
def get_case_obligations(case_id: str, db: Session = Depends(get_db)):
    """Returns statutory obligations for a specific case."""
    complaint = complaint_record_service.get_complaint_by_case_id(db, case_id)
    if not complaint:
        raise HTTPException(status_code=404, detail=f"No complaint found for case ID {case_id}.")

    # Evaluate any missing obligations idempotently
    obligations = statutory_rule_service.evaluate_case_statutory_obligations(db, complaint)
    return [_enhance_obligation_response(ob, db) for ob in obligations]


@router.get("/{obligation_id}", response_model=CaseObligationResponse)
def get_obligation(obligation_id: int, db: Session = Depends(get_db)):
    """Returns single obligation details."""
    ob = db.query(CaseObligation).filter(CaseObligation.id == obligation_id).first()
    if not ob:
        raise HTTPException(status_code=404, detail=f"Obligation ID {obligation_id} not found.")

    return _enhance_obligation_response(ob, db)


@router.get("/{obligation_id}/audit-trail", response_model=List[ObligationAuditEventResponse])
def get_obligation_audit_trail(obligation_id: int, db: Session = Depends(get_db)):
    """Returns audit history timeline for a statutory obligation."""
    events = (
        db.query(ObligationAuditEvent)
        .filter(ObligationAuditEvent.obligation_id == obligation_id)
        .order_by(ObligationAuditEvent.timestamp.asc())
        .all()
    )
    return events


@router.post("/{obligation_id}/complete", response_model=CaseObligationResponse)
def complete_obligation_endpoint(
    obligation_id: int,
    payload: ObligationActionRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_from_token),
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
):
    """Officer action: Mark statutory obligation as COMPLETED."""
    role = (current_user.role if current_user else (x_user_role or "OFFICER")).upper()
    if role not in ["OFFICER", "ADMIN", "SUPERVISOR"]:
        raise HTTPException(status_code=403, detail="Only authorized police officers or supervisors can complete statutory obligations.")

    actor_name = current_user.full_name if current_user else (payload.actor_name or "Officer")
    actor_id = current_user.id if current_user else None

    try:
        updated = statutory_rule_service.complete_obligation(
            db=db,
            obligation_id=obligation_id,
            actor_id=actor_id,
            actor_name=actor_name,
            actor_role=role,
            completion_notes=payload.completion_notes or "",
        )
        return _enhance_obligation_response(updated, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{obligation_id}/not-applicable", response_model=CaseObligationResponse)
def not_applicable_obligation_endpoint(
    obligation_id: int,
    payload: ObligationActionRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_from_token),
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
):
    """Officer action: Mark statutory obligation as NOT_APPLICABLE (requires reason)."""
    role = (current_user.role if current_user else (x_user_role or "OFFICER")).upper()
    if role not in ["OFFICER", "ADMIN", "SUPERVISOR"]:
        raise HTTPException(status_code=403, detail="Only authorized police officers or supervisors can modify statutory obligations.")

    if not payload.reason or not payload.reason.strip():
        raise HTTPException(status_code=400, detail="A justification reason is required to mark an obligation as NOT_APPLICABLE.")

    actor_name = current_user.full_name if current_user else (payload.actor_name or "Officer")
    actor_id = current_user.id if current_user else None

    try:
        updated = statutory_rule_service.mark_obligation_not_applicable(
            db=db,
            obligation_id=obligation_id,
            actor_id=actor_id,
            actor_name=actor_name,
            actor_role=role,
            reason=payload.reason,
        )
        return _enhance_obligation_response(updated, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{obligation_id}/request-review", response_model=CaseObligationResponse)
def request_review_obligation_endpoint(
    obligation_id: int,
    payload: ObligationActionRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_from_token),
    x_user_role: Optional[str] = Header(None, alias="X-User-Role"),
):
    """Officer action: Request legal/procedural review for an obligation."""
    role = (current_user.role if current_user else (x_user_role or "OFFICER")).upper()
    if role not in ["OFFICER", "ADMIN", "SUPERVISOR"]:
        raise HTTPException(status_code=403, detail="Only authorized police officers or supervisors can request obligation reviews.")

    if not payload.reason or not payload.reason.strip():
        raise HTTPException(status_code=400, detail="A reason is required to request legal/procedural review.")

    actor_name = current_user.full_name if current_user else (payload.actor_name or "Officer")
    actor_id = current_user.id if current_user else None

    try:
        updated = statutory_rule_service.request_obligation_review(
            db=db,
            obligation_id=obligation_id,
            actor_id=actor_id,
            actor_name=actor_name,
            actor_role=role,
            reason=payload.reason,
        )
        return _enhance_obligation_response(updated, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/cases/{case_id}/evaluate", response_model=List[CaseObligationResponse])
def evaluate_case_obligations_endpoint(case_id: str, db: Session = Depends(get_db)):
    """Triggers idempotent statutory obligation evaluation for a case."""
    complaint = complaint_record_service.get_complaint_by_case_id(db, case_id)
    if not complaint:
        raise HTTPException(status_code=404, detail=f"No complaint found for case ID {case_id}.")

    obligations = statutory_rule_service.evaluate_case_statutory_obligations(db, complaint)
    return [_enhance_obligation_response(ob, db) for ob in obligations]
