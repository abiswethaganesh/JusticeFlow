"""
Deterministic Python comparison — no Gemini involved here, per the
project rules (field comparison must not depend on the AI call).
"""
from app.services.form_schema_registry import get_schema
from app.services.gemini_service import evaluate_required_fir_fields


def get_missing_fields(complaint_type: str, entities: dict) -> list[str]:
    """
    Returns the list of required field names that are missing (null,
    absent, or blank) for a given complaint type.
    Uses the exact same single source of truth validation as the intake engine.
    """
    schema = get_schema(complaint_type)
    if schema is None:
        return []

    missing, _ = evaluate_required_fir_fields(complaint_type, entities)
    return missing

