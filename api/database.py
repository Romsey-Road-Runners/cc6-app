from google.cloud import firestore
import re

# Initialize Firestore
db = firestore.Client()

# Predefined running clubs
RUNNING_CLUBS = [
    "Chandler's Ford Swifts",
    "Eastleigh Running Club",
    "Halterworth Harriers",
    "Hamwic Harriers",
    "Hardley Runners",
    "Hedge End Running Club",
    "Itchen Spitfires Running Club",
    "Lordshill Road Runners",
    "Lymington Athletes",
    "Lymington Triathlon Club",
    "Netley Abbey Runners",
    "New Forest Runners",
    "Romsey Road Runners",
    "Solent Running Sisters",
    "Southampton Athletic Club",
    "Southampton Triathlon Club",
    "Stubbington Green Runners",
    "Totton Running Club",
    "Wessex Road Runners",
    "Winchester & District AC",
    "Winchester Fit Club",
    "Winchester Running Club",
]


def init_running_clubs():
    """Initialize running clubs in database if not present"""
    clubs_ref = db.collection("running_clubs")
    existing_clubs = clubs_ref.get()

    if not existing_clubs:
        for club_name in RUNNING_CLUBS:
            clubs_ref.add({"name": club_name})


def get_club_id_by_name(club_name):
    """Get club document ID by name"""
    clubs = (
        db.collection("running_clubs")
        .where(filter=firestore.FieldFilter("name", "==", club_name))
        .get()
    )
    return clubs[0].id if clubs else None


def validate_barcode(barcode):
    """Validate Parkrun barcode format (A followed by 6-7 digits)"""
    return re.match(r"^A\d{6,7}$", barcode.upper()) is not None
