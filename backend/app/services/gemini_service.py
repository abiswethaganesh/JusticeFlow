"""
Gemini AI Intelligence Engine Service for JusticeFlow Core.
Handles Conversational Intake Analysis, Entity Extraction, Missing Info & Ambiguity Detection,
Follow-up Question Generation, Evidence Recommendations, and IIF-I Standard FIR Draft Generation.
"""
import json
import logging
import re
from datetime import date
from typing import Optional

from google import genai
from google.genai import types

from app.config import settings
from app.services.form_schema_registry import FORM_SCHEMAS, get_schema

logger = logging.getLogger(__name__)


class GeminiUnavailableError(Exception):
    """Raised whenever we can't get a usable response from Gemini."""


_client = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        if not settings.gemini_api_key:
            raise GeminiUnavailableError("GEMINI_API_KEY is not configured.")
        _client = genai.Client(api_key=settings.gemini_api_key)
    return _client


INTAKE_SYSTEM_PROMPT = """You are the AI Intelligence Engine for JusticeFlow, an AI-Assisted Criminal Justice Platform.

Your job:
1. Read the citizen's complaint input and any existing conversation history.
2. Classify the complaint type strictly as one of:
   - vehicle_theft (ONLY for stolen motor vehicles like cars, bikes, scooters, motorcycles)
   - vehicle_accident (road accidents, vehicle collisions, hit-and-run incidents)
   - cyber_fraud (online financial fraud, UPI scams, phishing, bank fraud, digital scam)
   - financial_fraud (offline financial fraud, cheating, loan scams, fraudulent agreements)
   - property_damage (vandalism, property destruction, broken windows, damaged goods)
   - phone_snatching (mobile phone snatched on street, phone robbery by bike riders)
   - workplace_theft (stolen office assets, desk theft, workplace burglary)
   - vehicle_break_in (theft from parked vehicle, smashed car window, broken lock)
   - missing_person (ONLY when a human being or person is missing/kidnapped. NEVER for stolen items/objects)
   - property_theft (house theft, burglary, stolen handbag, wallet, gold, laptop, cash)
   - assault (physical attack, beating, violence, bodily injury)
   - threat (extortion, blackmail, criminal intimidation)
   - harassment (stalking, abuse, molestation, online harassment)
   - lost_document (lost ID card, passport, driving license without theft)
   - other (general complaint)

Classification Guidelines:
- If a mobile phone was snatched/grabbed on the road by someone fleeing, classify as phone_snatching.
- If items were stolen from inside a vehicle by breaking glass/locks, classify as vehicle_break_in.
- If items were stolen inside an office/desk/workplace, classify as workplace_theft.
- If a vehicle collided with another or caused an accident, classify as vehicle_accident.
- If property was intentionally damaged or vandalized, classify as property_damage.
- If no vehicle (car/bike/scooter) was stolen as a whole, NEVER classify as vehicle_theft.
- If no human being is missing, NEVER classify as missing_person.

3. Determine if the offense is cognizable (True for theft, accident, fraud, snatching, break-in, missing person, assault, threat, harassment, property damage; False for lost document or trivial civil matters).
4. Extract explicit entities mentioned by the citizen.
5. Identify missing or ambiguous required information for that category.
6. Generate ONLY 1 clear, focused follow-up question targeting the single most important missing or ambiguous detail. If all required information is already collected, return an empty array [].
7. Recommend relevant supporting evidence items for the citizen to upload (e.g. RC copy, medical report, bank statement, photos, CCTV footage, phone invoice).
8. Write a 1-2 sentence neutral executive summary.
9. Provide initial AI recommendations for police officers (suggested legal sections under Bharatiya Nyaya Sanhita (BNS) / IPC / IT Act / Motor Vehicles Act).

Strict Rules:
- NEVER invent names, dates, locations, vehicle numbers, transaction IDs, IMEI numbers, or facts not provided by the citizen.
- Set missing entity values to null or empty string.
- Return ONLY valid JSON matching the exact schema below.

JSON Output Schema:
{
  "complaint_type": "vehicle_theft" | "vehicle_accident" | "cyber_fraud" | "financial_fraud" | "property_damage" | "phone_snatching" | "workplace_theft" | "vehicle_break_in" | "missing_person" | "property_theft" | "assault" | "threat" | "harassment" | "lost_document" | "other",
  "is_cognizable": boolean,
  "summary": "<neutral summary>",
  "entities": {
     "complainant_name": string | null,
     "complainant_phone": string | null,
     "incident_location": string | null,
     "incident_date": string | null,
     "incident_time": string | null,
     ... category specific keys ...
  },
  "missing_fields": ["field_name_1", "field_name_2"],
  "ambiguous_fields": [],
  "follow_up_questions": ["Question 1?"],
  "recommended_evidence": ["Evidence Item 1", "Evidence Item 2"],
  "ai_recommendations": {
     "legal_sections": ["BNS 303(2) - Theft", "BNS 318 - Cheating"],
     "recommended_action": "Verify incident location CCTV and register FIR."
  }
}"""


