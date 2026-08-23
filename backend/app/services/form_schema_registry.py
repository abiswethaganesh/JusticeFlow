"""
Configurable Form Schema Registry for Dynamic Complaint Types & Evidence Requirements.
Follows Indian Police / CCTNS-style workflow with complaint-specific required fields, sections, and evidence.
"""

FORM_SCHEMAS = {
    "vehicle_theft": {
        "form_id": "vehicle_theft",
        "title": "Vehicle Theft Complaint",
        "icon": "🏍️",
        "is_cognizable": True,
        "required_fields": [
            "complainant_name",
            "complainant_phone",
            "vehicle_registration_number",
            "vehicle_type",
            "incident_location",
            "incident_date",
            "incident_time",
            "description",
        ],
        "form_sections": [
            {
                "section_id": "complainant_info",
                "title": "1. Complainant Information",
                "fields": ["complainant_name", "complainant_phone"],
            },
            {
                "section_id": "vehicle_info",
                "title": "2. Stolen Vehicle Particulars",
                "fields": ["vehicle_registration_number", "vehicle_type"],
            },
            {
                "section_id": "incident_info",
                "title": "3. Incident Location & Date/Time",
                "fields": ["incident_location", "incident_date", "incident_time"],
            },
            {
                "section_id": "statement_info",
                "title": "4. Statement of Facts",
                "fields": ["description"],
            },
        ],
        "recommended_evidence": [
            "Vehicle Registration Certificate (RC Copy)",
            "Photo of Stolen Vehicle",
            "Purchase Invoice / Insurance Document",
            "Keys Purchase Invoice / Photo",
        ],
    },
    "vehicle_accident": {
        "form_id": "vehicle_accident",
        "title": "Road Accident / Vehicle Collision Complaint",
        "icon": "🚗",
        "is_cognizable": True,
        "required_fields": [
            "complainant_name",
            "complainant_phone",
            "vehicle_registration_number",
            "other_vehicle_number",
            "incident_location",
            "incident_date",
            "incident_time",
            "injury_or_damage_details",
            "description",
        ],
        "form_sections": [
            {
                "section_id": "complainant_info",
                "title": "1. Complainant Information",
                "fields": ["complainant_name", "complainant_phone"],
            },
            {
                "section_id": "collision_info",
                "title": "2. Vehicles Involved in Collision",
                "fields": ["vehicle_registration_number", "other_vehicle_number"],
            },
            {
                "section_id": "incident_info",
                "title": "3. Accident Spot & Date/Time",
                "fields": ["incident_location", "incident_date", "incident_time"],
            },
            {
                "section_id": "damage_info",
                "title": "4. Injury & Vehicle Damage Particulars",
                "fields": ["injury_or_damage_details"],
            },
            {
                "section_id": "statement_info",
                "title": "5. Statement of Facts",
                "fields": ["description"],
            },
        ],
        "recommended_evidence": [
            "Photos of Vehicle Damage & Accident Spot",
            "Driving License & RC Copy",
            "Hospital MLC / Medical Prescription (if injured)",
            "Eyewitness Names & Contact Notes",
        ],
    },
    "cyber_fraud": {
        "form_id": "cyber_fraud",
        "title": "Cyber Crime / Online Fraud Complaint",
        "icon": "💳",
        "is_cognizable": True,
        "required_fields": [
            "complainant_name",
            "complainant_phone",
            "fraud_amount",
            "transaction_reference",
            "platform_used",
            "incident_date",
            "incident_time",
            "description",
        ],
        "form_sections": [
            {
                "section_id": "complainant_info",
                "title": "1. Complainant Information",
                "fields": ["complainant_name", "complainant_phone"],
            },
            {
                "section_id": "transaction_info",
                "title": "2. Fraud Transaction Particulars",
                "fields": ["fraud_amount", "transaction_reference", "platform_used"],
            },
            {
                "section_id": "incident_info",
                "title": "3. Date & Time of Cyber Crime",
                "fields": ["incident_date", "incident_time"],
            },
            {
                "section_id": "statement_info",
                "title": "4. Statement of Scam Facts",
                "fields": ["description"],
            },
        ],
        "recommended_evidence": [
            "Bank Statement / Payment Receipt",
            "Transaction Screenshot (UPI / NetBanking)",
            "Fraudulent Chat / SMS / Email Screenshots",
            "Scammer Phone Number / UPI ID Proof",
        ],
    },
    "financial_fraud": {
        "form_id": "financial_fraud",
        "title": "Financial Fraud & Cheating Complaint",
        "icon": "💰",
        "is_cognizable": True,
        "required_fields": [
            "complainant_name",
            "complainant_phone",
            "accused_name_or_organization",
            "fraud_amount",
            "transaction_mode",
            "incident_location",
            "incident_date",
            "description",
        ],
        "form_sections": [
            {
                "section_id": "complainant_info",
                "title": "1. Complainant Information",
                "fields": ["complainant_name", "complainant_phone"],
            },
            {
                "section_id": "accused_info",
                "title": "2. Accused Person / Entity Details",
                "fields": ["accused_name_or_organization"],
            },
            {
                "section_id": "fraud_details",
                "title": "3. Fraud Financial Details",
                "fields": ["fraud_amount", "transaction_mode"],
            },
            {
                "section_id": "incident_info",
                "title": "4. Location & Date of Occurrence",
                "fields": ["incident_location", "incident_date"],
            },
            {
                "section_id": "statement_info",
                "title": "5. Statement of Facts",
                "fields": ["description"],
            },
        ],
        "recommended_evidence": [
            "Bank Statement / Cancelled Cheque / Agreement",
            "Payment Receipts / Loan Documents",
            "WhatsApp / Email Communication Logs",
        ],
    },
    "property_damage": {
        "form_id": "property_damage",
        "title": "Property Damage & Vandalism Complaint",
        "icon": "🏚️",
        "is_cognizable": True,
        "required_fields": [
            "complainant_name",
            "complainant_phone",
            "property_location",
            "damaged_property_description",
            "estimated_damage_value",
            "accused_name_or_description",
            "incident_date",
            "incident_time",
            "description",
        ],
        "form_sections": [
            {
                "section_id": "complainant_info",
                "title": "1. Complainant Information",
                "fields": ["complainant_name", "complainant_phone"],
            },
            {
                "section_id": "property_info",
                "title": "2. Property & Damage Particulars",
                "fields": ["property_location", "damaged_property_description", "estimated_damage_value"],
            },
            {
                "section_id": "accused_info",
                "title": "3. Accused / Suspect Details",
                "fields": ["accused_name_or_description"],
            },
            {
                "section_id": "incident_info",
                "title": "4. Incident Date & Time",
                "fields": ["incident_date", "incident_time"],
            },
            {
                "section_id": "statement_info",
                "title": "5. Statement of Facts",
                "fields": ["description"],
            },
        ],
        "recommended_evidence": [
            "Photos / Video of Damaged Property",
            "CCTV Footage of Vandalism",
            "Repair Estimate / Contractor Bill",
            "Property Ownership / Lease Documents",
        ],
    },
    "phone_snatching": {
        "form_id": "phone_snatching",
        "title": "Mobile Phone Snatching / Robbery Complaint",
        "icon": "📱",
        "is_cognizable": True,
        "required_fields": [
            "complainant_name",
            "complainant_phone",
            "mobile_make_model",
            "imei_number",
            "snatching_location",
            "snatcher_description_or_vehicle",
            "incident_date",
            "incident_time",
            "description",
        ],
        "form_sections": [
            {
                "section_id": "complainant_info",
                "title": "1. Complainant Information",
                "fields": ["complainant_name", "complainant_phone"],
            },
            {
                "section_id": "mobile_info",
                "title": "2. Mobile Device Particulars",
                "fields": ["mobile_make_model", "imei_number"],
            },
            {
                "section_id": "snatching_info",
                "title": "3. Snatching Spot & Escape Particulars",
                "fields": ["snatching_location", "snatcher_description_or_vehicle"],
            },
            {
                "section_id": "incident_info",
                "title": "4. Incident Date & Time",
                "fields": ["incident_date", "incident_time"],
            },
            {
                "section_id": "statement_info",
                "title": "5. Statement of Facts",
                "fields": ["description"],
            },
        ],
        "recommended_evidence": [
            "Mobile Purchase Invoice / Box showing IMEI",
            "SIM Card Blocking Acknowledgment",
            "CCTV Footage near Snatching Location",
        ],
    },
    "workplace_theft": {
        "form_id": "workplace_theft",
        "title": "Workplace / Office Theft Complaint",
        "icon": "🏢",
        "is_cognizable": True,
        "required_fields": [
            "complainant_name",
            "complainant_phone",
            "company_or_office_name",
            "office_location",
            "stolen_items_description",
            "estimated_value",
            "suspect_employees_or_visitors",
            "incident_date",
            "incident_time",
            "description",
        ],
        "form_sections": [
            {
                "section_id": "complainant_info",
                "title": "1. Complainant Information",
                "fields": ["complainant_name", "complainant_phone"],
            },
            {
                "section_id": "workplace_info",
                "title": "2. Workplace / Organization Info",
                "fields": ["company_or_office_name", "office_location"],
            },
            {
                "section_id": "stolen_info",
                "title": "3. Stolen Asset Particulars & Valuation",
                "fields": ["stolen_items_description", "estimated_value"],
            },
            {
                "section_id": "suspect_info",
                "title": "4. Suspect Staff / Visitor Details",
                "fields": ["suspect_employees_or_visitors"],
            },
            {
                "section_id": "incident_info",
                "title": "5. Date & Time of Theft",
                "fields": ["incident_date", "incident_time"],
            },
            {
                "section_id": "statement_info",
                "title": "6. Statement of Facts",
                "fields": ["description"],
            },
        ],
        "recommended_evidence": [
            "Office CCTV Camera Recordings",
            "Asset Register / Purchase Invoices",
            "Visitor / Staff Entry Logbook",
            "Company Employee ID Copy",
        ],
    },
    "vehicle_break_in": {
        "form_id": "vehicle_break_in",
        "title": "Vehicle Break-In & Theft from Vehicle",
        "icon": "🚘",
        "is_cognizable": True,
        "required_fields": [
            "complainant_name",
            "complainant_phone",
            "vehicle_registration_number",
            "vehicle_parked_location",
            "stolen_items_from_vehicle",
            "estimated_value",
            "broken_window_or_lock_damage",
            "incident_date",
            "incident_time",
            "description",
        ],
        "form_sections": [
            {
                "section_id": "complainant_info",
                "title": "1. Complainant Information",
                "fields": ["complainant_name", "complainant_phone"],
            },
            {
                "section_id": "vehicle_info",
                "title": "2. Vehicle Details & Parking Location",
                "fields": ["vehicle_registration_number", "vehicle_parked_location"],
            },
            {
                "section_id": "breakin_info",
                "title": "3. Vehicle Damage & Stolen Items",
                "fields": ["broken_window_or_lock_damage", "stolen_items_from_vehicle", "estimated_value"],
            },
            {
                "section_id": "incident_info",
                "title": "4. Date & Time of Occurrence",
                "fields": ["incident_date", "incident_time"],
            },
            {
                "section_id": "statement_info",
                "title": "5. Statement of Facts",
                "fields": ["description"],
            },
        ],
        "recommended_evidence": [
            "Photos of Broken Glass / Tampered Vehicle Locks",
            "Invoices / Receipts for Stolen Items",
            "Parking Spot CCTV Video Clip",
        ],
    },
    "missing_person": {
        "form_id": "missing_person",
        "title": "Missing Person Report",
        "icon": "🔎",
        "is_cognizable": True,
        "required_fields": [
            "complainant_name",
            "complainant_phone",
            "missing_person_name",
            "age",
            "gender",
            "last_seen_location",
            "last_seen_date",
            "last_seen_time",
            "description",
        ],
        "form_sections": [
            {
                "section_id": "complainant_info",
                "title": "1. Complainant Information",
                "fields": ["complainant_name", "complainant_phone"],
            },
            {
                "section_id": "missing_person_info",
                "title": "2. Missing Person Particulars",
                "fields": ["missing_person_name", "age", "gender"],
            },
            {
                "section_id": "last_seen_info",
                "title": "3. Last Seen Location & Date/Time",
                "fields": ["last_seen_location", "last_seen_date", "last_seen_time"],
            },
            {
                "section_id": "statement_info",
                "title": "4. Clothing & Physical Description",
                "fields": ["description"],
            },
        ],
        "recommended_evidence": [
            "Recent Clear Photograph of Missing Person",
            "Aadhaar / ID Card Copy of Missing Person",
            "Last Known CCTV Footage / Location Note",
        ],
    },
    "property_theft": {
        "form_id": "property_theft",
        "title": "Property / House Theft Complaint",
        "icon": "🏠",
        "is_cognizable": True,
        "required_fields": [
            "complainant_name",
            "complainant_phone",
            "property_location",
            "stolen_items_description",
            "estimated_value",
            "incident_date",
            "incident_time",
            "description",
        ],
        "form_sections": [
            {
                "section_id": "complainant_info",
                "title": "1. Complainant Information",
                "fields": ["complainant_name", "complainant_phone"],
            },
            {
                "section_id": "property_info",
                "title": "2. House / Property Location",
                "fields": ["property_location"],
            },
            {
                "section_id": "stolen_info",
                "title": "3. Particulars of Stolen Property & Valuation",
                "fields": ["stolen_items_description", "estimated_value"],
            },
            {
                "section_id": "incident_info",
                "title": "4. Date & Time of Occurrence",
                "fields": ["incident_date", "incident_time"],
            },
            {
                "section_id": "statement_info",
                "title": "5. Statement of Facts",
                "fields": ["description"],
            },
        ],
        "recommended_evidence": [
            "List of Stolen Items with Bills/Serial Numbers",
            "Photos of Lock Break / Damaged Property",
            "CCTV Footage Copy",
        ],
    },
    "assault": {
        "form_id": "assault",
        "title": "Physical Assault Complaint",
        "icon": "⚠️",
        "is_cognizable": True,
        "required_fields": [
            "complainant_name",
            "complainant_phone",
            "victim_name",
            "accused_name_or_description",
            "incident_location",
            "incident_date",
            "incident_time",
            "injury_details",
            "description",
        ],
        "form_sections": [
            {
                "section_id": "complainant_info",
                "title": "1. Complainant Information",
                "fields": ["complainant_name", "complainant_phone"],
            },
            {
                "section_id": "victim_info",
                "title": "2. Victim & Accused Details",
                "fields": ["victim_name", "accused_name_or_description"],
            },
            {
                "section_id": "incident_info",
                "title": "3. Crime Scene & Date/Time",
                "fields": ["incident_location", "incident_date", "incident_time"],
            },
            {
                "section_id": "injury_info",
                "title": "4. Physical Injury & Medical Particulars",
                "fields": ["injury_details"],
            },
            {
                "section_id": "statement_info",
                "title": "5. Statement of Facts",
                "fields": ["description"],
            },
        ],
        "recommended_evidence": [
            "Medical Report / Hospital Prescription (MLC)",
            "Photos of Injuries",
            "Witness Contact / Statement Notes",
        ],
    },
    "threat": {
        "form_id": "threat",
        "title": "Criminal Intimidation / Threat Complaint",
        "icon": "🚨",
        "is_cognizable": True,
        "required_fields": [
            "complainant_name",
            "complainant_phone",
            "accused_name_or_description",
            "incident_location",
            "incident_date",
            "threat_medium",
            "description",
        ],
        "form_sections": [
            {
                "section_id": "complainant_info",
                "title": "1. Complainant Information",
                "fields": ["complainant_name", "complainant_phone"],
            },
            {
                "section_id": "accused_info",
                "title": "2. Accused Person Details",
                "fields": ["accused_name_or_description"],
            },
            {
                "section_id": "threat_info",
                "title": "3. Medium of Threat & Location/Date",
                "fields": ["threat_medium", "incident_location", "incident_date"],
            },
            {
                "section_id": "statement_info",
                "title": "4. Statement of Threat Facts",
                "fields": ["description"],
            },
        ],
        "recommended_evidence": [
            "Call Recording / WhatsApp Message Screenshots",
            "Threatening Letter / CCTV Record",
        ],
    },
    "harassment": {
        "form_id": "harassment",
        "title": "Harassment Complaint",
        "icon": "🛡️",
        "is_cognizable": True,
        "required_fields": [
            "complainant_name",
            "complainant_phone",
            "accused_details",
            "incident_location",
            "incident_date",
            "description",
        ],
        "form_sections": [
            {
                "section_id": "complainant_info",
                "title": "1. Complainant Information",
                "fields": ["complainant_name", "complainant_phone"],
            },
            {
                "section_id": "accused_info",
                "title": "2. Accused / Harasser Details",
                "fields": ["accused_details"],
            },
            {
                "section_id": "incident_info",
                "title": "3. Incident Location & Date",
                "fields": ["incident_location", "incident_date"],
            },
            {
                "section_id": "statement_info",
                "title": "4. Statement of Facts",
                "fields": ["description"],
            },
        ],
        "recommended_evidence": [
            "Message Logs / Audio Recording",
            "Eyewitness Names",
        ],
    },
    "lost_document": {
        "form_id": "lost_document",
        "title": "Lost Document / Property Report",
        "icon": "📄",
        "is_cognizable": False,
        "required_fields": [
            "complainant_name",
            "complainant_phone",
            "document_name",
            "document_number",
            "lost_location",
            "lost_date",
            "description",
        ],
        "form_sections": [
            {
                "section_id": "complainant_info",
                "title": "1. Complainant Information",
                "fields": ["complainant_name", "complainant_phone"],
            },
            {
                "section_id": "document_info",
                "title": "2. Document Details",
                "fields": ["document_name", "document_number"],
            },
            {
                "section_id": "incident_info",
                "title": "3. Lost Location & Date",
                "fields": ["lost_location", "lost_date"],
            },
            {
                "section_id": "statement_info",
                "title": "4. Additional Details",
                "fields": ["description"],
            },
        ],
        "recommended_evidence": [
            "Copy of Lost Document (if available)",
            "Aadhaar Card Copy",
        ],
    },
    "other": {
        "form_id": "other",
        "title": "General Complaint",
        "icon": "📝",
        "is_cognizable": False,
        "required_fields": [
            "complainant_name",
            "complainant_phone",
            "incident_location",
            "incident_date",
            "description",
        ],
        "form_sections": [
            {
                "section_id": "complainant_info",
                "title": "1. Complainant Information",
                "fields": ["complainant_name", "complainant_phone"],
            },
            {
                "section_id": "incident_info",
                "title": "2. Incident Location & Date",
                "fields": ["incident_location", "incident_date"],
            },
            {
                "section_id": "statement_info",
                "title": "3. Statement of Facts",
                "fields": ["description"],
            },
        ],
        "recommended_evidence": [
            "Any relevant photo, document, or audio proof",
        ],
    },
}


def get_schema(complaint_type: str) -> dict:
    """Returns the form schema dict for a complaint type, falling back to 'other'."""
    return FORM_SCHEMAS.get(complaint_type, FORM_SCHEMAS["other"])

