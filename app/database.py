import re

from google.cloud import firestore

# Initialize Firestore
db = firestore.Client()

RUNNING_CLUBS = [
    {"id": "Chandler's Ford Swifts", "short_names": ["CF Swifts"]},
    {"id": "Eastleigh Running Club", "short_names": ["Eastleigh"]},
    {"id": "Halterworth Harriers", "short_names": ["Halterworth"]},
    {"id": "Hamwic Harriers", "short_names": ["Hamwic"]},
    {"id": "Hardley Runners", "short_names": ["Hardley"]},
    {"id": "Hedge End Running Club", "short_names": ["Hedge End"]},
    {"id": "Itchen Spitfires Running Club", "short_names": ["Itchen"]},
    {"id": "Lordshill Road Runners", "short_names": ["Lordshill"]},
    {
        "id": "Lymington Triathlon Club & Lymington Athletes",
        "short_names": ["Lymington"],
    },
    {"id": "Netley Abbey Runners", "short_names": ["Netley"]},
    {"id": "New Forest Runners", "short_names": ["New Forest"]},
    {"id": "Romsey Road Runners", "short_names": ["Romsey"]},
    {"id": "Solent Running Sisters", "short_names": ["R Sisters"]},
    {"id": "Southampton Athletic Club", "short_names": ["Soton AC"]},
    {"id": "Southampton Triathlon Club", "short_names": ["Southampton Tri"]},
    {"id": "Stubbington Green Runners", "short_names": ["Stubbington"]},
    {"id": "Totton Running Club", "short_names": ["Totton"]},
    {"id": "Winchester & District AC", "short_names": ["WADAC"]},
    {"id": "Wessex Road Runners", "short_names": ["Wessex"]},
    {"id": "Winchester Fit Club", "short_names": ["Winchester Fit"]},
    {"id": "Winchester Running Club", "short_names": ["WinchesterRC"]},
]


def init_running_clubs():
    """Initialize running clubs in database if not present"""
    clubs_ref = db.collection("clubs")
    existing_clubs = clubs_ref.get()

    if not existing_clubs:
        batch = db.batch()
        for club_data in RUNNING_CLUBS:
            club_ref = clubs_ref.document(club_data["id"])
            batch.set(club_ref, {"short_names": club_data["short_names"]})
        batch.commit()


def validate_barcode(barcode):
    """Validate Parkrun barcode format (A followed by 2-8 digits)"""
    return re.match(r"^A\d{2,8}$", barcode.upper()) is not None


def validate_position_token(token):
    """Validate position token format (P followed by 1-4 digits)"""
    return re.match(r"^P\d{1,4}$", token.upper()) is not None


def calculate_age_category(season_date, dob, age_category_size=5):
    """Calculate age category based on season date, date of birth and category size"""
    from datetime import datetime

    # Parse dates if they are strings
    if isinstance(season_date, str):
        season_date = datetime.strptime(season_date, "%Y-%m-%d")
    if isinstance(dob, str):
        dob = datetime.strptime(dob, "%Y-%m-%d")

    # Calculate age during the season
    age = (
        season_date.year
        - dob.year
        - ((season_date.month, season_date.day) < (dob.month, dob.day))
    )

    if age < 40:
        return "Senior"

    # Calculate the appropriate V category
    base_age = 40
    while base_age <= 80:
        if age < base_age + age_category_size:
            return f"V{base_age}"
        base_age += age_category_size

    return "V80"


def get_clubs():
    """Get all running clubs ordered alphabetically"""
    clubs = db.collection("clubs").order_by("__name__").get()
    result = []
    for club in clubs:
        club_data = club.to_dict()
        result.append(
            {
                "name": club.id,  # Club name is the document ID
                "short_names": club_data.get("short_names", []),
            }
        )
    return result


def get_club(club_name):
    """Get single club by name"""
    return db.collection("clubs").document(club_name).get()


def update_club(club_name, data):
    """Update existing club"""
    return db.collection("clubs").document(club_name).update(data)


def delete_club(club_name):
    """Delete a club"""
    return db.collection("clubs").document(club_name).delete()