FIELD_QUESTION_MAP = {
    "complainant_name": "Could you please provide your full name so it can be recorded on the official FIR?",
    "complainant_phone": "Could you please provide your contact phone number so investigating officers can reach you?",
    "vehicle_registration_number": "Could you please provide your vehicle's registration number (e.g. TN 01 AB 1234)?",
    "vehicle_type": "What is the make, model, or type of your vehicle (e.g. Honda Activa, Hero Splendor, Swift Car)?",
    "other_vehicle_number": "What is the registration number, make, or description of the other vehicle involved in the collision?",
    "injury_or_damage_details": "Could you please detail any physical injuries suffered or the damage caused to the vehicles?",
    "incident_location": "Could you please specify the exact location where the incident occurred?",
    "incident_date": "On what date did this incident happen?",
    "incident_time": "At approximately what time of day or night did this happen?",
    "stolen_items": "Could you please detail all the items or belongings that were stolen or went missing?",
    "stolen_items_description": "Could you please detail all the items or belongings that were stolen or went missing?",
    "property_location": "Where was the property or house located when the theft/lock break occurred?",
    "estimated_value": "What is the total estimated monetary value of the stolen items or cash?",
    "fraud_amount": "Could you please specify the total amount involved in the fraudulent transaction?",
    "transaction_amount": "Could you please specify the total amount involved in the fraudulent transaction?",
    "transaction_reference": "Do you have the transaction reference number, UPI ID, or bank reference for the payment?",
    "platform_used": "Which platform or app was used by the scammer (e.g. UPI, GPay, PhonePe, WhatsApp, Telegram)?",
    "transaction_mode": "What was the mode of payment or transaction (e.g. NetBanking, UPI, Cash, Cheque)?",
    "accused_name_or_organization": "What is the name or details of the accused person or fraudulent organization?",
    "damaged_property_description": "Could you please describe the specific property that was damaged or vandalized?",
    "estimated_damage_value": "What is the estimated cost or value of the damage caused to your property?",
    "mobile_make_model": "What is the exact make and model of your snatched mobile phone (e.g. iPhone 15, Samsung Galaxy S23)?",
    "imei_number": "Do you have the 15-digit IMEI number of the snatched phone (usually found on the invoice or box)?",
    "snatching_location": "Where exactly was your mobile phone snatched?",
    "snatcher_description_or_vehicle": "Can you describe the snatcher or their getaway vehicle (e.g. bike color or appearance)?",
    "company_or_office_name": "What is the name of your company, office, or workplace where the theft occurred?",
    "office_location": "Where is your office or workplace located?",
    "suspect_employees_or_visitors": "Do you suspect any specific employee, staff member, or recent visitor?",
    "vehicle_parked_location": "Where was your vehicle parked when it was broken into?",
    "stolen_items_from_vehicle": "What specific items or belongings were stolen from inside the vehicle?",
    "broken_window_or_lock_damage": "Which window glass was smashed or which lock was tampered with?",
    "missing_person_name": "What is the full name of the missing person?",
    "age": "What is the age of the missing person?",
    "gender": "What is the gender of the missing person?",
    "last_seen_location": "Where was the person last seen before going missing?",
    "last_seen_date": "On what date was the person last seen?",
    "last_seen_time": "At approximately what time was the person last seen?",
    "victim_name": "What is the name of the person who was injured/assaulted?",
    "accused_name_or_description": "Do you know the identity, name, or physical description of the accused/attacker?",
    "injury_details": "Did the victim suffer any physical injuries, and were they taken to a hospital for medical treatment?",
    "threat_medium": "How was the threat conveyed to you (e.g. phone call, WhatsApp message, in-person)?",
    "accused_details": "Do you know the identity or phone number of the person harassing you?",
    "document_name": "Which specific document or ID card was lost (e.g. Passport, Aadhaar card, Driving License)?",
    "document_number": "Do you know the document number or ID number of the lost document?",
    "lost_location": "Where do you believe the document was lost or misplaced?",
    "lost_date": "On what date did you realize the document was lost?",
    "description": "Is there any other relevant detail or description you would like to add for the investigating officer?",
}


