from fastapi import APIRouter, HTTPException
from app.schemas.complaint import ConversationalIntakeRequest, ConversationalIntakeResponse
from app.services.gemini_service import analyze_conversational_intake, GeminiUnavailableError

router = APIRouter(prefix="/intake", tags=["intake"])


@router.post("/analyze", response_model=ConversationalIntakeResponse)
def analyze_intake(request: ConversationalIntakeRequest):
    if not request.complaint_text or not request.complaint_text.strip():
        raise HTTPException(status_code=400, detail="complaint_text is required.")

    try:
        res = analyze_conversational_intake(
            complaint_text=request.complaint_text,
            conversation_history=request.conversation_history,
            previous_entities=request.previous_entities,
        )
        return res
    except GeminiUnavailableError as e:
        raise HTTPException(
            status_code=503,
            detail="Conversational AI Engine is temporarily unavailable. Please try again.",
        ) from e
