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
    """Get all running clubs ordered alphabetically"""
    clubs = db.collection("running_clubs").order_by("name").get()
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
    admins = (
        db.collection("admin_emails")
        .where(filter=firestore.FieldFilter("email", "==", email))
        .get()
    )
    if admins:
        db.collection("admin_emails").document(admins[0].id).delete()
        return True
    return False


def get_all_seasons():
    """Get all seasons ordered by name"""
    seasons = db.collection("seasons").order_by("name").get()
    return [season.to_dict()["name"] for season in seasons]


def season_exists(season_name):
    """Check if season exists"""
    existing = (
        db.collection("seasons")
        .where(filter=firestore.FieldFilter("name", "==", season_name))
        .get()
    )
    return len(existing) > 0


def add_season(season_name):
    """Add new season"""
    return db.collection("seasons").add({"name": season_name})


def get_all_races():
    """Get all races ordered by date"""
    races = db.collection("races").order_by("date").get()
    result = []
    for race in races:
        race_data = race.to_dict()
        race_data["id"] = race.id
        result.append(race_data)
    return result


def add_race(name, date, season):
    """Add new race"""
    return db.collection("races").add({"name": name, "date": date, "season": season})


def add_race_results(results):
    """Add race results in batch"""
    batch = db.batch()
    for result in results:
        doc_ref = db.collection("race_results").document()
        batch.set(doc_ref, result)
    batch.commit()


def get_race_results(race_name):
    """Get race results with participant details"""
    results = (
        db.collection("race_results")
        .where(filter=firestore.FieldFilter("race_name", "==", race_name))
        .get()
    )

    # Get race date
    race_date = None
    races = (
        db.collection("races")
        .where(filter=firestore.FieldFilter("name", "==", race_name))
        .get()
    )
    if races:
        race_date = races[0].to_dict().get("date")

    # Get all participants for lookup
    participants = {}
    for p in db.collection("participants").get():
        if not p.to_dict().get("deleted", False):
            participants[p.to_dict().get("barcode")] = p.to_dict()

    result_list = []
    for result in results:
        result_data = result.to_dict()
        result_data["id"] = result.id

        # Add participant details if available
        barcode = result_data.get("barcode")
        if barcode in participants:
            p = participants[barcode]
            result_data["participant_name"] = (
                f"{p.get('first_name', '')} {p.get('last_name', '')}".strip()
            )
            result_data["club"] = p.get("club", "")
            result_data["gender"] = p.get("gender", "")

            # Calculate age category from date_of_birth and race date
            dob = p.get("date_of_birth")
            if dob and race_date:
                from datetime import datetime

                try:
                    birth_date = datetime.strptime(dob, "%Y-%m-%d")
                    race_date_obj = datetime.strptime(race_date, "%Y-%m-%d")
                    age = (
                        race_date_obj.year
                        - birth_date.year
                        - (
                            (race_date_obj.month, race_date_obj.day)
                            < (birth_date.month, birth_date.day)
                        )
                    )

                    if age < 40:
                        result_data["age"] = "Senior"
                    elif age < 50:
                        result_data["age"] = "V40"
                    elif age < 60:
                        result_data["age"] = "V50"
                    elif age < 70:
                        result_data["age"] = "V60"
                    else:
                        result_data["age"] = "V70"
                except ValueError:
                    result_data["age"] = ""
            else:
                result_data["age"] = ""
        else:
            result_data["participant_name"] = ""
            result_data["club"] = ""
            result_data["age"] = ""
            result_data["gender"] = ""

        result_list.append(result_data)

    # Sort by position
    result_list.sort(key=lambda x: x.get("position", "Z999"))
    return result_list


def delete_race_result(result_id):
    """Delete a race result"""
    return db.collection("race_results").document(result_id).delete()


def update_race_result_position(result_id, new_position):
    """Update race result position"""
    return (
        db.collection("race_results")
        .document(result_id)
        .update({"position": new_position})
    )
