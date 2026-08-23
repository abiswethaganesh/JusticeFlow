/**
 * Mirrors backend/app/services/form_schema_registry.py.
 * Complete 15 FIR-aware Indian Police / CCTNS Complaint Schemas.
 */
export const FORM_SCHEMAS = {
  vehicle_theft: {
    title: 'Vehicle Theft Complaint',
    icon: '🏍️',
    is_cognizable: true,
    requiredFields: [
      'complainant_name',
      'complainant_phone',
      'vehicle_registration_number',
      'vehicle_type',
      'incident_location',
      'incident_date',
      'incident_time',
      'description',
    ],
    sections: [
      { id: 'complainant', title: '1. Complainant Details', fields: ['complainant_name', 'complainant_phone'] },
      { id: 'vehicle', title: '2. Stolen Vehicle Details', fields: ['vehicle_registration_number', 'vehicle_type'] },
      { id: 'incident', title: '3. Incident Location & Date/Time', fields: ['incident_location', 'incident_date', 'incident_time'] },
      { id: 'statement', title: '4. Statement of Facts', fields: ['description'] },
    ],
  },
  vehicle_accident: {
    title: 'Road Accident / Vehicle Collision Complaint',
    icon: '🚗',
    is_cognizable: true,
    requiredFields: [
      'complainant_name',
      'complainant_phone',
      'vehicle_registration_number',
      'other_vehicle_number',
      'incident_location',
      'incident_date',
      'incident_time',
      'injury_or_damage_details',
      'description',
    ],
    sections: [
      { id: 'complainant', title: '1. Complainant Details', fields: ['complainant_name', 'complainant_phone'] },
      { id: 'collision', title: '2. Vehicles Involved', fields: ['vehicle_registration_number', 'other_vehicle_number'] },
      { id: 'incident', title: '3. Accident Spot & Time', fields: ['incident_location', 'incident_date', 'incident_time'] },
      { id: 'damage', title: '4. Injuries & Vehicle Damage', fields: ['injury_or_damage_details'] },
      { id: 'statement', title: '5. Statement of Facts', fields: ['description'] },
    ],
  },
  cyber_fraud: {
    title: 'Cyber Crime / Online Fraud Complaint',
    icon: '💳',
    is_cognizable: true,
    requiredFields: [
      'complainant_name',
      'complainant_phone',
      'fraud_amount',
      'transaction_reference',
      'platform_used',
      'incident_date',
      'incident_time',
      'description',
    ],
    sections: [
      { id: 'complainant', title: '1. Complainant Details', fields: ['complainant_name', 'complainant_phone'] },
      { id: 'transaction', title: '2. Fraud Transaction Particulars', fields: ['fraud_amount', 'transaction_reference', 'platform_used'] },
      { id: 'incident', title: '3. Date & Time of Occurrence', fields: ['incident_date', 'incident_time'] },
      { id: 'statement', title: '4. Statement of Scam Facts', fields: ['description'] },
    ],
  },
  financial_fraud: {
    title: 'Financial Fraud & Cheating Complaint',
    icon: '💰',
    is_cognizable: true,
    requiredFields: [
      'complainant_name',
      'complainant_phone',
      'accused_name_or_organization',
      'fraud_amount',
      'transaction_mode',
      'incident_location',
      'incident_date',
      'description',
    ],
    sections: [
      { id: 'complainant', title: '1. Complainant Details', fields: ['complainant_name', 'complainant_phone'] },
      { id: 'accused', title: '2. Accused Entity Details', fields: ['accused_name_or_organization'] },
      { id: 'fraud', title: '3. Financial Transaction Info', fields: ['fraud_amount', 'transaction_mode'] },
      { id: 'incident', title: '4. Location & Date', fields: ['incident_location', 'incident_date'] },
      { id: 'statement', title: '5. Statement of Facts', fields: ['description'] },
    ],
  },
  property_damage: {
    title: 'Property Damage & Vandalism Complaint',
    icon: '🏚️',
    is_cognizable: true,
    requiredFields: [
      'complainant_name',
      'complainant_phone',
      'property_location',
      'damaged_property_description',
      'estimated_damage_value',
      'accused_name_or_description',
      'incident_date',
      'incident_time',
      'description',
    ],
    sections: [
      { id: 'complainant', title: '1. Complainant Details', fields: ['complainant_name', 'complainant_phone'] },
      { id: 'property', title: '2. Property & Damage Info', fields: ['property_location', 'damaged_property_description', 'estimated_damage_value'] },
      { id: 'accused', title: '3. Accused Details', fields: ['accused_name_or_description'] },
      { id: 'incident', title: '4. Incident Date & Time', fields: ['incident_date', 'incident_time'] },
      { id: 'statement', title: '5. Statement of Facts', fields: ['description'] },
    ],
  },
  phone_snatching: {
    title: 'Mobile Phone Snatching Complaint',
    icon: '📱',
    is_cognizable: true,
    requiredFields: [
      'complainant_name',
      'complainant_phone',
      'mobile_make_model',
      'imei_number',
      'snatching_location',
      'snatcher_description_or_vehicle',
      'incident_date',
      'incident_time',
      'description',
    ],
    sections: [
      { id: 'complainant', title: '1. Complainant Details', fields: ['complainant_name', 'complainant_phone'] },
      { id: 'mobile', title: '2. Mobile Device Details', fields: ['mobile_make_model', 'imei_number'] },
      { id: 'snatching', title: '3. Snatching Spot & Escape Info', fields: ['snatching_location', 'snatcher_description_or_vehicle'] },
      { id: 'incident', title: '4. Date & Time of Occurrence', fields: ['incident_date', 'incident_time'] },
      { id: 'statement', title: '5. Statement of Facts', fields: ['description'] },
    ],
  },
  workplace_theft: {
    title: 'Workplace / Office Theft Complaint',
    icon: '🏢',
    is_cognizable: true,
    requiredFields: [
      'complainant_name',
      'complainant_phone',
      'company_or_office_name',
      'office_location',
      'stolen_items_description',
      'estimated_value',
      'suspect_employees_or_visitors',
      'incident_date',
      'incident_time',
      'description',
    ],
    sections: [
      { id: 'complainant', title: '1. Complainant Details', fields: ['complainant_name', 'complainant_phone'] },
      { id: 'workplace', title: '2. Office & Workplace Info', fields: ['company_or_office_name', 'office_location'] },
      { id: 'stolen', title: '3. Stolen Assets & Value', fields: ['stolen_items_description', 'estimated_value'] },
      { id: 'suspect', title: '4. Suspect Staff / Visitors', fields: ['suspect_employees_or_visitors'] },
      { id: 'incident', title: '5. Date & Time', fields: ['incident_date', 'incident_time'] },
      { id: 'statement', title: '6. Statement of Facts', fields: ['description'] },
    ],
  },
  vehicle_break_in: {
    title: 'Vehicle Break-In & Theft from Vehicle',
    icon: '🚘',
    is_cognizable: true,
    requiredFields: [
      'complainant_name',
      'complainant_phone',
      'vehicle_registration_number',
      'vehicle_parked_location',
      'stolen_items_from_vehicle',
      'estimated_value',
      'broken_window_or_lock_damage',
      'incident_date',
      'incident_time',
      'description',
    ],
    sections: [
      { id: 'complainant', title: '1. Complainant Details', fields: ['complainant_name', 'complainant_phone'] },
      { id: 'vehicle', title: '2. Vehicle & Parking Spot', fields: ['vehicle_registration_number', 'vehicle_parked_location'] },
      { id: 'breakin', title: '3. Damage & Stolen Items', fields: ['broken_window_or_lock_damage', 'stolen_items_from_vehicle', 'estimated_value'] },
      { id: 'incident', title: '4. Date & Time', fields: ['incident_date', 'incident_time'] },
      { id: 'statement', title: '5. Statement of Facts', fields: ['description'] },
    ],
  },
  missing_person: {
    title: 'Missing Person Complaint',
    icon: '🔎',
    is_cognizable: true,
    requiredFields: [
      'complainant_name',
      'complainant_phone',
      'missing_person_name',
      'age',
      'gender',
      'last_seen_location',
      'last_seen_date',
      'last_seen_time',
      'description',
    ],
    sections: [
      { id: 'complainant', title: '1. Complainant Details', fields: ['complainant_name', 'complainant_phone'] },
      { id: 'missing', title: '2. Missing Person Particulars', fields: ['missing_person_name', 'age', 'gender'] },
      { id: 'last_seen', title: '3. Last Seen Location & Time', fields: ['last_seen_location', 'last_seen_date', 'last_seen_time'] },
      { id: 'statement', title: '4. Physical Description', fields: ['description'] },
    ],
  },
  property_theft: {
    title: 'Property / House Theft Complaint',
    icon: '🏠',
    is_cognizable: true,
    requiredFields: [
      'complainant_name',
      'complainant_phone',
      'property_location',
      'stolen_items_description',
      'estimated_value',
      'incident_date',
      'incident_time',
      'description',
    ],
    sections: [
      { id: 'complainant', title: '1. Complainant Details', fields: ['complainant_name', 'complainant_phone'] },
      { id: 'property', title: '2. Property Location', fields: ['property_location'] },
      { id: 'stolen', title: '3. Stolen Items & Valuation', fields: ['stolen_items_description', 'estimated_value'] },
      { id: 'incident', title: '4. Date & Time of Theft', fields: ['incident_date', 'incident_time'] },
      { id: 'statement', title: '5. Statement of Facts', fields: ['description'] },
    ],
  },
  assault: {
    title: 'Physical Assault Complaint',
    icon: '⚠️',
    is_cognizable: true,
    requiredFields: [
      'complainant_name',
      'complainant_phone',
      'victim_name',
      'accused_name_or_description',
      'incident_location',
      'incident_date',
      'incident_time',
      'injury_details',
      'description',
    ],
    sections: [
      { id: 'complainant', title: '1. Complainant Details', fields: ['complainant_name', 'complainant_phone'] },
      { id: 'victim', title: '2. Victim & Accused Details', fields: ['victim_name', 'accused_name_or_description'] },
      { id: 'incident', title: '3. Crime Scene & Time', fields: ['incident_location', 'incident_date', 'incident_time'] },
      { id: 'injury', title: '4. Injuries & Medical Details', fields: ['injury_details'] },
      { id: 'statement', title: '5. Statement of Facts', fields: ['description'] },
    ],
  },
  threat: {
    title: 'Criminal Intimidation / Threat Complaint',
    icon: '🚨',
    is_cognizable: true,
    requiredFields: [
      'complainant_name',
      'complainant_phone',
      'accused_name_or_description',
      'incident_location',
      'incident_date',
      'threat_medium',
      'description',
    ],
    sections: [
      { id: 'complainant', title: '1. Complainant Details', fields: ['complainant_name', 'complainant_phone'] },
      { id: 'accused', title: '2. Accused Details', fields: ['accused_name_or_description'] },
      { id: 'threat', title: '3. Threat Medium & Location', fields: ['threat_medium', 'incident_location', 'incident_date'] },
      { id: 'statement', title: '4. Statement of Facts', fields: ['description'] },
    ],
  },
  harassment: {
    title: 'Harassment Complaint',
    icon: '🛡️',
    is_cognizable: true,
    requiredFields: [
      'complainant_name',
      'complainant_phone',
      'accused_details',
      'incident_location',
      'incident_date',
      'description',
    ],
    sections: [
      { id: 'complainant', title: '1. Complainant Details', fields: ['complainant_name', 'complainant_phone'] },
      { id: 'accused', title: '2. Accused Details', fields: ['accused_details'] },
      { id: 'incident', title: '3. Location & Date', fields: ['incident_location', 'incident_date'] },
      { id: 'statement', title: '4. Statement of Facts', fields: ['description'] },
    ],
  },
  lost_document: {
    title: 'Lost Document Report',
    icon: '📄',
    is_cognizable: false,
    requiredFields: [
      'complainant_name',
      'complainant_phone',
      'document_name',
      'document_number',
      'lost_location',
      'lost_date',
      'description',
    ],
    sections: [
      { id: 'complainant', title: '1. Complainant Details', fields: ['complainant_name', 'complainant_phone'] },
      { id: 'document', title: '2. Lost Document Particulars', fields: ['document_name', 'document_number'] },
      { id: 'incident', title: '3. Lost Location & Date', fields: ['lost_location', 'lost_date'] },
      { id: 'statement', title: '4. Additional Details', fields: ['description'] },
    ],
  },
  other: {
    title: 'General Complaint',
    icon: '📝',
    is_cognizable: false,
    requiredFields: ['complainant_name', 'complainant_phone', 'incident_location', 'incident_date', 'description'],
    sections: [
      { id: 'complainant', title: '1. Complainant Details', fields: ['complainant_name', 'complainant_phone'] },
      { id: 'incident', title: '2. Incident Location & Date', fields: ['incident_location', 'incident_date'] },
      { id: 'statement', title: '3. Statement of Facts', fields: ['description'] },
    ],
  },
}