def club_exists(club_name):
    """Check if club exists"""
    return db.collection("clubs").document(club_name).get().exists


def add_club(club_name, short_names=None):
    """Add new club with optional short names"""
    club_data = {"short_names": short_names or []}
    return db.collection("clubs").document(club_name).set(club_data)


def validate_and_normalize_club(club_input, clubs):
    """Validate club name using clubs list"""
    for club in clubs:
        # Check exact match with full name
        if club["name"] == club_input:
            return club["name"]

        # Check if input matches any short name
        if club_input in club["short_names"]:
            return club["name"]

    return None


def participant_exists(barcode):
    """Check if participant exists"""
    return db.collection("participants").document(barcode).get().exists


def create_participant(barcode, data):
    """Create new participant using barcode as document ID"""
    from datetime import datetime

    data["created_at"] = datetime.now()
    data["updated_at"] = datetime.now()
    return db.collection("participants").document(barcode).set(data)


def update_participant(barcode, data):
    """Update existing participant"""
    from datetime import datetime

    data["updated_at"] = datetime.now()
    return db.collection("participants").document(barcode).update(data)


def get_participants():
    """Get all participants"""
    participants = db.collection("participants").get()
    result = []
    for p in participants:
        participant_data = p.to_dict()
        participant_data["barcode"] = p.id  # Add barcode from document ID
        result.append(participant_data)
    return result


def get_participant(barcode):
    """Get single participant by barcode"""
    doc = db.collection("participants").document(barcode).get()
    if doc.exists:
        data = doc.to_dict()
        data["barcode"] = doc.id
        return data
    return None


def process_participants_batch(new_participants, updated_participants):
    """Process new and updated participants in batch"""
    from datetime import datetime

    batch_size = 500
    now = datetime.now()

    # Process new participants
    for i in range(0, len(new_participants), batch_size):
        batch = db.batch()
        chunk = new_participants[i : i + batch_size]
        for participant in chunk:
            barcode = participant.pop("barcode")  # Remove barcode from data
            participant["created_at"] = now
            participant["updated_at"] = now
            doc_ref = db.collection("participants").document(barcode)
            batch.set(doc_ref, participant)
        batch.commit()

    # Process updated participants
    for i in range(0, len(updated_participants), batch_size):
        batch = db.batch()
        chunk = updated_participants[i : i + batch_size]
        for barcode, data in chunk:
            data["updated_at"] = now
            doc_ref = db.collection("participants").document(barcode)
            batch.update(doc_ref, data)
        batch.commit()


def delete_participant(barcode):
    """Delete participant"""
    return db.collection("participants").document(barcode).delete()


def init_admin_emails():
    """Initialize admin emails if not present"""
    admins_ref = db.collection("admin_emails")
    existing_admins = admins_ref.get()

    if not existing_admins:
        admins_ref.document("weston.sam@gmail.com").set({})


def get_admin_emails():
    """Get all admin emails"""
    admins = db.collection("admin_emails").get()
    return [admin.id for admin in admins]


def is_admin_email(email):
    """Check if email is an admin"""
    return db.collection("admin_emails").document(email).get().exists


def add_admin_email(email):
    """Add new admin email"""
    return db.collection("admin_emails").document(email).set({})


def remove_admin_email(email):
    """Remove admin email"""
    return db.collection("admin_emails").document(email).delete()


def get_seasons():
    """Get all seasons ordered by name"""
    seasons = db.collection("season").order_by("__name__").get()
    return [season.id for season in seasons]


def get_default_season():
    """Get the default season if one exists"""
    seasons = (
        db.collection("season")
        .where(filter=firestore.FieldFilter("is_default", "==", True))
        .get()
    )
    if seasons:
        return seasons[0].id
    return None


def clear_default_seasons():
    """Clear all default season flags"""
    seasons = (
        db.collection("season")
        .where(filter=firestore.FieldFilter("is_default", "==", True))
        .get()
    )
    batch = db.batch()
    for season in seasons:
        batch.update(season.reference, {"is_default": False})
    batch.commit()


