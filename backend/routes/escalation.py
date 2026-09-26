from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from backend.database import get_db
from backend.constants import ASTRA, RANJAN
from backend.services.escalation.service import escalation_service
from backend.services.escalation.engine import IntentEngine
from backend.services.escalation.schemas import (
    IntentResult,
    StatusResponse,
    ModeSwitchRequest
)
from pydantic import BaseModel

router = APIRouter(prefix="/api/escalation", tags=["Escalation & Mode Switching"])
intent_engine = IntentEngine()


class TestIntentRequest(BaseModel):
    messages: List[str]


class ModeSwitchResponse(BaseModel):
    instagram_id: str
    previous_mode: str
    new_mode: str
    message: str


@router.get("/status/{instagram_id}", response_model=StatusResponse)
def get_user_status(instagram_id: str, db: Session = Depends(get_db)):
    """
    Get current mode (ASTRA or RANJAN) for an Instagram user.
    """
    status = escalation_service.get_user_status(db, instagram_id)
    if not status:
        raise HTTPException(status_code=404, detail="User not found")
    return status


@router.post("/switch/{instagram_id}", response_model=ModeSwitchResponse)
def switch_mode(instagram_id: str, req: ModeSwitchRequest, db: Session = Depends(get_db)):
    """
    Manually switch conversation mode between ASTRA (AI) and RANJAN (Human).
    """
    status = escalation_service.get_user_status(db, instagram_id)
    if not status:
        raise HTTPException(status_code=404, detail="User not found")

    target_mode = req.mode.upper().strip()
    if target_mode not in (ASTRA, RANJAN):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid mode: '{req.mode}'. Must be '{ASTRA}' or '{RANJAN}'."
        )

    previous_mode = status["current_mode"]
    escalation_service.switch_user_mode(db, instagram_id, target_mode)

    return {
        "instagram_id": instagram_id,
        "previous_mode": previous_mode,
        "new_mode": target_mode,
        "message": f"Successfully switched user to {target_mode} mode."
    }


@router.post("/reset/{instagram_id}", response_model=ModeSwitchResponse)
def reset_to_ai(instagram_id: str, db: Session = Depends(get_db)):
    """
    Reset conversation back to AI (ASTRA) mode.
    """
    status = escalation_service.get_user_status(db, instagram_id)
    if not status:
        raise HTTPException(status_code=404, detail="User not found")

    previous_mode = status["current_mode"]
    escalation_service.reset_to_ai(db, instagram_id)

    return {
        "instagram_id": instagram_id,
        "previous_mode": previous_mode,
        "new_mode": ASTRA,
        "message": "Conversation successfully reset back to AI (ASTRA) mode."
    }


@router.post("/test-intent", response_model=IntentResult)
def test_intent_analysis(req: TestIntentRequest):
    """
    Test messages against the Intent Scoring & Escalation Detector without modifying DB.
    """
    return intent_engine.analyze(req.messages)