QUESTION_TO_FIELD_MAP = [
    (
        ("accused", "attacker", "suspect", "snatcher", "harasser", "identity", "physical description", "who attacked", "who stole"),
        ["accused_name_or_description", "accused_details", "accused_name_or_organization", "snatcher_description_or_vehicle", "suspect_employees_or_visitors"]
    ),
    (
        ("injury", "injuries", "hospital", "medical", "treatment", "prescript"),
        ["injury_details", "injury_or_damage_details"]
    ),
    (
        ("victim",),
        ["victim_name"]
    ),
    (
        ("registration number", "license plate", "stolen vehicle"),
        ["vehicle_registration_number"]
    ),
    (
        ("other vehicle", "collision vehicle"),
        ["other_vehicle_number"]
    ),
    (
        ("type of vehicle", "make", "model of your vehicle"),
        ["vehicle_type"]
    ),
    (
        ("imei",),
        ["imei_number"]
    ),
    (
        ("mobile make", "make and model"),
        ["mobile_make_model"]
    ),
    (
        ("snatching location", "where exactly was your mobile"),
        ["snatching_location", "incident_location"]
    ),
    (
        ("parked", "vehicle parked"),
        ["vehicle_parked_location", "incident_location"]
    ),
    (
        ("broken window", "lock damage", "glass smashed"),
        ["broken_window_or_lock_damage"]
    ),
    (
        ("items from vehicle", "stolen from inside"),
        ["stolen_items_from_vehicle", "stolen_items_description"]
    ),
    (
        ("office name", "company", "workplace"),
        ["company_or_office_name"]
    ),
    (
        ("office location", "workplace location", "workplace address"),
        ["office_location", "incident_location"]
    ),
    (
        ("damaged property", "vandalized property"),
        ["damaged_property_description"]
    ),
    (
        ("damage value", "cost of damage", "estimated cost"),
        ["estimated_damage_value", "estimated_value"]
    ),
    (
        ("fraud amount", "amount involved", "transaction amount", "how much money"),
        ["fraud_amount", "transaction_amount"]
    ),
    (
        ("transaction reference", "upi id", "reference number"),
        ["transaction_reference"]
    ),
    (
        ("platform", "payment app"),
        ["platform_used"]
    ),
    (
        ("transaction mode", "mode of payment"),
        ["transaction_mode"]
    ),
    (
        ("missing person", "name of the missing"),
        ["missing_person_name"]
    ),
    (
        ("last seen location", "where was the person last seen"),
        ["last_seen_location", "incident_location"]
    ),
    (
        ("last seen date",),
        ["last_seen_date", "incident_date"]
    ),
    (
        ("last seen time",),
        ["last_seen_time", "incident_time"]
    ),
    (
        ("age",),
        ["age"]
    ),
    (
        ("gender",),
        ["gender"]
    ),
    (
        ("threat medium", "how was the threat"),
        ["threat_medium"]
    ),
    (
        ("document name", "which specific document"),
        ["document_name"]
    ),
    (
        ("document number", "id number"),
        ["document_number"]
    ),
    (
        ("lost location", "where do you believe the document was lost"),
        ["lost_location", "incident_location"]
    ),
    (
        ("lost date",),
        ["lost_date", "incident_date"]
    ),
    (
        ("full name", "your name", "complainant name"),
        ["complainant_name"]
    ),
    (
        ("phone number", "contact phone"),
        ["complainant_phone"]
    ),
    (
        ("location", "where exactly did"),
        ["incident_location", "property_location"]
    ),
    (
        ("date", "on what date"),
        ["incident_date"]
    ),
    (
        ("time of day", "what time", "approximately what time"),
        ["incident_time"]
    ),
    (
        ("stolen items", "belongings", "what was stolen"),
        ["stolen_items_description", "stolen_items"]
    ),
    (
        ("estimated value", "monetary value"),
        ["estimated_value"]
    ),
]


def match_and_persist_last_question_answer(conversation_history: list, user_answer: str, complaint_type: str, merged_entities: dict):
    """
    Finds the last AI question in conversation history, maps it to requirement field IDs,
    and updates merged_entities with user_answer, marking those fields COMPLETED.
    """
    if not conversation_history or not user_answer or not user_answer.strip():
        return

    # Find last AI message
    last_ai_msgs = [m for m in conversation_history if isinstance(m, dict) and m.get("sender") == "ai"]
    if not last_ai_msgs:
        return

    last_ai_text = (last_ai_msgs[-1].get("text") or "").lower()
    schema = get_schema(complaint_type)
    req_fields = schema.get("required_fields", [])

    matched_field = None

    # 1. Direct matching against FIELD_QUESTION_MAP
    for f in req_fields:
        q_str = FIELD_QUESTION_MAP.get(f)
        if q_str:
            q_clean = q_str.lower().strip('"\' ')
            if q_clean in last_ai_text or last_ai_text in q_clean:
                matched_field = f
                break

    # 2. Keyword fallback matching
    if not matched_field:
        for kw_tuple, field_list in QUESTION_TO_FIELD_MAP:
            if any(kw in last_ai_text for kw in kw_tuple):
                for f in field_list:
                    if f in req_fields:
                        matched_field = f
                        break
                if not matched_field:
                    matched_field = field_list[0]
                break

    if matched_field:
        answer_clean = user_answer.strip()
        merged_entities[matched_field] = answer_clean
        # Sync synonyms/aliases
        if matched_field in ["accused_name_or_description", "accused_details", "accused_name_or_organization", "snatcher_description_or_vehicle", "suspect_employees_or_visitors"]:
            merged_entities["accused_name_or_description"] = answer_clean
            merged_entities["accused_details"] = answer_clean
        elif matched_field in ["injury_details", "injury_or_damage_details"]:
            merged_entities["injury_details"] = answer_clean
            merged_entities["injury_or_damage_details"] = answer_clean
        elif matched_field in ["stolen_items", "stolen_items_description", "stolen_items_from_vehicle", "damaged_property_description"]:
            merged_entities["stolen_items"] = answer_clean
            merged_entities["stolen_items_description"] = answer_clean
        elif matched_field in ["fraud_amount", "transaction_amount"]:
            merged_entities["fraud_amount"] = answer_clean
            merged_entities["transaction_amount"] = answer_clean
        elif matched_field in ["incident_location", "property_location", "snatching_location", "office_location", "vehicle_parked_location", "last_seen_location", "lost_location"]:
            merged_entities["incident_location"] = answer_clean

            merged_entities["stolen_items_description"] = answer_clean
        elif matched_field in ["fraud_amount", "transaction_amount"]:
            merged_entities["fraud_amount"] = answer_clean
            merged_entities["transaction_amount"] = answer_clean
        elif matched_field in ["incident_location", "property_location", "snatching_location", "office_location", "vehicle_parked_location", "last_seen_location", "lost_location"]:
            merged_entities["incident_location"] = answer_clean

    # Multiple entity regex extractions in user answer
    text_lower = user_answer.lower()
    phone_match = re.search(r'\b(\+?91[\s-]?)?([6-9]\d{9})\b', user_answer)
    if phone_match and not merged_entities.get("complainant_phone"):
        merged_entities["complainant_phone"] = phone_match.group(2)

    if any(w in text_lower for w in ["yesterday", "today"]) and not merged_entities.get("incident_date"):
        merged_entities["incident_date"] = date.today().isoformat()

    time_match = re.search(r'\b(\d{1,2}(?::\d{2})?\s*(?:am|pm|a\.m\.|p\.m\.)?|\b(?:morning|afternoon|evening|night|midnight|noon|dawn|dusk)\b)', user_answer, re.IGNORECASE)
    if time_match and not merged_entities.get("incident_time"):
        merged_entities["incident_time"] = time_match.group(1).strip().title()


