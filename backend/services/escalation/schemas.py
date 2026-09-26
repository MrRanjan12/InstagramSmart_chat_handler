from typing import List, Optional
from pydantic import BaseModel, Field


class IntentResult(BaseModel):
    intent_score: int = Field(..., ge=0, le=100)
    intent_classification: str
    human_request_detected: bool
    matched_keywords: List[str] = Field(default_factory=list)
    reason: Optional[str] = None


class EscalationEvaluation(BaseModel):
    should_ai_reply: bool
    current_mode: str
    was_escalated: bool = False
    intent_result: Optional[IntentResult] = None
    handoff_sent: bool = False
    reason: str


class ModeSwitchRequest(BaseModel):
    mode: str = Field(..., description="Target mode: ASTRA or RANJAN")


class StatusResponse(BaseModel):
    instagram_id: str
    current_mode: str
    is_human_active: bool
    user_id: int
    conversation_id: Optional[int] = None
