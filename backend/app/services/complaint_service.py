"""
Sits between the router and gemini_service. For Phase B this just
calls Gemini and hands back the parsed dict — deterministic logic
like "which fields are missing" gets added here in Phase C, so this
file is deliberately small right now.
"""
from app.services.gemini_service import extract_complaint_entities, GeminiUnavailableError

__all__ = ["extract_complaint_entities", "GeminiUnavailableError"]


def analyze_complaint(complaint_text: str) -> dict:
    complaint_text = complaint_text.strip()
    if not complaint_text:
        raise ValueError("complaint_text must not be empty.")
    return extract_complaint_entities(complaint_text)