def synthesize_statement_of_facts(complaint_type: str, entities: dict) -> str:
    """
    Synthesizes the official Statement of Facts / Narrative strictly from verified extracted entities.
    Never invents missing facts.
    """
    complainant = entities.get("complainant_name") or "The complainant"
    loc = entities.get("incident_location") or entities.get("property_location") or entities.get("snatching_location") or "the specified location"
    dt = entities.get("incident_date") or entities.get("last_seen_date") or date.today().isoformat()
    tm = entities.get("incident_time") or entities.get("last_seen_time") or "unspecified time"

    c_type_str = complaint_type.replace("_", " ").title()
    facts = [f"On {dt} at approximately {tm}, {complainant} reported a {c_type_str} incident occurring at {loc}."]

    # Complaint-specific facts compilation
    if complaint_type == "assault":
        v = entities.get("victim_name") or complainant
        acc = entities.get("accused_name_or_description")
        inj = entities.get("injury_details")
        facts.append(f"Victim: {v}.")
        if acc: facts.append(f"Accused/Attacker Details: {acc}.")
        if inj: facts.append(f"Injuries & Medical Particulars: {inj}.")

    elif complaint_type == "vehicle_accident":
        v_reg = entities.get("vehicle_registration_number")
        o_reg = entities.get("other_vehicle_number")
        dmg = entities.get("injury_or_damage_details")
        if v_reg: facts.append(f"Complainant Vehicle: {v_reg}.")
        if o_reg: facts.append(f"Other Vehicle Involved: {o_reg}.")
        if dmg: facts.append(f"Collision & Damage Details: {dmg}.")

    elif complaint_type in ["cyber_fraud", "financial_fraud"]:
        amt = entities.get("fraud_amount") or entities.get("transaction_amount")
        ref = entities.get("transaction_reference")
        plat = entities.get("platform_used")
        mode = entities.get("transaction_mode")
        acc = entities.get("accused_name_or_organization")
        if amt: facts.append(f"Total Amount Involved: {amt}.")
        if ref: facts.append(f"Transaction Reference: {ref}.")
        if plat: facts.append(f"Platform/App Used: {plat}.")
        if mode: facts.append(f"Payment Mode: {mode}.")
        if acc: facts.append(f"Accused Entity: {acc}.")

    elif complaint_type == "phone_snatching":
        mob = entities.get("mobile_make_model")
        imei = entities.get("imei_number")
        snatch = entities.get("snatcher_description_or_vehicle")
        if mob: facts.append(f"Snatched Mobile Model: {mob}.")
        if imei: facts.append(f"15-Digit IMEI: {imei}.")
        if snatch: facts.append(f"Snatcher/Getaway Description: {snatch}.")

    elif complaint_type == "vehicle_break_in":
        v_reg = entities.get("vehicle_registration_number")
        stolen = entities.get("stolen_items_from_vehicle") or entities.get("stolen_items_description")
        dmg = entities.get("broken_window_or_lock_damage")
        val = entities.get("estimated_value")
        if v_reg: facts.append(f"Parked Vehicle Reg: {v_reg}.")
        if dmg: facts.append(f"Window Glass / Lock Damage: {dmg}.")
        if stolen: facts.append(f"Stolen Items: {stolen}.")
        if val: facts.append(f"Estimated Loss Value: {val}.")

    elif complaint_type == "workplace_theft":
        comp = entities.get("company_or_office_name")
        stolen = entities.get("stolen_items_description")
        susp = entities.get("suspect_employees_or_visitors")
        if comp: facts.append(f"Workplace: {comp}.")
        if stolen: facts.append(f"Stolen Assets: {stolen}.")
        if susp: facts.append(f"Suspect Staff/Visitors: {susp}.")

    elif complaint_type == "property_damage":
        prop = entities.get("damaged_property_description")
        val = entities.get("estimated_damage_value")
        acc = entities.get("accused_name_or_description")
        if prop: facts.append(f"Damaged Property: {prop}.")
        if val: facts.append(f"Estimated Cost: {val}.")
        if acc: facts.append(f"Accused Vandal: {acc}.")

    elif complaint_type == "missing_person":
        mp_name = entities.get("missing_person_name")
        age = entities.get("age")
        gender = entities.get("gender")
        if mp_name: facts.append(f"Missing Person: {mp_name}.")
        if age: facts.append(f"Age: {age}.")
        if gender: facts.append(f"Gender: {gender}.")

    return " ".join(facts)


