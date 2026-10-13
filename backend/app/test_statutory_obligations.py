import unittest
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.complaint import Complaint
from app.models.case_evidence import CaseEvidence
from app.models.evidence_audit_event import EvidenceAuditEvent
from app.models.case_event import CaseEvent
from app.models.fir_record import FIRRecord
from app.models.legal_procedure_rule import LegalProcedureRule
from app.models.case_obligation import CaseObligation
from app.models.obligation_audit_event import ObligationAuditEvent
from app.services.complaint_record_service import create_complaint_record
from app.services.statutory_rule_service import (
    seed_statutory_rules_if_needed,
    add_months,
    calculate_obligation_status,
    evaluate_case_statutory_obligations,
    complete_obligation,
    mark_obligation_not_applicable,
    request_obligation_review,
    trigger_obligation_escalation,
)


class TestStatutoryObligationsEngine(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # In-memory SQLite DB enforcing foreign keys for regression testing
        cls.engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
        )
        Base.metadata.create_all(bind=cls.engine)
        cls.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=cls.engine)

    def setUp(self):
        self.db = self.SessionLocal()
        self.db.execute(text("PRAGMA foreign_keys = ON;"))
        seed_statutory_rules_if_needed(self.db)

    def tearDown(self):
        self.db.query(EvidenceAuditEvent).delete()
        self.db.query(CaseEvidence).delete()
        self.db.query(CaseEvent).delete()
        self.db.query(FIRRecord).delete()
        self.db.query(ObligationAuditEvent).delete()
        self.db.query(CaseObligation).delete()
        self.db.query(Complaint).delete()
        self.db.commit()
        self.db.close()

    def test_01_qualitative_obligation_bnss_193_1(self):
        """Test 1 & 2: BNSS 193(1) Qualitative obligation has NO fabricated due date."""
        complaint = create_complaint_record(
            db=self.db,
            complaint_type="other",
            complaint_text="General non-specific inquiry.",
            is_cognizable=True,
        )
        obs = self.db.query(CaseObligation).filter(CaseObligation.case_id == complaint.case_id).all()
        ob_193_1 = next((ob for ob in obs if ob.rule_id == 1 or ob.applicability_reason.find("193(1)") != -1), None)

        self.assertIsNotNone(ob_193_1)
        self.assertIsNone(ob_193_1.due_date, "BNSS 193(1) qualitative obligation MUST NOT have a fabricated due date")
        self.assertEqual(ob_193_1.status, "UPCOMING")

    def test_02_bnss_193_2_specified_offence_bns_64(self):
        """Test 3: BNSS 193(2) 2-month deadline for verified BNS Section 64 offence."""
        complaint = create_complaint_record(
            db=self.db,
            complaint_type="assault",
            complaint_text="Sexual assault case under BNS 64.",
            structured_data={"legal_sections": ["BNS 64"], "bns_section": "64"},
            is_cognizable=True,
        )
        obs = self.db.query(CaseObligation).filter(CaseObligation.case_id == complaint.case_id).all()
        ob_193_2 = next((ob for ob in obs if ob.due_date is not None and ob.applicability_reason.find("193(2)") != -1), None)

        self.assertIsNotNone(ob_193_2)
        expected_due = add_months(complaint.created_at, 2)
        self.assertEqual(ob_193_2.due_date.date(), expected_due.date(), "BNSS 193(2) must compute exactly 2 months deadline")

    def test_03_ordinary_theft_no_2_month_deadline(self):
        """Test 4: Ordinary theft case MUST NOT automatically receive 2-month statutory deadline."""
        complaint = create_complaint_record(
            db=self.db,
            complaint_type="property_theft",
            complaint_text="My laptop was stolen from my house.",
            structured_data={"legal_sections": ["BNS 303(2) - Theft"]},
            is_cognizable=True,
        )
        obs = self.db.query(CaseObligation).filter(CaseObligation.case_id == complaint.case_id).all()
        ob_193_2 = next((ob for ob in obs if ob.applicability_reason.find("193(2)") != -1), None)

        self.assertIsNone(ob_193_2, "Ordinary theft case must NOT receive BNSS 193(2) 2-month deadline")

    def test_04_unverified_candidate_requires_review(self):
        """Test 5 & 6: Unverified / ambiguous statutory section leads to REQUIRES_REVIEW."""
        complaint = create_complaint_record(
            db=self.db,
            complaint_type="assault",
            complaint_text="Alleged rape mentioned in complaint narrative but unverified section.",
            structured_data={},
            is_cognizable=True,
        )
        obs = self.db.query(CaseObligation).filter(CaseObligation.case_id == complaint.case_id).all()
        ob_193_2 = next((ob for ob in obs if ob.applicability_reason.find("193(2)") != -1 or ob.status == "REQUIRES_REVIEW"), None)

        self.assertIsNotNone(ob_193_2)
        self.assertEqual(ob_193_2.status, "REQUIRES_REVIEW", "Unverified statutory section must yield REQUIRES_REVIEW status")

    def test_05_calendar_month_add_and_leap_year(self):
        """Test 8 & 9: Month-based date calculation and month-end/leap year edge cases."""
        d1 = datetime(2026, 9, 18, 12, 0, tzinfo=timezone.utc)
        self.assertEqual(add_months(d1, 2).date(), datetime(2026, 11, 18).date())

        # Month end clamping: Jan 31 + 1 month = Feb 28 in non-leap year (2025)
        d_jan31 = datetime(2025, 1, 31, 12, 0, tzinfo=timezone.utc)
        self.assertEqual(add_months(d_jan31, 1).date(), datetime(2025, 2, 28).date())

        # Leap year: Jan 31 2024 + 1 month = Feb 29 2024
        d_jan31_leap = datetime(2024, 1, 31, 12, 0, tzinfo=timezone.utc)
        self.assertEqual(add_months(d_jan31_leap, 1).date(), datetime(2024, 2, 29).date())

    def test_06_deadline_status_calculation(self):
        """Test 10, 11, 12: DUE_SOON, DUE_TODAY, OVERDUE status calculation."""
        now = datetime.now(timezone.utc)

        due_soon = now + timedelta(days=5)
        self.assertEqual(calculate_obligation_status(due_soon, ref_time=now), "DUE_SOON")

        due_today = now
        self.assertEqual(calculate_obligation_status(due_today, ref_time=now), "DUE_TODAY")

        overdue = now - timedelta(days=2)
        self.assertEqual(calculate_obligation_status(overdue, ref_time=now), "OVERDUE")

    def test_07_completed_obligation_never_becomes_overdue(self):
        """Test 13: COMPLETED obligation never becomes OVERDUE afterward."""
        past_due = datetime.now(timezone.utc) - timedelta(days=5)
        self.assertEqual(calculate_obligation_status(past_due, is_completed=True), "COMPLETED")

    def test_08_not_applicable_requires_reason(self):
        """Test 14: Marking NOT_APPLICABLE requires justification reason."""
        complaint = create_complaint_record(
            db=self.db,
            complaint_type="cyber_fraud",
            complaint_text="Online scam case.",
        )
        obs = evaluate_case_statutory_obligations(self.db, complaint)
        ob = obs[0]

        with self.assertRaises(ValueError):
            mark_obligation_not_applicable(self.db, ob.id, actor_id=1, actor_name="Officer", actor_role="OFFICER", reason="")

        updated = mark_obligation_not_applicable(self.db, ob.id, actor_id=1, actor_name="Officer", actor_role="OFFICER", reason="Case transferred to Cyber Cell")
        self.assertEqual(updated.status, "NOT_APPLICABLE")

    def test_09_completion_and_escalation_audit_events(self):
        """Test 15 & 16: Creation of audit events for completion and escalation."""
        complaint = create_complaint_record(
            db=self.db,
            complaint_type="cyber_fraud",
            complaint_text="Cyber fraud case.",
        )
        obs = evaluate_case_statutory_obligations(self.db, complaint)
        ob = obs[0]

        # Completion action
        complete_obligation(self.db, ob.id, actor_id=1, actor_name="Inspector Rajesh", actor_role="OFFICER", completion_notes="Sent update to victim")
        audit_complete = self.db.query(ObligationAuditEvent).filter(
            ObligationAuditEvent.obligation_id == ob.id,
            ObligationAuditEvent.action == "COMPLETED",
        ).first()
        self.assertIsNotNone(audit_complete)

        # Escalation trigger
        ob.status = "OVERDUE"
        ob.escalation_status = "NONE"
        self.db.commit()

        trigger_obligation_escalation(self.db, ob)
        audit_esc = self.db.query(ObligationAuditEvent).filter(
            ObligationAuditEvent.obligation_id == ob.id,
            ObligationAuditEvent.action == "ESCALATION_TRIGGERED",
        ).first()
        self.assertIsNotNone(audit_esc)
        self.assertEqual(ob.escalation_status, "ESCALATED_TO_SUPERVISOR")

    def test_10_idempotent_evaluation_prevents_duplicates(self):
        """Test 19: Duplicate evaluation calls do NOT create duplicate obligations."""
        complaint = create_complaint_record(
            db=self.db,
            complaint_type="phone_snatching",
            complaint_text="Phone snatched near shop.",
        )
        obs_1 = evaluate_case_statutory_obligations(self.db, complaint)
        obs_2 = evaluate_case_statutory_obligations(self.db, complaint)

        self.assertEqual(len(obs_1), len(obs_2))
        total_obs = self.db.query(CaseObligation).filter(CaseObligation.case_id == complaint.case_id).count()
        self.assertEqual(total_obs, len(obs_1), "Idempotent evaluation must not duplicate obligations")


if __name__ == "__main__":
    unittest.main()
