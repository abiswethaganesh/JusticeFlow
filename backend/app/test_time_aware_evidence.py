"""
Test Suite for Time-Aware Evidence Preservation System (10 Test Scenarios).
Verifies:
1. Complaint mentioning CCTV.
2. Complaint mentioning digital transaction.
3. Complaint with no time-sensitive evidence.
4. Evidence with unknown retention period.
5. Missing incident date.
6. Contradictory/incomplete dates.
7. Multiple evidence items with different urgency.
8. Evidence already marked as preserved.
9. AI returns invalid structured output (Fallback test).
10. Gemini API unavailable (Fallback test).
"""
import unittest
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.complaint import Complaint
from app.models.case_evidence import CaseEvidence
from app.models.evidence_audit_event import EvidenceAuditEvent
from app.models.retention_rule import EvidenceRetentionRule
from app.services.retention_service import (
    seed_retention_rules_if_needed,
    calculate_evidence_urgency,
    get_retention_rule_for_type,
)
from app.services.gemini_service import (
    _fallback_detect_time_sensitive_evidence,
    generate_preservation_request_draft,
)
from app.services.complaint_record_service import (
    create_complaint_record,
    scan_and_attach_time_sensitive_evidence,
)


class TestTimeAwareEvidencePreservation(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # In-memory SQLite database for testing
        cls.engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        Base.metadata.create_all(bind=cls.engine)
        cls.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=cls.engine)

    def setUp(self):
        self.db = self.SessionLocal()
        seed_retention_rules_if_needed(self.db)

    def tearDown(self):
        self.db.query(EvidenceAuditEvent).delete()
        self.db.query(CaseEvidence).delete()
        self.db.query(Complaint).delete()
        self.db.commit()
        self.db.close()

    def test_01_cctv_mention(self):
        """Test 1: Complaint mentioning CCTV outside a shop."""
        complaint = create_complaint_record(
            db=self.db,
            complaint_type="phone_snatching",
            complaint_text="My phone was snatched near Anna Nagar. There is a CCTV camera outside the nearby shop.",
            summary="Phone snatched near shop CCTV.",
            structured_data={"incident_location": "Anna Nagar", "incident_date": datetime.now(timezone.utc).date().isoformat()},
            is_cognizable=True,
        )
        evidence_list = self.db.query(CaseEvidence).filter(CaseEvidence.case_id == complaint.case_id).all()
        self.assertGreaterEqual(len(evidence_list), 1)

        cctv_item = next((ev for ev in evidence_list if "cctv" in ev.evidence_type.lower() or "cctv" in ev.title.lower()), None)
        self.assertIsNotNone(cctv_item)
        self.assertTrue(cctv_item.potentially_time_sensitive)
        self.assertIn(cctv_item.urgency, ["CRITICAL", "HIGH", "MEDIUM"])

    def test_02_digital_transaction_mention(self):
        """Test 2: Complaint mentioning digital transaction / scam."""
        complaint = create_complaint_record(
            db=self.db,
            complaint_type="cyber_fraud",
            complaint_text="I was scammed of Rs 15,000 via UPI GPay transaction ID 99882211.",
            summary="Cyber fraud via GPay UPI transaction.",
            structured_data={"fraud_amount": "Rs 15,000"},
            is_cognizable=True,
        )
        evidence_list = self.db.query(CaseEvidence).filter(CaseEvidence.case_id == complaint.case_id).all()
        tx_item = next((ev for ev in evidence_list if "digital_transaction" in ev.evidence_type or "transaction" in ev.title.lower()), None)
        self.assertIsNotNone(tx_item)
        self.assertTrue(tx_item.potentially_time_sensitive)

    def test_03_no_time_sensitive_evidence(self):
        """Test 3: Complaint with no time-sensitive evidence (lost paper document)."""
        complaint = create_complaint_record(
            db=self.db,
            complaint_type="lost_document",
            complaint_text="I lost my printed paper marksheet certificate in a park.",
            summary="Lost paper marksheet.",
            structured_data={"document_name": "Marksheet"},
            is_cognizable=False,
        )
        evidence_list = self.db.query(CaseEvidence).filter(CaseEvidence.case_id == complaint.case_id).all()
        ts_items = [ev for ev in evidence_list if ev.potentially_time_sensitive]
        self.assertEqual(len(ts_items), 0)

    def test_04_unknown_retention_handling(self):
        """Test 4: Unlisted evidence type returns UNKNOWN retention and UNKNOWN urgency (no hallucinated deadlines)."""
        result = calculate_evidence_urgency(
            evidence_type="unknown_custom_physical_artifact",
            incident_date="2026-09-01",
            db=self.db,
        )
        self.assertEqual(result["retention_confidence"], "UNKNOWN")
        self.assertEqual(result["urgency"], "UNKNOWN")
        self.assertIsNone(result["retention_period_days"])
        self.assertIn("officer verification required", result["reason"].lower())

    def test_05_missing_incident_date(self):
        """Test 5: Missing incident date calculates urgency safely using identified_at reference."""
        now_dt = datetime.now(timezone.utc)
        result = calculate_evidence_urgency(
            evidence_type="cctv_private",
            incident_date=None,
            identified_at=now_dt,
            db=self.db,
        )
        self.assertIsNotNone(result["estimated_expiry"])
        self.assertIn(result["urgency"], ["CRITICAL", "HIGH", "MEDIUM", "LOW"])

    def test_06_contradictory_dates(self):
        """Test 6: Invalid/contradictory incident date string handles gracefully without crash."""
        result = calculate_evidence_urgency(
            evidence_type="cctv_private",
            incident_date="INVALID_DATE_STRING_9999",
            db=self.db,
        )
        self.assertIsNotNone(result["estimated_expiry"])
        self.assertIn(result["urgency"], ["CRITICAL", "HIGH", "MEDIUM", "LOW"])


    def test_07_multiple_evidence_items(self):
        """Test 7: Complaint with multiple evidence items of different types."""
        detected = _fallback_detect_time_sensitive_evidence(
            "My car window was broken near ATM kiosk, CCTV recorded it and I transferred money via GPay to scammer."
        )
        self.assertGreaterEqual(len(detected), 2)
        types = [item["type"] for item in detected]
        self.assertIn("cctv_private", types)
        self.assertIn("digital_transaction", types)

    def test_08_evidence_already_preserved(self):
        """Test 8: Evidence marked as PRESERVED sets urgency to LOW."""
        result = calculate_evidence_urgency(
            evidence_type="cctv_private",
            incident_date="2026-09-01",
            preservation_status="PRESERVED",
            db=self.db,
        )
        self.assertFalse(result["potentially_time_sensitive"])
        self.assertEqual(result["urgency"], "LOW")

    def test_09_invalid_ai_output_fallback(self):
        """Test 9: Fallback regex extractor works accurately when AI JSON is invalid."""
        fallback_items = _fallback_detect_time_sensitive_evidence(
            "There is a CCTV camera outside the shop."
        )
        self.assertEqual(len(fallback_items), 1)
        self.assertEqual(fallback_items[0]["type"], "cctv_private")

    def test_10_preservation_draft_fallback(self):
        """Test 10: Rule-based preservation request draft generator produces complete officer notice draft."""
        draft = generate_preservation_request_draft(
            case_id="JF-2026-000123",
            evidence_data={"title": "Shop CCTV Footage", "source": "Nearby Shop", "urgency": "HIGH"},
            complaint_data={"incident_details": {"location": "Anna Nagar"}, "structured_data": {"incident_date": "2026-09-18"}},
        )
        self.assertIn("OFFICIAL REQUISITION", draft["subject"])
        self.assertEqual(draft["case_id"], "JF-2026-000123")
        self.assertIn("OFFICER REVIEW DRAFT ONLY", draft["disclaimer"])


if __name__ == "__main__":
    unittest.main()