export const FIELD_LABELS = {
  complainant_name: 'Complainant Full Name',
  complainant_phone: 'Contact Phone Number',
  vehicle_registration_number: 'Vehicle Registration Number',
  vehicle_type: 'Vehicle Type / Model',
  other_vehicle_number: 'Other Vehicle Number / Make',
  injury_or_damage_details: 'Injury & Damage Details',
  incident_location: 'Incident Location',
  incident_date: 'Incident Date',
  incident_time: 'Incident Time',
  description: 'Statement of Facts / Narrative',
  fraud_amount: 'Fraud Amount Involved',
  transaction_reference: 'Transaction Reference / UPI ID',
  platform_used: 'Platform / Payment App Used',
  transaction_mode: 'Payment Mode',
  accused_name_or_organization: 'Accused Person / Entity Name',
  damaged_property_description: 'Damaged Property Details',
  estimated_damage_value: 'Estimated Repair Cost / Damage Value',
  mobile_make_model: 'Mobile Make & Model',
  imei_number: '15-Digit IMEI Number',
  snatching_location: 'Snatching Location',
  snatcher_description_or_vehicle: 'Snatcher / Escape Vehicle Info',
  company_or_office_name: 'Company / Workplace Name',
  office_location: 'Office / Workplace Address',
  suspect_employees_or_visitors: 'Suspect Staff / Visitors',
  vehicle_parked_location: 'Vehicle Parking Location',
  stolen_items_from_vehicle: 'Items Stolen from Vehicle',
  broken_window_or_lock_damage: 'Window / Lock Damage Details',
  stolen_items_description: 'Stolen Items Details',
  property_location: 'Property / House Address',
  estimated_value: 'Estimated Monetary Value',
  missing_person_name: "Missing Person's Full Name",
  age: 'Age',
  gender: 'Gender',
  last_seen_location: 'Last Seen Location',
  last_seen_date: 'Last Seen Date',
  last_seen_time: 'Last Seen Time',
  victim_name: "Victim's Full Name",
  accused_name_or_description: 'Accused / Suspect Details',
  injury_details: 'Injury & Hospitalization Particulars',
  threat_medium: 'Medium of Threat (Call/Message/In-person)',
  accused_details: 'Accused / Harasser Details',
  document_name: 'Lost Document Name (Passport/Aadhaar)',
  document_number: 'Document / ID Reference Number',
  lost_location: 'Location Where Document Was Misplaced',
  lost_date: 'Date Document Realized Lost',
}