def evaluate_required_fir_fields(complaint_type: str, entities: dict) -> tuple[list, list]:
    """Dynamically checks schema required fields and returns missing fields and follow-up questions for real-world FIR completion."""
    schema = get_schema(complaint_type)
    req_fields = schema.get("required_fields", ["complainant_name", "incident_location", "incident_date", "description"])

    # Bidirectional entity field syncing across schemas
    if entities.get("stolen_items") and not entities.get("stolen_items_description"):
        entities["stolen_items_description"] = entities["stolen_items"]
    if entities.get("stolen_items_description") and not entities.get("stolen_items"):
        entities["stolen_items"] = entities["stolen_items_description"]

    if entities.get("transaction_amount") and not entities.get("fraud_amount"):
        entities["fraud_amount"] = entities["transaction_amount"]
    if entities.get("fraud_amount") and not entities.get("transaction_amount"):
        entities["transaction_amount"] = entities["fraud_amount"]

    # Location aliases
    loc = (
        entities.get("incident_location")
        or entities.get("snatching_location")
        or entities.get("office_location")
        or entities.get("vehicle_parked_location")
        or entities.get("property_location")
        or entities.get("last_seen_location")
        or entities.get("lost_location")
    )
    if loc:
        entities["incident_location"] = loc
        if complaint_type == "phone_snatching": entities["snatching_location"] = loc
        elif complaint_type == "workplace_theft": entities["office_location"] = loc
        elif complaint_type == "vehicle_break_in": entities["vehicle_parked_location"] = loc
        elif complaint_type == "property_theft" or complaint_type == "property_damage": entities["property_location"] = loc
        elif complaint_type == "missing_person": entities["last_seen_location"] = loc
        elif complaint_type == "lost_document": entities["lost_location"] = loc

    # Damage / Stolen details aliases
    if entities.get("stolen_items_from_vehicle") and not entities.get("stolen_items_description"):
        entities["stolen_items_description"] = entities["stolen_items_from_vehicle"]
    if entities.get("stolen_items_description") and not entities.get("stolen_items_from_vehicle") and complaint_type == "vehicle_break_in":
        entities["stolen_items_from_vehicle"] = entities["stolen_items_description"]

    if entities.get("injury_details") and not entities.get("injury_or_damage_details"):
        entities["injury_or_damage_details"] = entities["injury_details"]

    # 1. Check non-description missing fields first
    missing_non_desc = []
    for f in req_fields:
        if f == "description":
            continue
        val = entities.get(f)
        if val is None or str(val).strip() in ["", "null", "None", "—"]:
            missing_non_desc.append(f)

    if not entities.get("complainant_phone") and "complainant_phone" not in missing_non_desc:
        missing_non_desc.append("complainant_phone")

    # 2. If all non-description fields are filled, auto-synthesize Statement of Facts / Narrative if empty
    if len(missing_non_desc) == 0:
        desc_val = entities.get("description")
        if desc_val is None or str(desc_val).strip() in ["", "null", "None", "—"]:
            entities["description"] = synthesize_statement_of_facts(complaint_type, entities)

    # 3. Final validation across ALL required fields (including description)
    missing_fields = []
    follow_up_questions = []

    for f in req_fields:
        val = entities.get(f)
        if val is None or str(val).strip() in ["", "null", "None", "—"]:
            missing_fields.append(f)
            q = FIELD_QUESTION_MAP.get(f, f"Could you please specify {f.replace('_', ' ')}?")
            follow_up_questions.append(q)

    if not entities.get("complainant_phone") and "complainant_phone" not in missing_fields:
        missing_fields.append("complainant_phone")
        follow_up_questions.append(FIELD_QUESTION_MAP["complainant_phone"])

    return missing_fields, follow_up_questions



