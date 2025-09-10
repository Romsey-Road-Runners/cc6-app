import re

from google.cloud import firestore

# Initialize Firestore
db = firestore.Client()


def init_running_clubs():
    """Initialize running clubs in database if not present"""
    clubs_ref = db.collection("running_clubs")
    existing_clubs = clubs_ref.get()

    if not existing_clubs:
        for club_data in RUNNING_CLUBS:
            clubs_ref.add(club_data)


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
    return re.match(r"^A\d{2,8}$", barcode.upper()) is not None


def calculate_age_category(age, age_category_size=5):
    """Calculate age category based on age and category size"""
    if age < 40:
        return "Senior"

    # Calculate the appropriate V category
    base_age = 40
    while base_age <= 80:
        if age < base_age + age_category_size:
            return f"V{base_age}"
        base_age += age_category_size

    return "V80"  # Maximum category


def get_all_clubs():
    """Get all running clubs ordered alphabetically"""
    clubs = db.collection("running_clubs").order_by("name").get()
    result = []
    for club in clubs:
        club_data = club.to_dict()
        result.append(
            {
                "id": club.id,
                "name": club_data["name"],
                "short_names": club_data.get("short_names", []),
            }
        )
    return result


def get_club(club_id):
    """Get single club"""
    return db.collection("running_clubs").document(club_id).get()


def update_club(club_id, data):
    """Update existing club"""
    return db.collection("running_clubs").document(club_id).update(data)


def delete_club(club_id):
    """Delete a club"""
    return db.collection("running_clubs").document(club_id).delete()


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


RUNNING_CLUBS = [
    {"name": "Chandler's Ford Swifts", "short_names": ["CF Swifts"]},
    {"name": "Eastleigh Running Club", "short_names": ["Eastleigh"]},
    {"name": "Halterworth Harriers", "short_names": ["Halterworth"]},
    {"name": "Hamwic Harriers", "short_names": ["Hamwic"]},
    {"name": "Hardley Runners", "short_names": ["Hardley"]},
    {"name": "Hedge End Running Club", "short_names": ["Hedge End"]},
    {"name": "Itchen Spitfires Running Club", "short_names": ["Itchen"]},
    {"name": "Lordshill Road Runners", "short_names": ["Lordshill"]},
    {
        "name": "Lymington Triathlon Club & Lymington Athletes",
        "short_names": ["Lymington"],
    },
    {"name": "Netley Abbey Runners", "short_names": ["Netley"]},
    {"name": "New Forest Runners", "short_names": ["New Forest"]},
    {"name": "Romsey Road Runners", "short_names": ["Romsey"]},
    {"name": "Solent Running Sisters", "short_names": ["R Sisters"]},
    {"name": "Southampton Athletic Club", "short_names": ["Soton AC"]},
    {"name": "Southampton Triathlon Club", "short_names": ["Southampton Tri"]},
    {"name": "Stubbington Green Runners", "short_names": ["Stubbington"]},
    {"name": "Totton Running Club", "short_names": ["Totton"]},
    {"name": "Winchester & District AC", "short_names": ["WADAC"]},
    {"name": "Wessex Road Runners", "short_names": ["Wessex"]},
    {"name": "Winchester Fit Club", "short_names": ["Winchester Fit"]},
    {"name": "Winchester Running Club", "short_names": ["WinchesterRC"]},
]


def add_club(club_name, short_names=None):
    """Add new club with optional short names"""
    club_data = {"name": club_name}
    if short_names:
        club_data["short_names"] = short_names
    return db.collection("running_clubs").add(club_data)


def get_participant_by_barcode(barcode):
    """Get participant by barcode"""
    participants = (
        db.collection("participants")
        .where(filter=firestore.FieldFilter("barcode", "==", barcode))
        .get()
    )
    if participants and not participants[0].to_dict().get("deleted", False):
        participant_data = participants[0].to_dict()
        participant_data["id"] = participants[0].id
        return participant_data
    return None


def process_participants_batch(new_participants, updated_participants):
    """Process new and updated participants in batch"""
    batch_size = 500

    # Process new participants
    for i in range(0, len(new_participants), batch_size):
        batch = db.batch()
        chunk = new_participants[i : i + batch_size]
        for participant in chunk:
            participant["registered_at"] = firestore.SERVER_TIMESTAMP
            doc_ref = db.collection("participants").document()
            batch.set(doc_ref, participant)
        batch.commit()

    # Process updated participants
    for i in range(0, len(updated_participants), batch_size):
        batch = db.batch()
        chunk = updated_participants[i : i + batch_size]
        for participant_id, data in chunk:
            doc_ref = db.collection("participants").document(participant_id)
            batch.update(doc_ref, data)
        batch.commit()


def validate_and_normalize_club(club_input):
    """Validate club name and return full name if valid"""
    clubs = get_all_clubs()

    for club in clubs:
        # Check exact match with full name
        if club["name"] == club_input:
            return club["name"]

        # Check if input matches any short name
        if club_input in club["short_names"]:
            return club["name"]

    return None


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


def get_all_seasons_with_ids():
    """Get all seasons with IDs ordered by name"""
    seasons = db.collection("seasons").order_by("name").get()
    result = []
    for season in seasons:
        season_data = season.to_dict()
        season_data["id"] = season.id
        result.append(season_data)
    return result


def get_races_by_season(season_id):
    """Get races for a specific season"""
    # Get season name by ID
    season_doc = db.collection("seasons").document(season_id).get()
    if not season_doc.exists:
        return []

    season_name = season_doc.to_dict().get("name")

    # Get races for this season
    races = (
        db.collection("races")
        .where(filter=firestore.FieldFilter("season", "==", season_name))
        .get()
    )

    result = []
    for race in races:
        race_data = race.to_dict()
        race_data["id"] = race.id
        result.append(race_data)

    # Sort by date in Python instead of Firestore
    result.sort(key=lambda x: x.get("date", ""))
    return result


def season_exists(season_name):
    """Check if season exists"""
    existing = (
        db.collection("seasons")
        .where(filter=firestore.FieldFilter("name", "==", season_name))
        .get()
    )
    return len(existing) > 0


def add_season(season_name, age_category_size):
    """Add new season with age category size"""
    return db.collection("seasons").add(
        {"name": season_name, "age_category_size": age_category_size}
    )


def get_season(season_id):
    """Get single season"""
    return db.collection("seasons").document(season_id).get()


def update_season(season_id, data):
    """Update existing season"""
    return db.collection("seasons").document(season_id).update(data)


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

                    # Get season age category size
                    season_name = None
                    if races:
                        season_name = races[0].to_dict().get("season")

                    age_category_size = 5  # Default
                    if season_name:
                        seasons = (
                            db.collection("seasons")
                            .where(
                                filter=firestore.FieldFilter("name", "==", season_name)
                            )
                            .get()
                        )
                        if seasons:
                            age_category_size = (
                                seasons[0].to_dict().get("age_category_size", 5)
                            )

                    result_data["age_category"] = calculate_age_category(
                        age, age_category_size
                    )
                except ValueError:
                    result_data["age_category"] = ""
            else:
                result_data["age_category"] = ""
        else:
            result_data["participant_name"] = ""
            result_data["club"] = ""
            result_data["age_category"] = ""
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


def delete_all_race_results(race_name):
    """Delete all results for a race"""
    results = (
        db.collection("race_results")
        .where(filter=firestore.FieldFilter("race_name", "==", race_name))
        .get()
    )

    batch = db.batch()
    for result in results:
        batch.delete(result.reference)
    batch.commit()
