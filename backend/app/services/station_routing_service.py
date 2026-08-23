"""
Automatic police station routing service.
Determines the relevant police station/branch based on incident location and complaint details.
"""

STATION_MAPPINGS = [
    (
        ["anna nagar", "shenoy nagar", "koyambedu", "arumbakkam", "kilpauk", "aminjikarai"],
        "Anna Nagar Police Station",
    ),
    (
        ["t. nagar", "t nagar", "thyagaraya nagar", "kodambakkam", "nungambakkam", "mambalam", "pondy bazaar"],
        "T. Nagar Police Station",
    ),
    (
        ["adyar", "besant nagar", "thiruvanmiyur", "kotturpuram", "guindy", "ra puram"],
        "Adyar Police Station",
    ),
    (
        ["velachery", "madipakkam", "perungudi", "taramani", "medavakkam"],
        "Velachery Police Station",
    ),
    (
        ["tambaram", "chromepet", "pallavaram", "selaiyur"],
        "Tambaram Police Station",
    ),
    (
        ["mylapore", "mandavelli", "alwarpet", "royapettah", "triplicane"],
        "Mylapore Police Station",
    ),
]


def determine_assigned_station(
    incident_location: str = "",
    structured_data: dict = None,
    complaint_text: str = "",
) -> str:
    """
    Analyzes incident location or text to route the complaint to the correct police station branch.
    """
    if structured_data is None:
        structured_data = {}

    # Gather potential location strings
    loc_candidates = [
        incident_location,
        structured_data.get("incident_location", ""),
        structured_data.get("last_seen_location", ""),
        structured_data.get("location", ""),
    ]
    
    combined_text = " ".join([c for c in loc_candidates if c]).strip().lower()

    if not combined_text:
        combined_text = complaint_text.lower()

    for keywords, station_name in STATION_MAPPINGS:
        for kw in keywords:
            if kw in combined_text:
                return station_name

    # If location text is non-empty but not in preset list, form standard station name or default
    first_loc = next((c.strip() for c in loc_candidates if c and c.strip()), "")
    if first_loc:
        # e.g., "Porur 3rd Street" -> "Porur Police Station"
        area = first_loc.split(",")[0].split(" ")[0].strip().title()
        if area and len(area) > 2:
            return f"{area} Police Station"

    # Default fallback station for MVP demo
    return "Anna Nagar Police Station"