def create_season(
    season_name,
    age_category_size=5,
    is_default=False,
    start_date=None,
    individual_results_best_of=None,
):
    """Create new season"""
    data = {"age_category_size": age_category_size, "is_default": is_default}
    if start_date:
        data["start_date"] = start_date
    if individual_results_best_of:
        data["individual_results_best_of"] = individual_results_best_of
    return db.collection("season").document(season_name).set(data)


def get_season(season_name):
    """Get single season by name"""
    doc = db.collection("season").document(season_name).get()
    if doc.exists:
        data = doc.to_dict()
        return data
    return None


def update_season(season_name, data):
    """Update existing season"""
    return db.collection("season").document(season_name).update(data)


def delete_season(season_name):
    """Delete a season"""
    return db.collection("season").document(season_name).delete()


def get_races_by_season(season_name):
    """Get races for a specific season"""
    races = db.collection("season").document(season_name).collection("races").get()
    result = []
    for race in races:
        race_data = race.to_dict()
        race_data["name"] = race.id  # Race name is the document ID
        result.append(race_data)
    return result


def create_race(season_name, race_name, race_data):
    """Create new race in a season"""
    return (
        db.collection("season")
        .document(season_name)
        .collection("races")
        .document(race_name)
        .set(race_data)
    )


def get_race_results(season_name, race_name):
    """Get results for a specific race"""
    results = (
        db.collection("season")
        .document(season_name)
        .collection("races")
        .document(race_name)
        .collection("results")
        .get()
    )
    result = []
    for res in results:
        result_data = res.to_dict()
        result_data["finish_token"] = res.id
        result.append(result_data)
    return result


def add_race_result(season_name, race_name, finish_token, participant_data):
    """Add result for a race"""
    return (
        db.collection("season")
        .document(season_name)
        .collection("races")
        .document(race_name)
        .collection("results")
        .document(finish_token)
        .set({"participant": participant_data})
    )


def delete_race_result(season_name, race_name, finish_token):
    """Delete a race result"""
    return (
        db.collection("season")
        .document(season_name)
        .collection("races")
        .document(race_name)
        .collection("results")
        .document(finish_token)
        .delete()
    )


def delete_all_race_results(season_name, race_name):
    """Delete all results for a race"""
    results = (
        db.collection("season")
        .document(season_name)
        .collection("races")
        .document(race_name)
        .collection("results")
        .get()
    )

    batch = db.batch()
    for result in results:
        batch.delete(result.reference)
    batch.commit()


def add_race_results_batch(season_name, race_name, results_data):
    """Add multiple race results in batch"""
    batch_size = 500

    for i in range(0, len(results_data), batch_size):
        batch = db.batch()
        chunk = results_data[i : i + batch_size]

        for result_data in chunk:
            finish_token = result_data["finish_token"]
            participant_data = result_data["participant"]

            doc_ref = (
                db.collection("season")
                .document(season_name)
                .collection("races")
                .document(race_name)
                .collection("results")
                .document(finish_token)
            )
            batch.set(doc_ref, {"participant": participant_data})

        batch.commit()


def get_participant_results(participant_id):
    """Get all results for a specific participant across all seasons and races"""
    # Use collection group query to search across all results collections
    results_query = (
        db.collection_group("results")
        .where(
            filter=firestore.FieldFilter(
                "participant.parkrun_barcode_id", "==", participant_id
            )
        )
        .get()
    )

    results = []
    for result in results_query:
        # Extract season and race from document path
        path_parts = result.reference.path.split("/")
        season_name = path_parts[1]
        race_name = path_parts[3]

        # Get race data for date
        race_doc = (
            db.collection("season")
            .document(season_name)
            .collection("races")
            .document(race_name)
            .get()
        )
        race_date = race_doc.to_dict().get("date", "") if race_doc.exists else ""

        result_data = result.to_dict()
        results.append(
            {
                "season": season_name,
                "race_name": race_name,
                "race_date": race_date,
                "finish_token": result.id,
                "participant": result_data.get("participant", {}),
            }
        )

    # Sort by race date (most recent first)
    results.sort(key=lambda x: x.get("race_date", ""), reverse=True)
    return results
