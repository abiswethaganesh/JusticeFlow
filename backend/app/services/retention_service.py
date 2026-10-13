"""
Evidence Retention Knowledge Base & Deterministic Urgency Calculator.
Ensures deterministic calculation without AI hallucination of retention periods or legal deadlines.
"""
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple
from sqlalchemy.orm import Session

from app.models.retention_rule import EvidenceRetentionRule
from app.models.case_evidence import CaseEvidence


SEED_RULES = [
    {
        "evidence_type": "telecom_cdr",
        "display_label": "Telecom Call Detail Records (CDR)",
        "retention_period_days": 730,
        "source_policy": "TRAI Unified License Agreement (Clause 39.20) / DoT Mandate",
        "confidence_level": "VERIFIED",
        "is_time_sensitive": True,
        "default_urgency": "MEDIUM",
        "preservation_guidelines": "Send formal Section 91 CrPC / BNS notice to Telecom Nodal Officer for CDR and tower dump preservation.",
    },
    {
        "evidence_type": "isp_log",
        "display_label": "ISP / Server IP Access Logs",
        "retention_period_days": 180,
        "source_policy": "CERT-In Cyber Security Directions 2022 under IT Act Sec 70B",
        "confidence_level": "VERIFIED",
        "is_time_sensitive": True,
        "default_urgency": "HIGH",
        "preservation_guidelines": "Issue notice to Internet Service Provider / Cloud host for IP logs and subscriber records.",
    },
    {
        "evidence_type": "atm_footage",
        "display_label": "ATM Kiosk Security Camera Footage",
        "retention_period_days": 90,
        "source_policy": "RBI Cyber Security Framework for Banks Guidelines",
        "confidence_level": "VERIFIED",
        "is_time_sensitive": True,
        "default_urgency": "MEDIUM",
        "preservation_guidelines": "Request ATM CCTV backup from Bank Security Division.",
    },
    {
        "evidence_type": "cctv_private",
        "display_label": "Private Commercial / Shop CCTV Footage",
        "retention_period_days": 15,
        "source_policy": "PROTOTYPE_CONFIGURED (Private DVR Auto-Overwrite Loop — Subject to Provider Verification)",
        "confidence_level": "CONFIGURED",
        "is_time_sensitive": True,
        "default_urgency": "HIGH",
        "preservation_guidelines": "Officer must verify local DVR storage capacity and request physical copy or export immediately.",
    },
    {
        "evidence_type": "cctv_public",
        "display_label": "Public / Traffic Surveillance CCTV",
        "retention_period_days": 30,
        "source_policy": "PROTOTYPE_CONFIGURED (Municipal Traffic Surveillance Policy — Subject to Verification)",
        "confidence_level": "CONFIGURED",
        "is_time_sensitive": True,
        "default_urgency": "HIGH",
        "preservation_guidelines": "Requisition footage from Smart City Control Room / Police Command Centre.",
    },
    {
        "evidence_type": "digital_transaction",
        "display_label": "Bank / Payment Gateway Digital Transaction Record",
        "retention_period_days": 90,
        "source_policy": "PROTOTYPE_CONFIGURED (Payment Aggregator Gateway Log Cycle — Subject to Verification)",
        "confidence_level": "CONFIGURED",
        "is_time_sensitive": True,
        "default_urgency": "MEDIUM",
        "preservation_guidelines": "Issue requisition to Bank Nodal Officer / Payment Gateway Nodal.",
    },
]


def seed_retention_rules_if_needed(db: Session):
    """Seed retention rules if missing from database."""
    existing_types = {r.evidence_type for r in db.query(EvidenceRetentionRule.evidence_type).all()}
    added = False
    for r in SEED_RULES:
        if r["evidence_type"] not in existing_types:
            rule = EvidenceRetentionRule(
                evidence_type=r["evidence_type"],
                display_label=r["display_label"],
                retention_period_days=r["retention_period_days"],
                source_policy=r["source_policy"],
                confidence_level=r["confidence_level"],
                is_time_sensitive=r["is_time_sensitive"],
                default_urgency=r["default_urgency"],
                preservation_guidelines=r["preservation_guidelines"],
            )
            db.add(rule)
            added = True
    if added:
        db.commit()


