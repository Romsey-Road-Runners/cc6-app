import re

from google.cloud import firestore

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


def get_all_clubs():
    """Get all running clubs"""
    clubs = db.collection("running_clubs").get()
    return [club.to_dict()["name"] for club in clubs]


def club_exists(club_name):
    """Check if club exists"""
    existing = (
        db.collection("running_clubs")
        .where(filter=firestore.FieldFilter("name", "==", club_name))
        .get()
    )
    return len(existing) > 0


def barcode_exists(barcode, exclude_participant_id=None):
    """Check if barcode already exists"""
    existing = (
        db.collection("participants")
        .where(filter=firestore.FieldFilter("barcode", "==", barcode))
        .get()
    )
    if not existing:
        return False
    return exclude_participant_id is None or existing[0].id != exclude_participant_id


def create_participant(data):
    """Create new participant"""
    data["registered_at"] = firestore.SERVER_TIMESTAMP
    return db.collection("participants").add(data)


def update_participant(participant_id, data):
    """Update existing participant"""
    return db.collection("participants").document(participant_id).update(data)


def get_participants():
    """Get all non-deleted participants"""
    all_participants = (
        db.collection("participants")
        .order_by("registered_at", direction=firestore.Query.DESCENDING)
        .get()
    )
    participants = []
    for p in all_participants:
        if not p.to_dict().get("deleted", False):
            participant_data = p.to_dict()
            participant_data["id"] = p.id
            participants.append(participant_data)
    return participants


def get_participant(participant_id):
    """Get single participant"""
    return db.collection("participants").document(participant_id).get()


def get_clubs_ordered():
    """Get all clubs ordered by name"""
    return db.collection("running_clubs").order_by("name").get()


def add_club(club_name):
    """Add new club"""
    return db.collection("running_clubs").add({"name": club_name})


def soft_delete_participant(participant_id):
    """Soft delete participant"""
    return (
        db.collection("participants").document(participant_id).update({"deleted": True})
    )


def init_admin_emails():
    """Initialize admin emails if not present"""
    admins_ref = db.collection("admin_emails")
    existing_admins = admins_ref.get()

    if not existing_admins:
        admins_ref.add({"email": "weston.sam@gmail.com"})


def get_admin_emails():
    """Get all admin emails"""
    admins = db.collection("admin_emails").get()
    return [admin.to_dict()["email"] for admin in admins]


def is_admin_email(email):
    """Check if email is an admin"""
    return email in get_admin_emails()


def add_admin_email(email):
    """Add new admin email"""
    return db.collection("admin_emails").add({"email": email})


def remove_admin_email(email):
    """Remove admin email"""
    admins = db.collection("admin_emails").where("email", "==", email).get()
    if admins:
        db.collection("admin_emails").document(admins[0].id).delete()
        return True
    return False