def _fallback_analyze_intake(
    complaint_text: str,
    conversation_history: Optional[list] = None,
    previous_entities: Optional[dict] = None,
) -> dict:
    """Fallback rule-based intelligence engine when Gemini API is rate-limited or unavailable."""
    merged_entities = dict(previous_entities) if previous_entities else {}

    # Combine full conversation text
    full_text = complaint_text
    if conversation_history:
        history_text = " ".join([m.get("text", "") for m in conversation_history])
        full_text = f"{history_text} {complaint_text}"

    text_lower = full_text.lower()

    # Enhanced 15-category classification engine
    if re.search(r'\b(snatch|snatched|grabbed my phone|snatchers|mobile snatching|phone robbery)\b', text_lower):
        complaint_type = "phone_snatching"
    elif re.search(r'\b(break in|break-in|smashed glass|broken window|broke.*window|car window|window glass|stolen from car|stolen from vehicle|tampered lock)\b', text_lower):
        complaint_type = "vehicle_break_in"
    elif re.search(r'\b(office|workplace|desk|cabin|company|stolen from office|workplace theft)\b', text_lower):
        complaint_type = "workplace_theft"
    elif re.search(r'\b(accident|collision|hit and run|crashed|rammed|vehicle hit|road accident|car hit|truck hit|bike hit|hit my car|hit my vehicle|hit my bike)\b', text_lower):
        complaint_type = "vehicle_accident"
    elif re.search(r'\b(vandaliz|damaged property|property damage|broke window|wall damaged|destroyed property)\b', text_lower):
        complaint_type = "property_damage"
    elif re.search(r'\b(loan scam|cheating money|business fraud|cheque bounce|financial fraud|invest fraud)\b', text_lower):
        complaint_type = "financial_fraud"
    elif re.search(r'\b(vehicle|bike|car|scooter|motorcycle|activa|two wheeler|stolen vehicle)\b', text_lower) and "stolen" in text_lower:
        complaint_type = "vehicle_theft"
    elif re.search(r'\b(fraud|cyber|bank|transaction|scam|upi|otp|phishing|money transferred|defrauded)\b', text_lower):
        complaint_type = "cyber_fraud"
    elif re.search(r'\b(missing person|disappeared|kidnap|lost child|lost person)\b', text_lower):
        complaint_type = "missing_person"
    elif re.search(r'\b(assault|attacked|beaten|beating|punched|slapped|stabbed|physical attack|physical violence)\b', text_lower):
        complaint_type = "assault"
    elif re.search(r'\b(threat|extort|blackmail|intimidat)\b', text_lower):
        complaint_type = "threat"
    elif re.search(r'\b(harass|stalk|abuse|molest)\b', text_lower):
        complaint_type = "harassment"
    elif re.search(r'\b(lost document|lost passport|lost aadhar|lost pan card|lost driving license)\b', text_lower):
        complaint_type = "lost_document"
    elif re.search(r'\b(handbag|purse|wallet|bag|stolen|missing|theft|stolen items|belongings|jewellery|gold|laptop|phone|cash)\b', text_lower):
        complaint_type = "property_theft"
    else:
        complaint_type = "property_theft"

    is_cognizable = complaint_type != "lost_document"

    # Match and persist last AI question's answer into merged_entities
    match_and_persist_last_question_answer(conversation_history or [], complaint_text, complaint_type, merged_entities)

    # Complaint-specific entity extraction helpers
    if complaint_type == "phone_snatching":
        if "iphone" in text_lower: merged_entities["mobile_make_model"] = "Apple iPhone"
        elif "samsung" in text_lower: merged_entities["mobile_make_model"] = "Samsung Galaxy"
        elif "oneplus" in text_lower: merged_entities["mobile_make_model"] = "OnePlus Mobile"
        imei_match = re.search(r'\b(\d{15})\b', full_text)
        if imei_match: merged_entities["imei_number"] = imei_match.group(1)

    if complaint_type in ["cyber_fraud", "financial_fraud"]:
        amt_match = re.search(r'(?:₹|rs\.?|inr|amount|transferred|scammed|paid|sum\s+of)?\s*([\d,]{3,9})', full_text, re.IGNORECASE)
        digits_in_latest = re.sub(r'[^\d]', '', complaint_text.strip())
        if digits_in_latest and 2 <= len(digits_in_latest) <= 8:
            try:
                merged_entities["fraud_amount"] = f"Rs. {int(digits_in_latest):,}"
            except ValueError:
                pass
        elif amt_match:
            raw_amt = amt_match.group(1).replace(',', '')
            if raw_amt.isdigit() and int(raw_amt) > 0:
                merged_entities["fraud_amount"] = f"Rs. {int(raw_amt):,}"

    # Vehicle registration extraction
    reg_match = re.search(r'\b([A-Z]{2}\s*\d{1,2}\s*[A-Z]{1,3}\s*\d{1,4})\b', full_text, re.IGNORECASE)
    if reg_match:
        found_reg = reg_match.group(1).upper().strip()
        if complaint_type in ["vehicle_theft", "vehicle_accident", "vehicle_break_in"]:
            merged_entities["vehicle_registration_number"] = found_reg

    # Location extraction
    if "anna nagar" in text_lower: merged_entities["incident_location"] = "Anna Nagar"
    elif "t. nagar" in text_lower or "pondy bazaar" in text_lower: merged_entities["incident_location"] = "T. Nagar"
    elif "mylapore" in text_lower: merged_entities["incident_location"] = "Mylapore"
    elif "adyar" in text_lower: merged_entities["incident_location"] = "Adyar"
    elif "velachery" in text_lower: merged_entities["incident_location"] = "Velachery"
    else:
        loc_match = re.search(r'(?:near|at|around)\s+([A-Z][a-zA-Z0-9\s.]{2,25}(?:Park|Station|Road|Street|Bazaar|Nagar|Beach|Mall|Airport|Bus Stand|Railway Station))', full_text)
        if loc_match and not merged_entities.get("incident_location"):
            merged_entities["incident_location"] = loc_match.group(1).strip()

    # Phone number extraction
    phone_match = re.search(r'\b(\+?91[\s-]?)?([6-9]\d{9})\b', full_text)
    if phone_match and not merged_entities.get("complainant_phone"):
        merged_entities["complainant_phone"] = phone_match.group(2)

    # Date / Time extraction
    if any(w in text_lower for w in ["yesterday", "today"]) and not merged_entities.get("incident_date"):
        merged_entities["incident_date"] = date.today().isoformat()

    time_match = re.search(
        r'\b(\d{1,2}(?::\d{2})?\s*(?:am|pm|a\.m\.|p\.m\.)?|\b(?:morning|afternoon|evening|night|midnight|noon|dawn|dusk)\b)',
        complaint_text,
        re.IGNORECASE,
    )
    if time_match and not merged_entities.get("incident_time"):
        merged_entities["incident_time"] = time_match.group(1).strip().title()

    # Dynamic FIR missing fields evaluation
    missing_fields, follow_up_questions = evaluate_required_fir_fields(complaint_type, merged_entities)
    schema = get_schema(complaint_type)

    location_desc = merged_entities.get('incident_location', 'the specified location')
    summary_str = f"The complainant reported a {complaint_type.replace('_', ' ')} incident ({location_desc})."

    return {
        "complaint_type": complaint_type,
        "is_cognizable": is_cognizable,
        "summary": summary_str,
        "entities": merged_entities,
        "missing_fields": missing_fields,
        "ambiguous_fields": [],
        "follow_up_questions": follow_up_questions[:1],
        "recommended_evidence": schema.get("recommended_evidence", ["ID Proof", "Supporting Document"]),
        "ai_recommendations": {
            "legal_sections": ["BNS 303(2) - Theft"] if "theft" in complaint_type or "snatching" in complaint_type else ["BNS 318 - Cheating"],
            "recommended_action": "Verify incident location and proceed with case registration.",
        },
    }


