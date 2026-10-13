"""
Statutory Rule Knowledge Base & Deterministic Accountability Engine.
Ensures source-backed statutory procedural tracking under Bharatiya Nagarik Suraksha Sanhita, 2023 (BNSS).
Strictly prevents AI hallucination of legal deadlines.
"""
import calendar
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session

from app.models.legal_procedure_rule import LegalProcedureRule
from app.models.case_obligation import CaseObligation
from app.models.obligation_audit_event import ObligationAuditEvent
from app.models.complaint import Complaint

logger = logging.getLogger(__name__)

DEADLINE_WARNING_DAYS = 7  # Configurable Operational System Warning Threshold (NOT a statutory limit)

SEED_RULES = [
    {
        "rule_code": "BNSS_193_1",
        "title": "Investigation Without Unnecessary Delay",
        "legal_source": "Bharatiya Nagarik Suraksha Sanhita, 2023",
        "section_reference": "Section 193(1)",
        "description": "Every investigation under the chapter shall be completed without unnecessary delay.",
        "applicability_conditions": {"type": "GENERAL_INVESTIGATION"},
        "deadline_value": None,
        "deadline_unit": "QUALITATIVE",
        "start_event": "CASE_INFORMATION_RECORDED",
        "severity": "MEDIUM",
        "responsible_role": "OFFICER",
        "verification_status": "VERIFIED",
        "source_url": "https://www.indiacode.nic.in/handle/123456789/20063",
        "is_active": True,
    },
    {
        "rule_code": "BNSS_193_2",
        "title": "Specified Offence Investigation Completion",
        "legal_source": "Bharatiya Nagarik Suraksha Sanhita, 2023",
        "section_reference": "Section 193(2)",
        "description": "Investigation for offences under BNS sections 64, 65, 66, 67, 68, 70, 71 or POCSO sections 4, 6, 8, 10 shall be completed within two months from the date on which information was recorded.",
        "applicability_conditions": {
            "bns_sections": ["64", "65", "66", "67", "68", "70", "71"],
            "pocso_sections": ["4", "6", "8", "10"],
        },
        "deadline_value": 2,
        "deadline_unit": "MONTHS",
        "start_event": "CASE_INFORMATION_RECORDED",
        "severity": "CRITICAL",
        "responsible_role": "OFFICER",
        "verification_status": "VERIFIED",
        "source_url": "https://www.indiacode.nic.in/handle/123456789/20063",
        "is_active": True,
    },
    {
        "rule_code": "BNSS_193_3_II",
        "title": "Investigation Progress Communication",
        "legal_source": "Bharatiya Nagarik Suraksha Sanhita, 2023",
        "section_reference": "Section 193(3)(ii)",
        "description": "The officer in charge shall, within ninety days, inform the informant or victim of the progress of the investigation by any means including electronic communication.",
        "applicability_conditions": {"type": "ALL_INFORMANT_COMMUNICATIONS"},
        "deadline_value": 90,
        "deadline_unit": "DAYS",
        "start_event": "CASE_INFORMATION_RECORDED",
        "severity": "HIGH",
        "responsible_role": "OFFICER",
        "verification_status": "VERIFIED",
        "source_url": "https://www.indiacode.nic.in/handle/123456789/20063",
        "is_active": True,
    },
]


def seed_statutory_rules_if_needed(db: Session):
    """Seed BNSS statutory procedure rules into database if missing."""
    existing_codes = {r.rule_code for r in db.query(LegalProcedureRule.rule_code).all()}
    added = False
    for r in SEED_RULES:
        if r["rule_code"] not in existing_codes:
            rule = LegalProcedureRule(
                rule_code=r["rule_code"],
                title=r["title"],
                legal_source=r["legal_source"],
                section_reference=r["section_reference"],
                description=r["description"],
                applicability_conditions=r["applicability_conditions"],
                deadline_value=r["deadline_value"],
                deadline_unit=r["deadline_unit"],
                start_event=r["start_event"],
                severity=r["severity"],
                responsible_role=r["responsible_role"],
                verification_status=r["verification_status"],
                source_url=r["source_url"],
                is_active=r["is_active"],
            )
            db.add(rule)
            added = True
    if added:
        db.commit()


def add_months(start_date: datetime, months: int) -> datetime:
    """
    Calendar-aware month addition.
    Correctly handles month-end clamping (e.g. Jan 31 + 1 month = Feb 28/29) and leap years.
    """
    new_year = start_date.year + (start_date.month - 1 + months) // 12
    new_month = (start_date.month - 1 + months) % 12 + 1
    max_days = calendar.monthrange(new_year, new_month)[1]
    new_day = min(start_date.day, max_days)
    return start_date.replace(year=new_year, month=new_month, day=new_day)