export const FIELD_QUESTIONS = {
  complainant_name: 'What is your full name?',
  complainant_phone: 'What is your contact phone number?',
  vehicle_registration_number: 'What is your vehicle registration number?',
  vehicle_type: 'What type of vehicle is it?',
  other_vehicle_number: 'What was the other vehicle registration number or description?',
  injury_or_damage_details: 'What injuries were suffered or what vehicle damage occurred?',
  incident_location: 'Where exactly did the incident occur?',
  incident_date: 'On what date did this happen?',
  incident_time: 'At approximately what time did this happen?',
  description: 'Is there any other statement of facts you can add?',
  fraud_amount: 'What was the total fraud amount involved?',
  transaction_reference: 'Do you have a transaction reference or UPI ID?',
  platform_used: 'Which platform or payment app was used?',
  transaction_mode: 'What was the transaction mode (UPI, NetBanking, Cheque)?',
  accused_name_or_organization: 'What is the name of the accused person or organization?',
  damaged_property_description: 'What specific property was damaged or vandalized?',
  estimated_damage_value: 'What is the estimated cost of damage?',
  mobile_make_model: 'What is your mobile phone make and model?',
  imei_number: 'What is your phone 15-digit IMEI number?',
  snatching_location: 'Where was your mobile phone snatched?',
  snatcher_description_or_vehicle: 'Can you describe the snatcher or their vehicle?',
  company_or_office_name: 'What is the name of your workplace or company?',
  office_location: 'Where is your office located?',
  suspect_employees_or_visitors: 'Do you suspect any staff member or visitor?',
  vehicle_parked_location: 'Where was your vehicle parked?',
  stolen_items_from_vehicle: 'What items were stolen from inside the vehicle?',
  broken_window_or_lock_damage: 'Which window or lock was damaged?',
  stolen_items_description: 'What items were stolen?',
  property_location: 'Where is the house or property located?',
  estimated_value: 'What is the total estimated value of stolen items?',
  missing_person_name: 'What is the missing person\u2019s full name?',
  age: 'What is their age?',
  gender: 'What is their gender?',
  last_seen_location: 'Where were they last seen?',
  last_seen_date: 'On what date were they last seen?',
  last_seen_time: 'At approximately what time were they last seen?',
  victim_name: 'What is the victim\u2019s name?',
  accused_name_or_description: 'Who is the accused / attacker?',
  injury_details: 'What physical injuries were suffered?',
  threat_medium: 'How was the threat conveyed?',
  accused_details: 'Who is harassing you?',
  document_name: 'Which document was lost?',
  document_number: 'What is the document reference number?',
  lost_location: 'Where was the document lost?',
  lost_date: 'On what date was it lost?',
}