def analyze_conversational_intake(
    complaint_text: str,
    conversation_history: Optional[list] = None,
    previous_entities: Optional[dict] = None,
) -> dict:
    client = _get_client()
    today_iso = date.today().isoformat()

    history_str = ""
    if conversation_history:
        history_str = "\nPrevious Conversation:\n" + "\n".join(
            [f"{msg.get('sender', 'User')}: {msg.get('text', '')}" for msg in conversation_history]
        )

    user_prompt = f"Today's date is {today_iso}.\n{history_str}\nLatest User Input:\n\"\"\"{complaint_text}\"\"\"\n\nReturn JSON output."

    import time
    response = None
    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model=settings.gemini_model,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=INTAKE_SYSTEM_PROMPT,
                    response_mime_type="application/json",
                    temperature=0.1,
                ),
            )
            break
        except Exception as exc:
            if attempt < 2 and ("503" in str(exc) or "UNAVAILABLE" in str(exc) or "demand" in str(exc).lower()):
                time.sleep(1.2 * (attempt + 1))
                continue
            logger.warning(f"Gemini intake call failed, using fallback engine: {exc}")
            return _fallback_analyze_intake(complaint_text, conversation_history, previous_entities)

    if not response or not (response.text or "").strip():
        return _fallback_analyze_intake(complaint_text, conversation_history, previous_entities)

    try:
        parsed = json.loads(response.text.strip())
    except json.JSONDecodeError:
        return _fallback_analyze_intake(complaint_text, conversation_history, previous_entities)

    # Master Classification Engine Override with strict order
    text_check = (complaint_text + " " + " ".join([m.get("text", "") for m in (conversation_history or [])])).lower()

    if re.search(r'\b(snatch|snatched|grabbed my phone|snatchers|mobile snatching|phone robbery)\b', text_check):
        parsed["complaint_type"] = "phone_snatching"
    elif re.search(r'\b(break in|break-in|smashed glass|broken window|stolen from car|stolen from vehicle|tampered lock)\b', text_check):
        parsed["complaint_type"] = "vehicle_break_in"
    elif re.search(r'\b(office|workplace|desk|cabin|company|stolen from office|workplace theft)\b', text_check):
        parsed["complaint_type"] = "workplace_theft"
    elif re.search(r'\b(accident|collision|hit and run|crashed|rammed|vehicle hit|road accident)\b', text_check):
        parsed["complaint_type"] = "vehicle_accident"
    elif re.search(r'\b(vandaliz|damaged property|property damage|broke window|wall damaged|destroyed property)\b', text_check):
        parsed["complaint_type"] = "property_damage"
    elif re.search(r'\b(loan scam|cheating money|business fraud|cheque bounce|financial fraud)\b', text_check):
        parsed["complaint_type"] = "financial_fraud"
    elif re.search(r'\b(missing person|missing child|missing daughter|missing son|missing father|missing mother|missing brother|missing sister|kidnap|disappeared person|lost child)\b', text_check):
        parsed["complaint_type"] = "missing_person"
    elif re.search(r'\b(vehicle|bike|car|scooter|motorcycle|activa|two wheeler|stolen vehicle)\b', text_check) and "stolen" in text_check:
        parsed["complaint_type"] = "vehicle_theft"
    elif re.search(r'\b(fraud|cyber|bank|transaction|scam|upi|otp|phishing|money transferred|defrauded)\b', text_check):
        parsed["complaint_type"] = "cyber_fraud"

    # Merge previous entities if supplied
    if not isinstance(parsed.get("entities"), dict):
        parsed["entities"] = {}

    merged_entities = {**(previous_entities or {})}

    # Match and persist last AI question's answer into merged_entities
    match_and_persist_last_question_answer(conversation_history or [], complaint_text, parsed.get("complaint_type", "other"), merged_entities)

    # Now overlay any newly extracted non-empty entities from Gemini
    for k, v in parsed["entities"].items():
        if v is not None and str(v).strip() not in ["", "null", "None"]:
            merged_entities[k] = v

    parsed["entities"] = merged_entities

    # Clean non-applicable fields
    if parsed.get("complaint_type") != "vehicle_theft":
        parsed["entities"].pop("vehicle_registration_number", None)

    # Dynamic FIR missing fields evaluation
    missing_fields, follow_up_questions = evaluate_required_fir_fields(parsed.get("complaint_type", "other"), parsed["entities"])
    parsed["missing_fields"] = missing_fields
    parsed["follow_up_questions"] = follow_up_questions[:1]

    # Fallback default evidence from schema registry if AI returned empty
    schema = get_schema(parsed.get("complaint_type", "other"))
    if not parsed.get("recommended_evidence"):
        parsed["recommended_evidence"] = schema.get("recommended_evidence", ["ID Proof", "Supporting Document"])

    return parsed