def get_retention_rule_for_type(db: Session, evidence_type: str) -> Optional[EvidenceRetentionRule]:
    """Look up retention rule by evidence type or key alias."""
    if not evidence_type:
        return None
    
    clean_type = str(evidence_type).strip().lower()

    # Direct match
    rule = db.query(EvidenceRetentionRule).filter(EvidenceRetentionRule.evidence_type == clean_type).first()
    if rule:
        return rule

    # Alias matching
    if "cctv" in clean_type or "camera" in clean_type or "video" in clean_type:
        if "traffic" in clean_type or "public" in clean_type:
            return db.query(EvidenceRetentionRule).filter(EvidenceRetentionRule.evidence_type == "cctv_public").first()
        return db.query(EvidenceRetentionRule).filter(EvidenceRetentionRule.evidence_type == "cctv_private").first()

    if "transaction" in clean_type or "bank" in clean_type or "upi" in clean_type or "payment" in clean_type or "fraud" in clean_type:
        return db.query(EvidenceRetentionRule).filter(EvidenceRetentionRule.evidence_type == "digital_transaction").first()

    if "cdr" in clean_type or "telecom" in clean_type or "call" in clean_type or "phone_log" in clean_type:
        return db.query(EvidenceRetentionRule).filter(EvidenceRetentionRule.evidence_type == "telecom_cdr").first()

    if "isp" in clean_type or "ip_log" in clean_type or "server" in clean_type or "url" in clean_type:
        return db.query(EvidenceRetentionRule).filter(EvidenceRetentionRule.evidence_type == "isp_log").first()

    if "atm" in clean_type:
        return db.query(EvidenceRetentionRule).filter(EvidenceRetentionRule.evidence_type == "atm_footage").first()

    return None


def calculate_evidence_urgency(
    evidence_type: str,
    incident_date: Optional[str] = None,
    incident_time: Optional[str] = None,
    identified_at: Optional[datetime] = None,
    preservation_status: str = "NOT_REVIEWED",
    db: Optional[Session] = None,
) -> dict:
    """
    Pure deterministic urgency calculation based on verified/configured retention rules.
    Never invents retention periods or legal deadlines.
    
    Returns dict with:
      potentially_time_sensitive: bool
      retention_period_days: Optional[int]
      retention_source: str
      retention_confidence: str ("VERIFIED" | "CONFIGURED" | "UNKNOWN")
      urgency: str ("CRITICAL" | "HIGH" | "MEDIUM" | "LOW" | "UNKNOWN")
      estimated_expiry: Optional[datetime]
      reason: str
    """
    if preservation_status in ["PRESERVED", "NOT_APPLICABLE"]:
        return {
            "potentially_time_sensitive": False,
            "retention_period_days": None,
            "retention_source": "Preservation Completed / Not Applicable",
            "retention_confidence": "VERIFIED",
            "urgency": "LOW",
            "estimated_expiry": None,
            "reason": f"Evidence is currently marked as {preservation_status}.",
        }

    rule = get_retention_rule_for_type(db, evidence_type) if db else None

    # Unknown evidence type or no rule
    if not rule or rule.retention_period_days is None:
        return {
            "potentially_time_sensitive": rule.is_time_sensitive if rule else False,
            "retention_period_days": None,
            "retention_source": rule.source_policy if rule else "Retention information unavailable — officer verification required.",
            "retention_confidence": "UNKNOWN",
            "urgency": "UNKNOWN",
            "estimated_expiry": None,
            "reason": "Retention information unavailable — officer verification required.",
        }

    # Reference time: Incident date/time or identification date
    ref_datetime = None
    if incident_date:
        try:
            # Parse ISO date string
            clean_date = incident_date.strip()
            ref_datetime = datetime.fromisoformat(clean_date).replace(tzinfo=timezone.utc)
        except ValueError:
            ref_datetime = None

    if not ref_datetime:
        ref_datetime = identified_at or datetime.now(timezone.utc)

    # Expiry datetime
    expiry_dt = ref_datetime + timedelta(days=rule.retention_period_days)
    now_utc = datetime.now(timezone.utc)
    remaining_days = (expiry_dt - now_utc).total_seconds() / 86400.0

    # Determine urgency level based on remaining days
    if remaining_days <= 0:
        urgency = "CRITICAL"
        reason = f"Potential overwrite window reached ({rule.retention_period_days} days elapsed since incident/identification)."
    elif remaining_days < 2:
        urgency = "CRITICAL"
        reason = f"Critical time window: Estimated {remaining_days:.1f} days remaining before potential overwrite."
    elif remaining_days < 7:
        urgency = "HIGH"
        reason = f"High time sensitivity: Estimated {remaining_days:.1f} days remaining before potential overwrite."
    elif remaining_days < 30:
        urgency = "MEDIUM"
        reason = f"Moderate time window: Estimated {int(remaining_days)} days remaining before potential log cycle."
    else:
        urgency = "LOW"
        reason = f"Sufficient window: Estimated {int(remaining_days)} days remaining under {rule.source_policy}."

    confidence_note = ""
    if rule.confidence_level == "CONFIGURED":
        confidence_note = " (Note: Retention rule is PROTOTYPE_CONFIGURED; verify local system policy)."

    return {
        "potentially_time_sensitive": rule.is_time_sensitive,
        "retention_period_days": rule.retention_period_days,
        "retention_source": rule.source_policy,
        "retention_confidence": rule.confidence_level,
        "urgency": urgency,
        "estimated_expiry": expiry_dt,
        "reason": reason + confidence_note,
    }
