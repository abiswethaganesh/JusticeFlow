"""
Mock CCTNS (Crime and Criminal Tracking Network & Systems) Adapter.
Provides an integration layer to demonstrate official FIR submission and reference generation.
"""
import random
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models.complaint import Complaint
from app.models.fir_record import FIRRecord
from app.models.case_event import CaseEvent


def register_fir_with_cctns(
    db: Session,
    case_id: str,
    iif_data: dict,
    officer_user_id: int,
    officer_name: str = "Officer",
) -> FIRRecord:
    """
    Simulates official CCTNS registration for an FIR draft.
    Generates a unique CCTNS reference ID and updates case status.
    """
    complaint = db.query(Complaint).filter(Complaint.case_id == case_id).first()
    if not complaint:
        raise ValueError(f"No complaint found with case ID {case_id}")

    # Generate mock CCTNS reference ID
    random_digits = random.randint(100000, 999999)
    year = datetime.now(timezone.utc).year
    cctns_ref_id = f"CCTNS-TN-{year}-{random_digits}"
    fir_no = f"FIR/{year}/{complaint.assigned_station[:2].upper()}/{random.randint(1000, 9999)}"

    # Check if FIRRecord already exists
    fir = db.query(FIRRecord).filter(FIRRecord.case_id == case_id).first()
    if not fir:
        fir = FIRRecord(
            case_id=case_id,
            fir_number=fir_no,
            iif_data=iif_data,
            status="REGISTERED_OFFICIAL",
            registered_by_officer_id=officer_user_id,
            official_cctns_ref_id=cctns_ref_id,
        )
        db.add(fir)
    else:
        fir.status = "REGISTERED_OFFICIAL"
        fir.official_cctns_ref_id = cctns_ref_id
        fir.iif_data = iif_data
        fir.registered_by_officer_id = officer_user_id

    # Update complaint status to INVESTIGATION
    prev_status = complaint.status
    complaint.status = "INVESTIGATION"
    complaint.workflow_type = "official_fir_registered"

    # Add audit log in case_events
    event = CaseEvent(
        case_id=case_id,
        previous_status=prev_status,
        new_status="INVESTIGATION",
        changed_by_user_id=officer_user_id,
        actor_name=officer_name,
        actor_role="OFFICER",
        remarks=f"FIR registered in Official CCTNS System. Reference ID: {cctns_ref_id}",
    )
    db.add(event)

    db.commit()
    db.refresh(fir)
    db.refresh(complaint)

    return fir