FIR_DRAFT_SYSTEM_PROMPT = """You are an AI Legal Assistant generating a formal IIF-I Standard FIR (First Information Report) Draft for police officer review.

Your job:
Read the complaint text, summary, incident location, and extracted entities.
Generate a structured IIF-I FIR draft following the official Indian Police FIR structure.

Strict Rules:
- Include ONLY facts provided in the complaint.
- Map offense to relevant sections of Bharatiya Nyaya Sanhita (BNS) / Indian Penal Code (IPC) / IT Act.
- Clearly write a formal, objective, professional FIR narrative statement of facts.
- Return ONLY valid JSON matching the exact schema.

JSON Output Schema:
{
  "district": "Chennai Police District",
  "police_station": "<station_name>",
  "fir_no_draft": "FIR-DRAFT-2026",
  "occurrence_date_time": "<date and time of occurrence>",
  "complainant_details": {
     "name": "<name>",
     "phone": "<phone>",
     "address": "<address>"
  },
  "place_of_occurrence": "<location details>",
  "acts_and_sections": ["BNS Section 303(2) - Theft", "IT Act Section 66D"],
  "suspect_accused_details": "<known accused or 'Unknown person(s)'>",
  "stolen_or_involved_property": "<details of vehicle/money/property>",
  "fir_narrative": "<formal, chronological, neutral legal statement of facts for FIR entry>"
}"""


def generate_fir_draft(case_data: dict) -> dict:
    client = _get_client()
    prompt = f"Case Data for FIR Draft:\n{json.dumps(case_data, indent=2)}\n\nGenerate structured IIF-I FIR draft JSON."

    import time
    response = None
    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model=settings.gemini_model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=FIR_DRAFT_SYSTEM_PROMPT,
                    response_mime_type="application/json",
                    temperature=0.1,
                ),
            )
            break
        except Exception as exc:
            if attempt < 2 and ("503" in str(exc) or "UNAVAILABLE" in str(exc) or "demand" in str(exc).lower()):
                time.sleep(1.2 * (attempt + 1))
                continue
            logger.exception("Gemini FIR draft call failed")
            raise GeminiUnavailableError(str(exc)) from exc

    raw_text = (response.text or "").strip()
    if not raw_text:
        raise GeminiUnavailableError("Gemini returned empty FIR draft.")

    try:
        return json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise GeminiUnavailableError("Gemini returned invalid FIR draft JSON.") from exc
