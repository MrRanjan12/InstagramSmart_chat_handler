from typing import List
from backend.services.escalation.detector import EscalationDetector
from backend.services.escalation.schemas import IntentResult


class IntentEngine:
    def __init__(self, detector: EscalationDetector = None):
        self.detector = detector or EscalationDetector()

    def analyze(self, messages: List[str]) -> IntentResult:
        """
        Main business logic for intent detection & scoring.
        Calculates score (0-100) and classifies user intent.
        """
        if not messages:
            return IntentResult(
                intent_score=10,
                intent_classification="general_query",
                human_request_detected=False,
                matched_keywords=[],
                reason="no_messages"
            )

        human_detected, matched_keywords = self.detector.detect(messages)

        if human_detected:
            return IntentResult(
                intent_score=95,
                intent_classification="human_assistance",
                human_request_detected=True,
                matched_keywords=matched_keywords,
                reason="explicit_human_request"
            )

        score = self._calculate_score(messages)
        classification = self._classify(score)

        return IntentResult(
            intent_score=score,
            intent_classification=classification,
            human_request_detected=False,
            matched_keywords=[],
            reason="standard_scoring"
        )

    # -----------------------------
    # Internal Scoring Logic
    # -----------------------------

    def _calculate_score(self, messages: List[str]) -> int:
        score = 10  # base score

        combined_text = " ".join(messages).lower()

        # Keyword boosts (English & Hinglish indicators of problem/urgency)
        urgency_keywords = [
            "help", "issue", "problem", "error", "urgent", "emergency",
            "support", "pareshan", "madad", "dikkat", "fraud", "scam",
            "not working", "kaam nahi kar raha", "fail", "kharab"
        ]

        if any(word in combined_text for word in urgency_keywords):
            score += 20

        # Query / Question indicator
        if "?" in combined_text:
            score += 10

        # High detail / complex message
        if len(combined_text) > 100:
            score += 10

        # Frustration / emphasis markers
        if "???" in combined_text or "!!!" in combined_text:
            score += 15

        # Check uppercase yelling in the latest message
        latest_message = messages[-1] if messages else ""
        if len(latest_message) > 15 and latest_message.isupper():
            score += 15

        # Cap before escalation threshold (80) unless triggered explicitly
        return min(score, 79)

    def _classify(self, score: int) -> str:
        if score < 40:
            return "general_query"
        elif score < 80:
            return "assistance_needed"
        return "human_assistance"
