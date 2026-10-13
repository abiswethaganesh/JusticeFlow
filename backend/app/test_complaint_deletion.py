import os
import unittest
import tempfile
from datetime import datetime, timezone
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.complaint import Complaint
from app.models.case_evidence import CaseEvidence
from app.models.evidence_audit_event import EvidenceAuditEvent
from app.models.case_event import CaseEvent
from app.models.fir_record import FIRRecord
from app.services.complaint_record_service import (
    create_complaint_record,
    delete_complaint_record,
)


class TestComplaintDeletionRegression(unittest.TestCase):

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
        # Enable SQLite foreign key constraints
        self.db.execute(text("PRAGMA foreign_keys = ON;"))

    def tearDown(self):
        self.db.close()

    def test_delete_complaint_with_evidence_and_audit_events(self):
        # 1. Create Complaint
        complaint = create_complaint_record(
            db=self.db,
            complaint_type="phone_snatching",
            complaint_text="My phone was snatched near Anna Nagar.",
            summary="Phone snatched.",
            structured_data={"incident_location": "Anna Nagar"},
            is_cognizable=True,
        )
        case_id = complaint.case_id

        # Create temporary dummy physical file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
        temp_file.write(b"dummy image data")
        temp_file.close()
        temp_file_path = temp_file.name

        # 2. Create CaseEvidence record
        evidence = CaseEvidence(
            case_id=case_id,
            evidence_type="cctv",
            title="Shop CCTV Footage",
            file_path=temp_file_path,
            file_url=f"/evidence/1/file",
            description="CCTV footage clip",
            potentially_time_sensitive=True,
            urgency="HIGH",
        )
        self.db.add(evidence)
        self.db.flush()

        # 3. Create EvidenceAuditEvent referencing both case_id and evidence.id
        audit_event = EvidenceAuditEvent(
            case_id=case_id,
            evidence_id=evidence.id,
            action="EVIDENCE_IDENTIFIED",
            previous_status=None,
            new_status="REVIEW_REQUIRED",
            actor_name="AI Engine",
            actor_role="SYSTEM",
            remarks="Identified shop CCTV",
        )
        self.db.add(audit_event)

        # 4. Create CaseEvent record
        case_event = CaseEvent(
            case_id=case_id,
            previous_status="SUBMITTED",
            new_status="UNDER_INVESTIGATION",
            actor_name="Inspector Rajesh",
            actor_role="OFFICER",
            remarks="Investigating",
        )
        self.db.add(case_event)

        # 5. Create FIRRecord
        fir_record = FIRRecord(
            case_id=case_id,
            fir_number=f"FIR-TEST-{case_id}",
            iif_data={"crime": "phone_snatching"},
            status="DRAFT",
        )
        self.db.add(fir_record)
        self.db.commit()

        # Verify records exist before deletion
        self.assertIsNotNone(self.db.query(Complaint).filter(Complaint.case_id == case_id).first())
        self.assertIsNotNone(self.db.query(CaseEvidence).filter(CaseEvidence.case_id == case_id).first())
        self.assertIsNotNone(self.db.query(EvidenceAuditEvent).filter(EvidenceAuditEvent.case_id == case_id).first())
        self.assertIsNotNone(self.db.query(CaseEvent).filter(CaseEvent.case_id == case_id).first())
        self.assertIsNotNone(self.db.query(FIRRecord).filter(FIRRecord.case_id == case_id).first())
        self.assertTrue(os.path.exists(temp_file_path))

        # 6. Execute delete_complaint_record
        success = delete_complaint_record(self.db, case_id)
        self.assertTrue(success, "Complaint deletion should return True")

        # 7. Verify all dependent entities and complaint are deleted
        self.assertIsNone(self.db.query(Complaint).filter(Complaint.case_id == case_id).first())
        self.assertIsNone(self.db.query(CaseEvidence).filter(CaseEvidence.case_id == case_id).first())
        self.assertIsNone(self.db.query(EvidenceAuditEvent).filter(EvidenceAuditEvent.case_id == case_id).first())
        self.assertIsNone(self.db.query(CaseEvent).filter(CaseEvent.case_id == case_id).first())
        self.assertIsNone(self.db.query(FIRRecord).filter(FIRRecord.case_id == case_id).first())

        # Verify physical disk file was removed
        self.assertFalse(os.path.exists(temp_file_path), "Physical evidence file on disk should be removed")

    def test_delete_non_existent_complaint(self):
        result = delete_complaint_record(self.db, "NON_EXISTENT_CASE_ID_9999")
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