/** Deterministic comparison using current schema required fields and alias resolution. */
export function getMissingFields(complaintType, entities) {
  const schema = FORM_SCHEMAS[complaintType] || FORM_SCHEMAS.other
  const e = entities || {}

  const hasValue = (field) => {
    let val = e[field]

    // Location alias
    if (!val && ['incident_location', 'snatching_location', 'office_location', 'vehicle_parked_location', 'property_location', 'last_seen_location', 'lost_location'].includes(field)) {
      val = e.incident_location || e.snatching_location || e.office_location || e.vehicle_parked_location || e.property_location || e.last_seen_location || e.lost_location
    }

    // Accused alias
    if (!val && ['accused_name_or_description', 'accused_details', 'accused_name_or_organization', 'snatcher_description_or_vehicle', 'suspect_employees_or_visitors'].includes(field)) {
      val = e.accused_name_or_description || e.accused_details || e.accused_name_or_organization || e.snatcher_description_or_vehicle || e.suspect_employees_or_visitors
    }

    // Injury / damage alias
    if (!val && ['injury_details', 'injury_or_damage_details'].includes(field)) {
      val = e.injury_details || e.injury_or_damage_details
    }

    // Stolen items alias
    if (!val && ['stolen_items_description', 'stolen_items', 'stolen_items_from_vehicle', 'damaged_property_description'].includes(field)) {
      val = e.stolen_items_description || e.stolen_items || e.stolen_items_from_vehicle || e.damaged_property_description
    }

    // Amount alias
    if (!val && ['fraud_amount', 'transaction_amount'].includes(field)) {
      val = e.fraud_amount || e.transaction_amount
    }

    return val !== null && val !== undefined && String(val).trim() !== '' && String(val).trim() !== 'null' && String(val).trim() !== 'None' && String(val).trim() !== '—'
  }

  // Check non-description fields first
  const missingNonDesc = schema.requiredFields.filter((field) => field !== 'description' && !hasValue(field))
  if (!hasValue('complainant_phone') && !missingNonDesc.includes('complainant_phone')) {
    missingNonDesc.push('complainant_phone')
  }

  // If all non-description fields are complete, description is automatically filled on backend
  return schema.requiredFields.filter((field) => {
    if (field === 'description' && missingNonDesc.length === 0 && e.description) {
      return false
    }
    return !hasValue(field)
  })
}


