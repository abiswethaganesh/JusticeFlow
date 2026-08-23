"""
Deterministic Police Station Jurisdiction Routing Engine.
Maps incident locations strictly using area/keyword matching against database records.
"""
from typing import Tuple
from sqlalchemy.orm import Session
from app.models.police_station import PoliceStation

DEFAULT_STATION_CODE = "AN-PS-01"
DEFAULT_STATION_NAME = "Anna Nagar Police Station"

# Default seed data if database is empty
INITIAL_POLICE_STATIONS = [
    {
        "station_code": "AN-PS-01",
        "station_name": "Anna Nagar Police Station",
        "jurisdiction_area": {"keywords": ["anna nagar", "shenoy nagar", "koyambedu", "arumbakkam", "kilpauk", "aminjikarai"]},
        "city": "Chennai",
        "address": "2nd Avenue, Anna Nagar, Chennai",
        "contact_number": "044-26210100",
    },
    {
        "station_code": "TN-PS-02",
        "station_name": "T. Nagar Police Station",
        "jurisdiction_area": {"keywords": ["t. nagar", "t nagar", "thyagaraya nagar", "kodambakkam", "nungambakkam", "mambalam", "pondy bazaar"]},
        "city": "Chennai",
        "address": "Usman Road, T. Nagar, Chennai",
        "contact_number": "044-24340200",
    },
    {
        "station_code": "AD-PS-03",
        "station_name": "Adyar Police Station",
        "jurisdiction_area": {"keywords": ["adyar", "besant nagar", "thiruvanmiyur", "kotturpuram", "guindy", "ra puram"]},
        "city": "Chennai",
        "address": "Lattice Bridge Road, Adyar, Chennai",
        "contact_number": "044-24410300",
    },
    {
        "station_code": "VL-PS-04",
        "station_name": "Velachery Police Station",
        "jurisdiction_area": {"keywords": ["velachery", "madipakkam", "perungudi", "taramani", "medavakkam"]},
        "city": "Chennai",
        "address": "100 Feet Road, Velachery, Chennai",
        "contact_number": "044-22430400",
    },
    {
        "station_code": "TB-PS-05",
        "station_name": "Tambaram Police Station",
        "jurisdiction_area": {"keywords": ["tambaram", "chromepet", "pallavaram", "selaiyur"]},
        "city": "Chennai",
        "address": "GST Road, Tambaram, Chennai",
        "contact_number": "044-22260500",
    },
    {
        "station_code": "MY-PS-06",
        "station_name": "Mylapore Police Station",
        "jurisdiction_area": {"keywords": ["mylapore", "mandavelli", "alwarpet", "royapettah", "triplicane"]},
        "city": "Chennai",
        "address": "Kutchery Road, Mylapore, Chennai",
        "contact_number": "044-24980600",
    },
]


def seed_police_stations_if_needed(db: Session):
    """Ensures standard police stations exist in database."""
    count = db.query(PoliceStation).count()
    if count == 0:
        for data in INITIAL_POLICE_STATIONS:
            station = PoliceStation(
                station_code=data["station_code"],
                station_name=data["station_name"],
                jurisdiction_area=data["jurisdiction_area"],
                city=data["city"],
                address=data["address"],
                contact_number=data["contact_number"],
            )
            db.add(station)
        db.commit()


def resolve_police_station(
    db: Session,
    incident_location: str = "",
    structured_data: dict = None,
    complaint_text: str = "",
) -> Tuple[int, str]:
    """
    Deterministic jurisdiction matching against PostgreSQL database police_stations table.
    """
    seed_police_stations_if_needed(db)
    stations = db.query(PoliceStation).all()

    if structured_data is None:
        structured_data = {}

    loc_candidates = [
        incident_location,
        structured_data.get("incident_location", ""),
        structured_data.get("last_seen_location", ""),
        structured_data.get("property_location", ""),
        structured_data.get("location", ""),
    ]
    combined_text = " ".join([c for c in loc_candidates if c]).strip().lower()

    if not combined_text:
        combined_text = complaint_text.lower()

    # Search keyword match
    for st in stations:
        keywords = st.jurisdiction_area.get("keywords", [])
        for kw in keywords:
            if kw in combined_text:
                return st.id, st.station_name

    # Default fallback to first station (Anna Nagar PS)
    default_st = stations[0] if stations else None
    if default_st:
        return default_st.id, default_st.station_name

    return 1, DEFAULT_STATION_NAME
