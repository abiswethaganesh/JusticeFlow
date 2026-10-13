import unittest
from datetime import date
from app.services.gemini_service import _fallback_analyze_intake, _fallback_detect_time_sensitive_evidence

class TestClassificationFix(unittest.TestCase):

    def test_main_abuse_complaint(self):
        complaint = (
            "I witnessed a man verbally and physically abusing a woman on a public road near Anna Nagar today at around 6:30 PM. "
            "The man was shouting at her and hitting her. Several people were present at the location. "
            "There may also be CCTV cameras from nearby shops or buildings that captured the incident. "
            "I do not know either person's name. I happened to collect the CCTV footage."
        )
        res = _fallback_analyze_intake(complaint)
        self.assertNotEqual(res["complaint_type"], "property_theft", "Abuse complaint should not be property_theft")
        self.assertIn(res["complaint_type"], ["assault", "harassment"], "Should be classified as assault or harassment")
        
        entities = res.get("entities", {})
        self.assertEqual(entities.get("complainant_role"), "eyewitness", "Complainant role should be eyewitness")
        self.assertIsNotNone(entities.get("victim_name"), "Victim details should be extracted")
        self.assertIsNotNone(entities.get("accused_name_or_description"), "Accused details should be extracted")

        # Test evidence preservation scan
        items = _fallback_detect_time_sensitive_evidence(complaint, date.today().isoformat())
        cctv_item = next((item for item in items if "cctv" in str(item.get("evidence_type", "")).lower() or "cctv" in str(item.get("description", "")).lower()), None)
        self.assertIsNotNone(cctv_item, "CCTV evidence item should be detected by time-aware evidence preservation system")

    def test_variation_1_hitting(self):
        text = "I saw a man hitting a woman on the road."
        res = _fallback_analyze_intake(text)
        self.assertNotEqual(res["complaint_type"], "property_theft")
        self.assertEqual(res["complaint_type"], "assault")

    def test_variation_2_physically_attacked(self):
        text = "A man physically attacked another person outside a shop."
        res = _fallback_analyze_intake(text)
        self.assertNotEqual(res["complaint_type"], "property_theft")
        self.assertEqual(res["complaint_type"], "assault")

    def test_variation_3_punching(self):
        text = "I witnessed a fight where one person was repeatedly punching another."
        res = _fallback_analyze_intake(text)
        self.assertNotEqual(res["complaint_type"], "property_theft")
        self.assertEqual(res["complaint_type"], "assault")

    def test_variation_4_verbally_abused(self):
        text = "A woman was being verbally abused by a man."
        res = _fallback_analyze_intake(text)
        self.assertNotEqual(res["complaint_type"], "property_theft")
        self.assertIn(res["complaint_type"], ["harassment", "assault"])

    def test_variation_5_house_theft(self):
        text = "My house was broken into and my laptop was stolen."
        res = _fallback_analyze_intake(text)
        self.assertEqual(res["complaint_type"], "property_theft", "House break-in theft must still be property_theft")

if __name__ == "__main__":
    unittest.main()
