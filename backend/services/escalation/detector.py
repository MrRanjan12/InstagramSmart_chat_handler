import re
from typing import List, Tuple, Set


# Standard English escalation keywords / phrases
ENGLISH_KEYWORDS: Set[str] = {
    "human",
    "person",
    "agent",
    "representative",
    "counselor",
    "counsellor",
    "support",
    "talk to someone",
    "speak to someone",
    "talk to a human",
    "speak to a human",
    "connect me",
    "real person",
    "manual reply",
    "call me",
    "call pe aao",
    "phone call",
}

# Hinglish / Hindi escalation keywords / phrases tailored for Ranjan's Instagram
HINGLISH_KEYWORDS: Set[str] = {
    "asli ranjan",
    "asli ho kya",
    "real ho kya",
    "bot ho kya",
    "robot ho kya",
    "ai ho kya",
    "kisi insan se",
    "kisi insaan se",
    "phone karo",
    "call karu",
    "number do",
    "asli banda",
    "bande se baat",
    "ranjan se baat karni",
    "khud reply karo",
    "asli banda baat kare",
}

ALL_KEYWORDS: Set[str] = ENGLISH_KEYWORDS | HINGLISH_KEYWORDS


class EscalationDetector:
    def __init__(self, custom_keywords: Set[str] = None):
        self.keywords = custom_keywords if custom_keywords is not None else ALL_KEYWORDS

    def detect(self, messages: List[str]) -> Tuple[bool, List[str]]:
        """
        Returns (is_detected, matched_keywords) if any human escalation intent is found.
        """
        if not messages:
            return False, []

        matched = []

        for msg in messages:
            if not msg:
                continue

            normalized = self._normalize(msg)

            for keyword in self.keywords:
                # Use regex word boundaries or phrase containment
                pattern = r"(^|\s|\W)" + re.escape(keyword) + r"($|\s|\W)"
                if re.search(pattern, normalized):
                    if keyword not in matched:
                        matched.append(keyword)

        return len(matched) > 0, matched

    def _normalize(self, text: str) -> str:
        """
        Normalizes text: lowercase, replaces multiple spaces with single space.
        """
        return re.sub(r"\s+", " ", text.lower().strip())