def calculate_obligation_status(
    due_date: Optional[datetime],
    is_completed: bool = False,
    is_not_applicable: bool = False,
    is_requires_review: bool = False,
    warning_days: int = DEADLINE_WARNING_DAYS,
    ref_time: Optional[datetime] = None,
) -> str:
    """
    Deterministic obligation status calculator based on verified calendar rules.
    """
    if is_completed:
        return "COMPLETED"
    if is_not_applicable:
        return "NOT_APPLICABLE"
    if is_requires_review:
        return "REQUIRES_REVIEW"
    if due_date is None:
        return "UPCOMING"  # Qualitative obligations have no fixed numeric due date

    now = ref_time or datetime.now(timezone.utc)
    if due_date.tzinfo is None:
        due_date = due_date.replace(tzinfo=timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    if now > due_date:
        return "OVERDUE"
    elif now.date() == due_date.date():
        return "DUE_TODAY"
    elif now + timedelta(days=warning_days) >= due_date:
        return "DUE_SOON"
    else:
        return "UPCOMING"


def evaluate_case_statutory_obligations(db: Session, complaint: Complaint) -> List[CaseObligation]:
    """
    Idempotent Rule Applicability Engine:
    Evaluates verified statutory rules for a complaint and creates or updates obligations.
    Will NOT invent legal deadlines or guess statutory applicability.
    """
    seed_statutory_rules_if_needed(db)

    active_rules = db.query(LegalProcedureRule).filter(LegalProcedureRule.is_active == True).all()
    rule_map = {r.rule_code: r for r in active_rules}

    existing_obs = db.query(CaseObligation).filter(CaseObligation.case_id == complaint.case_id).all()
    existing_map = {ob.rule_id: ob for ob in existing_obs}

    evaluated_obligations = []
    start_dt = complaint.created_at or datetime.now(timezone.utc)
    if start_dt.tzinfo is None:
        start_dt = start_dt.replace(tzinfo=timezone.utc)

    struct_data = complaint.structured_data or {}
    text_lower = (complaint.original_complaint or complaint.complaint_text or "").lower()

    # Extracted legal section candidate strings
    legal_sec_list = struct_data.get("legal_sections") or []
    if isinstance(legal_sec_list, str):
        legal_sec_list = [legal_sec_list]

    # Combine all section mentions in structured data
    all_sections_str = " ".join([str(s) for s in legal_sec_list] + [
        str(struct_data.get("bns_section", "")),
        str(struct_data.get("offence_section", "")),
    ]).lower()

    # ----------------------------------------------------
    # RULE 1: BNSS 193(1) - Investigation Without Unnecessary Delay
    # ----------------------------------------------------
    rule1 = rule_map.get("BNSS_193_1")
    if rule1:
        if rule1.id in existing_map:
            ob = existing_map[rule1.id]
            if ob.status not in ["COMPLETED", "NOT_APPLICABLE", "WAIVED"]:
                new_st = calculate_obligation_status(ob.due_date, is_requires_review=(ob.status == "REQUIRES_REVIEW"))
                if new_st != ob.status:
                    ob.status = new_st
                    db.commit()
            evaluated_obligations.append(ob)
        else:
            ob = CaseObligation(
                case_id=complaint.case_id,
                rule_id=rule1.id,
                start_date=start_dt,
                due_date=None,  # Qualitative obligation - NO fabricated due date
                status="UPCOMING",
                responsible_role=rule1.responsible_role,
                applicability_reason="Statutory mandate under BNSS Section 193(1) requiring investigation to proceed without unnecessary delay.",
            )
            db.add(ob)
            db.flush()

            audit = ObligationAuditEvent(
                obligation_id=ob.id,
                case_id=complaint.case_id,
                action="OBLIGATION_CREATED",
                previous_status=None,
                new_status="UPCOMING",
                actor_name="Statutory Rule Engine",
                actor_role="SYSTEM",
                remarks="Qualitative procedural obligation created under BNSS Section 193(1).",
            )
            db.add(audit)
            db.commit()
            evaluated_obligations.append(ob)

    # ----------------------------------------------------
    # RULE 2: BNSS 193(2) - Specified Offence Investigation Completion (2 Months)
    # ----------------------------------------------------
    rule2 = rule_map.get("BNSS_193_2")
    if rule2:
        target_bns = rule2.applicability_conditions.get("bns_sections", [])
        target_pocso = rule2.applicability_conditions.get("pocso_sections", [])

        # Check for verified section matches
        has_verified_specified_section = False
        has_unverified_candidate = False

        # Match exact section numbers
        for sec in target_bns:
            if f"bns {sec}" in all_sections_str or f"section {sec}" in all_sections_str or f"bns_{sec}" in all_sections_str:
                has_verified_specified_section = True
                break
        for sec in target_pocso:
            if f"pocso {sec}" in all_sections_str or f"pocso_{sec}" in all_sections_str:
                has_verified_specified_section = True
                break

        # Check for unverified candidate indicators (e.g. rape / sexual assault / pocso mentioned in narrative)
        if not has_verified_specified_section:
            if any(w in text_lower for w in ["rape", "sexual assault", "pocso", "molest", "bns 64", "bns 65", "bns 70"]):
                has_unverified_candidate = True

        if has_verified_specified_section or has_unverified_candidate:
            if rule2.id in existing_map:
                ob = existing_map[rule2.id]
                if ob.status not in ["COMPLETED", "NOT_APPLICABLE", "WAIVED"]:
                    is_req_rev = not has_verified_specified_section
                    new_st = calculate_obligation_status(ob.due_date, is_requires_review=is_req_rev)
                    if new_st != ob.status:
                        ob.status = new_st
                        db.commit()
                evaluated_obligations.append(ob)
            else:
                if has_verified_specified_section:
                    due_dt = add_months(start_dt, 2)
                    st = calculate_obligation_status(due_dt)
                    reason = "Statutory 2-month investigation completion mandate under BNSS Section 193(2) for specified offences (BNS 64-71 / POCSO 4-10)."
                    ob = CaseObligation(
                        case_id=complaint.case_id,
                        rule_id=rule2.id,
                        start_date=start_dt,
                        due_date=due_dt,
                        status=st,
                        responsible_role=rule2.responsible_role,
                        applicability_reason=reason,
                    )
                else:
                    due_dt = add_months(start_dt, 2)
                    reason = "Potential specified offence indicators detected; applicable statutory section could not be conclusively verified without officer review."
                    ob = CaseObligation(
                        case_id=complaint.case_id,
                        rule_id=rule2.id,
                        start_date=start_dt,
                        due_date=due_dt,
                        status="REQUIRES_REVIEW",
                        responsible_role=rule2.responsible_role,
                        applicability_reason=reason,
                        review_reason="Offence indicators present but statutory section verification by officer required before enforcing 2-month deadline.",
                    )

                db.add(ob)
                db.flush()

                audit = ObligationAuditEvent(
                    obligation_id=ob.id,
                    case_id=complaint.case_id,
                    action="OBLIGATION_CREATED" if ob.status != "REQUIRES_REVIEW" else "OBLIGATION_REVIEW_REQUIRED",
                    previous_status=None,
                    new_status=ob.status,
                    actor_name="Statutory Rule Engine",
                    actor_role="SYSTEM",
                    remarks=ob.applicability_reason,
                )
                db.add(audit)
                db.commit()
                evaluated_obligations.append(ob)

    # ----------------------------------------------------
    # RULE 3: BNSS 193(3)(ii) - Investigation Progress Communication (90 Days)
    # ----------------------------------------------------
    rule3 = rule_map.get("BNSS_193_3_II")
    if rule3:
        if rule3.id in existing_map:
            ob = existing_map[rule3.id]
            if ob.status not in ["COMPLETED", "NOT_APPLICABLE", "WAIVED"]:
                new_st = calculate_obligation_status(ob.due_date, is_requires_review=(ob.status == "REQUIRES_REVIEW"))
                if new_st != ob.status:
                    ob.status = new_st
                    db.commit()
            evaluated_obligations.append(ob)
        else:
            due_dt = start_dt + timedelta(days=90)
            st = calculate_obligation_status(due_dt)
            ob = CaseObligation(
                case_id=complaint.case_id,
                rule_id=rule3.id,
                start_date=start_dt,
                due_date=due_dt,
                status=st,
                responsible_role=rule3.responsible_role,
                applicability_reason="Statutory mandate under BNSS Section 193(3)(ii) to communicate investigation progress to the informant/victim within 90 days.",
            )
            db.add(ob)
            db.flush()

            audit = ObligationAuditEvent(
                obligation_id=ob.id,
                case_id=complaint.case_id,
                action="OBLIGATION_CREATED",
                previous_status=None,
                new_status=st,
                actor_name="Statutory Rule Engine",
                actor_role="SYSTEM",
                remarks="90-day progress communication obligation created under BNSS Section 193(3)(ii).",
            )
            db.add(audit)
            db.commit()
            evaluated_obligations.append(ob)

    return evaluated_obligations


def complete_obligation(
    db: Session,
    obligation_id: int,
    actor_id: Optional[int],
    actor_name: str,
    actor_role: str,
    completion_notes: str,
) -> CaseObligation:
    """Mark a statutory obligation as COMPLETED with required completion notes."""
    ob = db.query(CaseObligation).filter(CaseObligation.id == obligation_id).first()
    if not ob:
        raise ValueError(f"Obligation ID {obligation_id} not found.")

    prev_status = ob.status
    ob.status = "COMPLETED"
    ob.completion_at = datetime.now(timezone.utc)
    ob.completion_notes = completion_notes or "Marked completed by authorized officer."

    audit = ObligationAuditEvent(
        obligation_id=ob.id,
        case_id=ob.case_id,
        action="COMPLETED",
        previous_status=prev_status,
        new_status="COMPLETED",
        actor_id=actor_id,
        actor_name=actor_name,
        actor_role=actor_role,
        remarks=f"Completed with notes: {ob.completion_notes}",
    )
    db.add(audit)
    db.commit()
    db.refresh(ob)
    return ob


def mark_obligation_not_applicable(
    db: Session,
    obligation_id: int,
    actor_id: Optional[int],
    actor_name: str,
    actor_role: str,
    reason: str,
) -> CaseObligation:
    """Mark a statutory obligation as NOT_APPLICABLE with required justification reason."""
    if not reason or not reason.strip():
        raise ValueError("A justification reason is required to mark an obligation as NOT_APPLICABLE.")

    ob = db.query(CaseObligation).filter(CaseObligation.id == obligation_id).first()
    if not ob:
        raise ValueError(f"Obligation ID {obligation_id} not found.")

    prev_status = ob.status
    ob.status = "NOT_APPLICABLE"
    ob.review_reason = reason.strip()

    audit = ObligationAuditEvent(
        obligation_id=ob.id,
        case_id=ob.case_id,
        action="MARKED_NOT_APPLICABLE",
        previous_status=prev_status,
        new_status="NOT_APPLICABLE",
        actor_id=actor_id,
        actor_name=actor_name,
        actor_role=actor_role,
        remarks=f"Marked NOT_APPLICABLE: {ob.review_reason}",
    )
    db.add(audit)
    db.commit()
    db.refresh(ob)
    return ob


def request_obligation_review(
    db: Session,
    obligation_id: int,
    actor_id: Optional[int],
    actor_name: str,
    actor_role: str,
    reason: str,
) -> CaseObligation:
    """Request legal or procedural review for an obligation."""
    if not reason or not reason.strip():
        raise ValueError("A reason is required to request legal/procedural review.")

    ob = db.query(CaseObligation).filter(CaseObligation.id == obligation_id).first()
    if not ob:
        raise ValueError(f"Obligation ID {obligation_id} not found.")

    prev_status = ob.status
    ob.status = "REQUIRES_REVIEW"
    ob.review_reason = reason.strip()

    audit = ObligationAuditEvent(
        obligation_id=ob.id,
        case_id=ob.case_id,
        action="OBLIGATION_REVIEW_REQUIRED",
        previous_status=prev_status,
        new_status="REQUIRES_REVIEW",
        actor_id=actor_id,
        actor_name=actor_name,
        actor_role=actor_role,
        remarks=f"Review requested: {ob.review_reason}",
    )
    db.add(audit)
    db.commit()
    db.refresh(ob)
    return ob


def trigger_obligation_escalation(
    db: Session,
    obligation: CaseObligation,
    actor_name: str = "System Accountability Engine",
    actor_role: str = "SYSTEM",
) -> CaseObligation:
    """Trigger accountability escalation for overdue obligations."""
    if obligation.status == "OVERDUE" and obligation.escalation_status != "ESCALATED_TO_SUPERVISOR":
        prev_esc = obligation.escalation_status
        obligation.escalation_status = "ESCALATED_TO_SUPERVISOR"

        audit = ObligationAuditEvent(
            obligation_id=obligation.id,
            case_id=obligation.case_id,
            action="ESCALATION_TRIGGERED",
            previous_status=obligation.status,
            new_status="OVERDUE",
            actor_name=actor_name,
            actor_role=actor_role,
            remarks=f"Escalation triggered: Obligation overdue beyond statutory/procedural deadline. Escalated from {prev_esc} to ESCALATED_TO_SUPERVISOR.",
        )
        db.add(audit)
        db.commit()
        db.refresh(obligation)

    return obligation
