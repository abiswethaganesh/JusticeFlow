"""
Test multi-turn conversational intake question matching and answer persistence.
Verifies that once a requirement (e.g. accused description) is answered:
1. It updates the exact entity field.
2. Marks the requirement COMPLETED.
3. Recalculates missing requirements.
4. NEVER asks the exact same requirement again.
5. Auto-synthesizes Statement of Facts when all incident fields are complete.
"""
import sys
from pathlib import Path

# Force UTF-8 stdout
sys.stdout.reconfigure(encoding='utf-8')

backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.services.gemini_service import _fallback_analyze_intake, evaluate_required_fir_fields


def test_assault_multiturn_flow():
    print("==================================================")
    print("Testing Multi-Turn Follow-Up Answer Persistence")
    print("==================================================")

    history = []
    entities = {}

    # Turn 1: Initial complaint
    t1_text = "I was physically beaten up by someone near T. Nagar market yesterday evening."
    res1 = _fallback_analyze_intake(t1_text, history, entities)
    print("\nTurn 1 (User):", t1_text)
    print("  Classification:", res1["complaint_type"])
    print("  Missing Fields:", res1["missing_fields"])
    print("  AI Question:", res1["follow_up_questions"][0])

    history.append({"sender": "user", "text": t1_text})
    history.append({"sender": "ai", "text": res1["follow_up_questions"][0]})
    entities = res1["entities"]

    q1 = res1["follow_up_questions"][0]

    # Turn 2: User answers complainant_name
    t2_text = "Abi Swetha"
    res2 = _fallback_analyze_intake(t2_text, history, entities)
    print("\nTurn 2 (User Answer):", t2_text)
    print("  Extracted Complainant Name:", res2["entities"].get("complainant_name"))
    print("  Missing Fields:", res2["missing_fields"])
    print("  AI Question:", res2["follow_up_questions"][0])

    assert res2["entities"].get("complainant_name") == "Abi Swetha", "complainant_name should be set"
    assert "complainant_name" not in res2["missing_fields"], "complainant_name must be COMPLETED!"

    history.append({"sender": "user", "text": t2_text})
    history.append({"sender": "ai", "text": res2["follow_up_questions"][0]})
    entities = res2["entities"]

    # Turn 3: User answers complainant_phone
    t3_text = "9876543210"
    res3 = _fallback_analyze_intake(t3_text, history, entities)
    print("\nTurn 3 (User Answer):", t3_text)
    print("  Extracted Phone:", res3["entities"].get("complainant_phone"))
    print("  Missing Fields:", res3["missing_fields"])
    print("  AI Question:", res3["follow_up_questions"][0])

    assert res3["entities"].get("complainant_phone") == "9876543210", "complainant_phone should be set"
    assert "complainant_phone" not in res3["missing_fields"], "complainant_phone must be COMPLETED!"

    history.append({"sender": "user", "text": t3_text})
    history.append({"sender": "ai", "text": res3["follow_up_questions"][0]})
    entities = res3["entities"]

    # Turn 4: User answers victim_name
    t4_text = "Abi Swetha"
    res4 = _fallback_analyze_intake(t4_text, history, entities)
    print("\nTurn 4 (User Answer):", t4_text)
    print("  Extracted Victim Name:", res4["entities"].get("victim_name"))
    print("  Missing Fields:", res4["missing_fields"])
    print("  AI Question:", res4["follow_up_questions"][0])

    assert res4["entities"].get("victim_name") == "Abi Swetha", "victim_name should be set"
    assert "victim_name" not in res4["missing_fields"], "victim_name must be COMPLETED!"

    history.append({"sender": "user", "text": t4_text})
    history.append({"sender": "ai", "text": res4["follow_up_questions"][0]})
    entities = res4["entities"]

    q_accused = res4["follow_up_questions"][0]
    print(f"Target Accused Question asked: '{q_accused}'")

    # Turn 5: User answers accused description/identity
    t5_text = "It was a guy named Ramesh, wearing a black jacket and blue jeans around 25 years old."
    res5 = _fallback_analyze_intake(t5_text, history, entities)
    print("\nTurn 5 (User Answer):", t5_text)
    print("  Extracted Accused Info:", res5["entities"].get("accused_name_or_description"))
    print("  Missing Fields:", res5["missing_fields"])

    assert res5["entities"].get("accused_name_or_description") is not None, "accused_name_or_description must be persisted!"
    assert "accused_name_or_description" not in res5["missing_fields"], "accused_name_or_description must be COMPLETED!"

    q_next = res5["follow_up_questions"][0] if res5["follow_up_questions"] else None
    print(f"  Next AI Question asked: '{q_next}'")
    assert q_next != q_accused, "CRITICAL ERROR: AI asked the exact same question again!"

    history.append({"sender": "user", "text": t5_text})
    history.append({"sender": "ai", "text": q_next})
    entities = res5["entities"]

    # Turn 6: User answers final incident detail (injury_details)
    t6_text = "Bleeding from head, admitted and treated at Government Hospital."
    res6 = _fallback_analyze_intake(t6_text, history, entities)
    print("\nTurn 6 (User Answer - Final Requirement):", t6_text)
    print("  Extracted Injury Details:", res6["entities"].get("injury_details"))
    print("  Auto-Synthesized Statement of Facts:", res6["entities"].get("description"))
    print("  Final Missing Fields Count:", len(res6["missing_fields"]))
    print("  Follow-up Questions Count:", len(res6["follow_up_questions"]))

    assert res6["entities"].get("injury_details") is not None, "injury_details must be set"
    assert res6["entities"].get("description") is not None, "description MUST be auto-synthesized!"
    assert len(res6["missing_fields"]) == 0, "ALL missing fields must be 0 when complete!"
    assert len(res6["follow_up_questions"]) == 0, "No more follow-up questions when complete!"

    print("\n==================================================")
    print("ALL MULTI-TURN PERSISTENCE & AUTO-SYNTHESIS TESTS PASSED!")
    print("==================================================")


if __name__ == "__main__":
    test_assault_multiturn_flow()
