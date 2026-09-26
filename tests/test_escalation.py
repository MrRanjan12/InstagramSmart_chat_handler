import unittest
from backend.services.escalation.detector import EscalationDetector
from backend.services.escalation.engine import IntentEngine
from backend.constants import ASTRA, RANJAN


class TestEscalationDetector(unittest.TestCase):
    def setUp(self):
        self.detector = EscalationDetector()

    def test_english_escalation_detection(self):
        messages = ["Can I please speak to a human?", "I need support"]
        detected, matched = self.detector.detect(messages)
        self.assertTrue(detected)
        self.assertTrue(any(k in ["speak to a human", "human", "support"] for k in matched))

    def test_hinglish_escalation_detection(self):
        test_cases = [
            ["bhai asli ranjan se baat karni hai"],
            ["tum bot ho kya yaar?"],
            ["phone karo mujhe urgent"],
            ["kisi insan se connect kara do"],
        ]
        for msgs in test_cases:
            detected, matched = self.detector.detect(msgs)
            self.assertTrue(detected, f"Failed to detect escalation in: {msgs}")
            self.assertTrue(len(matched) > 0)

    def test_normal_casual_messages_not_escalated(self):
        normal_cases = [
            ["Hey Ranjan! Kaisa hai bhai?"],
            ["Python and FastAPI kaise seekhein?"],
            ["Nice reel, kaafi badhiya laga dekh ke"],
            ["Aur batao kya chal raha hai aajkal"],
        ]
        for msgs in normal_cases:
            detected, matched = self.detector.detect(msgs)
            self.assertFalse(detected, f"False positive escalation in: {msgs}")
            self.assertEqual(len(matched), 0)


class TestIntentEngine(unittest.TestCase):
    def setUp(self):
        self.engine = IntentEngine()

    def test_explicit_human_request(self):
        result = self.engine.analyze(["I want to talk to an agent please"])
        self.assertEqual(result.intent_score, 95)
        self.assertEqual(result.intent_classification, "human_assistance")
        self.assertTrue(result.human_request_detected)

    def test_general_query_scoring(self):
        result = self.engine.analyze(["Hey how are you?"])
        self.assertLess(result.intent_score, 40)
        self.assertEqual(result.intent_classification, "general_query")
        self.assertFalse(result.human_request_detected)

    def test_urgent_issue_scoring(self):
        result = self.engine.analyze(["Bhai bohot bada problem ho gaya hai urgent madad chahiye???"])
        self.assertGreaterEqual(result.intent_score, 40)
        self.assertLessEqual(result.intent_score, 79)
        self.assertEqual(result.intent_classification, "assistance_needed")
        self.assertFalse(result.human_request_detected)


if __name__ == "__main__":
    unittest.main()
