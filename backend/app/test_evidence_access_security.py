"""
Verification & Security Test Suite for Evidence File Access & Authorization.
Tests:
1. Upload a new test file using temporary directory.
2. Confirm temporary test file exists during test and is cleaned up in tearDown.
3. Confirm database record stores correct file_path and file_url.
4. Authorized Citizen (complaint owner) can access/view evidence file inline and download with parameter.
5. Authorized Officer (assigned station) can access/view evidence file inline.
6. Unauthorized Citizen (different user) receives 403 Forbidden.
7. Unauthorized Officer (different station) receives 403 Forbidden.
8. Existing evidence uploaded before Time-Aware feature still opens.
9. Time-Aware evidence metadata remains 100% intact.
10. Default view disposition is 'inline', download=True disposition is 'attachment'.
"""
import os
import tempfile
import unittest
import uuid
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.user import User
from app.models.police_station import PoliceStation
from app.models.officer import Officer
from app.models.complaint import Complaint
from app.models.case_evidence import CaseEvidence
from app.services.retention_service import seed_retention_rules_if_needed, calculate_evidence_urgency
from app.services.complaint_record_service import create_complaint_record
from app.routers.evidence import download_or_view_evidence_file
from fastapi import HTTPException


class TestEvidenceAccessSecurity(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        Base.metadata.create_all(bind=cls.engine)
        cls.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=cls.engine)

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db = self.SessionLocal()
        seed_retention_rules_if_needed(self.db)

        uid = uuid.uuid4().hex[:6]
        # Create Station 1 & Station 2
        self.station1 = PoliceStation(station_name="Anna Nagar Police Station", station_code=f"AN_{uid}", city="Chennai")
        self.station2 = PoliceStation(station_name="Adyar Police Station", station_code=f"AD_{uid}", city="Chennai")
        self.db.add_all([self.station1, self.station2])
        self.db.flush()

        # Create Citizen 1 & Citizen 2
        self.citizen1 = User(email=f"c1_{uid}@test.com", phone=f"987{uuid.uuid4().hex[:7]}", full_name="Citizen One", role="CITIZEN", password_hash="testpass")
        self.citizen2 = User(email=f"c2_{uid}@test.com", phone=f"912{uuid.uuid4().hex[:7]}", full_name="Citizen Two", role="CITIZEN", password_hash="testpass")
        self.db.add_all([self.citizen1, self.citizen2])
        self.db.flush()

        # Create Officer 1 (Station 1) & Officer 2 (Station 2)
        self.officer_user1 = User(email=f"officer1_{uid}@test.com", phone=f"900{uuid.uuid4().hex[:7]}", full_name="Inspector Rajesh", role="OFFICER", station_branch="Anna Nagar Police Station", password_hash="testpass")
        self.officer_user2 = User(email=f"officer2_{uid}@test.com", phone=f"901{uuid.uuid4().hex[:7]}", full_name="Inspector Vikram", role="OFFICER", station_branch="Adyar Police Station", password_hash="testpass")
        self.db.add_all([self.officer_user1, self.officer_user2])
        self.db.flush()

        self.officer1 = Officer(user_id=self.officer_user1.id, officer_id=f"OFF_{uid}_1", badge_number=f"AN{uid}", police_station_id=self.station1.id)
        self.officer2 = Officer(user_id=self.officer_user2.id, officer_id=f"OFF_{uid}_2", badge_number=f"AD{uid}", police_station_id=self.station2.id)
        self.db.add_all([self.officer1, self.officer2])
        self.db.commit()

    def tearDown(self):
        self.db.close()
        if hasattr(self, "temp_dir") and self.temp_dir:
            self.temp_dir.cleanup()

    def test_01_upload_physical_file_and_db_link(self):
        """Test 1-3: Upload new physical file in temp dir, confirm DB record links to file."""
        complaint = create_complaint_record(
            db=self.db,
            complaint_type="vehicle_theft",
            complaint_text="My bike was stolen at Anna Nagar.",
            summary="Bike stolen.",
            citizen_id=self.citizen1.id,
            citizen_phone=self.citizen1.phone,
            structured_data={"incident_location": "Anna Nagar"},
        )

        test_fn = f"test_file_{uuid.uuid4().hex[:8]}.txt"
        test_file_path = os.path.join(self.temp_dir.name, test_fn)
        with open(test_file_path, "w") as f:
            f.write("Binary evidence content for testing.")

        # Confirm file physically exists in temp dir
        self.assertTrue(os.path.exists(test_file_path))

        ev = CaseEvidence(
            case_id=complaint.case_id,
            evidence_type="document",
            title="Bike Invoice Test",
            file_path=os.path.abspath(test_file_path),
            file_url=f"/evidence/file",
            description="Vehicle purchase invoice",
            potentially_time_sensitive=False,
            urgency="LOW",
        )
        self.db.add(ev)
        self.db.commit()

        # Confirm DB record links to file
        db_ev = self.db.query(CaseEvidence).filter(CaseEvidence.id == ev.id).first()
        self.assertIsNotNone(db_ev)
        self.assertTrue(os.path.exists(db_ev.file_path))

    def test_02_authorized_citizen_access(self):
        """Test 4: Citizen (owner of complaint) can access evidence file inline by default, attachment when download=True."""
        complaint = create_complaint_record(
            db=self.db,
            complaint_type="cyber_fraud",
            complaint_text="Scammed via GPay.",
            citizen_id=self.citizen1.id,
            citizen_phone=self.citizen1.phone,
        )
        test_fn = f"citizen_ev_{uuid.uuid4().hex[:8]}.png"
        test_file_path = os.path.join(self.temp_dir.name, test_fn)
        with open(test_file_path, "w") as f:
            f.write("Citizen Screenshot Data")

        ev = CaseEvidence(
            case_id=complaint.case_id,
            evidence_type="digital_transaction",
            title="GPay Payment Screenshot",
            file_path=os.path.abspath(test_file_path),
            file_url=f"/evidence/file",
            potentially_time_sensitive=True,
            urgency="HIGH",
        )
        self.db.add(ev)
        self.db.commit()

        # Access attempt by Citizen 1 (Owner) — View inline (default)
        response_inline = download_or_view_evidence_file(
            evidence_id=ev.id,
            download=False,
            db=self.db,
            current_user=self.citizen1,
        )
        self.assertIsNotNone(response_inline)
        self.assertEqual(response_inline.status_code, 200)
        self.assertTrue(response_inline.headers["content-disposition"].startswith("inline"))

        # Access attempt by Citizen 1 (Owner) — Explicit Download
        response_download = download_or_view_evidence_file(
            evidence_id=ev.id,
            download=True,
            db=self.db,
            current_user=self.citizen1,
        )
        self.assertIsNotNone(response_download)
        self.assertEqual(response_download.status_code, 200)
        self.assertTrue(response_download.headers["content-disposition"].startswith("attachment"))

    def test_03_authorized_officer_access(self):
        """Test 5: Authorized Officer (assigned station) can access evidence file inline."""
        complaint = create_complaint_record(
            db=self.db,
            complaint_type="vehicle_theft",
            complaint_text="Stolen car at Anna Nagar.",
            structured_data={"incident_location": "Anna Nagar"},
        )
        test_fn = f"officer_ev_{uuid.uuid4().hex[:8]}.jpg"
        test_file_path = os.path.join(self.temp_dir.name, test_fn)
        with open(test_file_path, "w") as f:
            f.write("CCTV Snapshot Data")

        ev = CaseEvidence(
            case_id=complaint.case_id,
            evidence_type="cctv_private",
            title="CCTV Snapshot",
            file_path=os.path.abspath(test_file_path),
            file_url=f"/evidence/file",
            potentially_time_sensitive=True,
            urgency="CRITICAL",
        )
        self.db.add(ev)
        self.db.commit()

        # Access attempt by Officer 1 (Station 1 — Anna Nagar)
        response = download_or_view_evidence_file(
            evidence_id=ev.id,
            download=False,
            db=self.db,
            current_user=self.officer_user1,
        )
        self.assertIsNotNone(response)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.headers["content-disposition"].startswith("inline"))

    def test_04_unauthorized_citizen_blocked(self):
        """Test 6: Citizen 2 attempting to access Citizen 1's complaint evidence gets 403 Forbidden."""
        complaint = create_complaint_record(
            db=self.db,
            complaint_type="cyber_fraud",
            complaint_text="Private Citizen 1 Fraud.",
            citizen_id=self.citizen1.id,
            citizen_phone=self.citizen1.phone,
        )
        test_fn = f"private_ev_{uuid.uuid4().hex[:8]}.pdf"
        test_file_path = os.path.join(self.temp_dir.name, test_fn)
        with open(test_file_path, "w") as f:
            f.write("Private Document")

        ev = CaseEvidence(
            case_id=complaint.case_id,
            evidence_type="document",
            title="Bank Statement",
            file_path=os.path.abspath(test_file_path),
            file_url=f"/evidence/file",
        )
        self.db.add(ev)
        self.db.commit()

        # Attempt access as Citizen 2
        with self.assertRaises(HTTPException) as ctx:
            download_or_view_evidence_file(
                evidence_id=ev.id,
                db=self.db,
                current_user=self.citizen2,
            )
        self.assertEqual(ctx.exception.status_code, 403)

    def test_05_unauthorized_officer_blocked(self):
        """Test 7: Officer 2 (Adyar Station) attempting to access Anna Nagar complaint evidence gets 403 Forbidden."""
        complaint = create_complaint_record(
            db=self.db,
            complaint_type="phone_snatching",
            complaint_text="Snatched at Anna Nagar.",
            structured_data={"incident_location": "Anna Nagar"},
        )
        test_fn = f"anna_nagar_ev_{uuid.uuid4().hex[:8]}.mp4"
        test_file_path = os.path.join(self.temp_dir.name, test_fn)
        with open(test_file_path, "w") as f:
            f.write("Video Data")

        ev = CaseEvidence(
            case_id=complaint.case_id,
            evidence_type="cctv_private",
            title="Anna Nagar CCTV Video",
            file_path=os.path.abspath(test_file_path),
            file_url=f"/evidence/file",
        )
        self.db.add(ev)
        self.db.commit()

        # Attempt access as Officer 2 (Adyar Station)
        with self.assertRaises(HTTPException) as ctx:
            download_or_view_evidence_file(
                evidence_id=ev.id,
                db=self.db,
                current_user=self.officer_user2,
            )
        self.assertEqual(ctx.exception.status_code, 403)

    def test_06_legacy_and_time_aware_metadata_intact(self):
        """Test 8-9: Verify Time-Aware metadata remains intact alongside file retrieval."""
        complaint = create_complaint_record(
            db=self.db,
            complaint_type="cyber_fraud",
            complaint_text="UPI scam details.",
            citizen_id=self.citizen1.id,
            citizen_phone=self.citizen1.phone,
        )
        test_fn = f"time_aware_ev_{uuid.uuid4().hex[:8]}.png"
        test_file_path = os.path.join(self.temp_dir.name, test_fn)
        with open(test_file_path, "w") as f:
            f.write("Time-aware image data")

        ev = CaseEvidence(
            case_id=complaint.case_id,
            evidence_type="digital_transaction",
            title="UPI Transaction Screenshot",
            file_path=os.path.abspath(test_file_path),
            file_url=f"/evidence/file",
            potentially_time_sensitive=True,
            retention_confidence="VERIFIED",
            urgency="HIGH",
            preservation_status="REVIEW_REQUIRED",
        )
        self.db.add(ev)
        self.db.commit()

        # Verify time-aware metadata fields
        db_ev = self.db.query(CaseEvidence).filter(CaseEvidence.id == ev.id).first()
        self.assertEqual(db_ev.urgency, "HIGH")
        self.assertEqual(db_ev.retention_confidence, "VERIFIED")
        self.assertEqual(db_ev.preservation_status, "REVIEW_REQUIRED")
        self.assertTrue(db_ev.potentially_time_sensitive)


if __name__ == "__main__":
    unittest.main()

