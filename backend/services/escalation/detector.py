import re
from typing import List, Tuple, Set
from backend.config import config


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
    "talk to a person",
    "speak to a person",
    "talk to agent",
    "speak to agent",
    "connect me",
    "real person",
    "live agent",
    "customer support",
    "customer care",
    "manual reply",
    "call me",
    "call pe aao",
    "phone call",
    "stop bot",
    "turn off bot",
}

# Hinglish / Hindi escalation keywords / phrases tailored for Ranjan's Instagram
HINGLISH_KEYWORDS: Set[str] = {
    "asli ranjan",
    "real ranjan",
    "asli ho kya",
    "real ho kya",
    "bot ho kya",
    "robot ho kya",
    "ai ho kya",
    "kisi insan se",
    "kisi insaan se",
    "phone karo",
    "call karo",
    "call karu",
    "number do",
    "apna number",
    "asli banda",
    "bande se baat",
    "ranjan se baat",
    "ranjan se baat karni",
    "ranjan se call",
    "khud reply karo",
    "asli banda baat kare",
    "bot band karo",
    "bot band",
}

ALL_KEYWORDS: Set[str] = ENGLISH_KEYWORDS | HINGLISH_KEYWORDS


class EscalationDetector:
    def __init__(self, custom_keywords: Set[str] = None):
        if custom_keywords is not None:
            self.keywords = custom_keywords
        else:
            self.keywords = set(ALL_KEYWORDS)
            # Incorporate any custom keywords from configuration / .env
            env_keywords = getattr(config, "HUMAN_HANDOFF_KEYWORDS", "")
            if env_keywords:
                for kw in env_keywords.split(","):
                    cleaned = kw.strip().lower()
                    if cleaned:
                        self.keywords.add(cleaned)


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
