from fastapi import APIRouter, HTTPException

from app.schemas.form import MissingFieldsRequest, MissingFieldsResponse
from app.services.form_schema_registry import get_schema
from app.services.form_service import get_missing_fields

router = APIRouter(prefix="/forms", tags=["forms"])


@router.post("/missing-fields", response_model=MissingFieldsResponse)
def missing_fields(request: MissingFieldsRequest):
    schema = get_schema(request.complaint_type)
    if schema is None:
        raise HTTPException(status_code=400, detail=f"Unknown complaint_type: {request.complaint_type}")

    entities_dict = request.entities or {}
    missing = get_missing_fields(request.complaint_type, entities_dict)

    return MissingFieldsResponse(
        form_id=schema["form_id"],
        required_fields=schema["required_fields"],
        missing_fields=missing,
    )

