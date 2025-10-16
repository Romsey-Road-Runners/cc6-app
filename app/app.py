import os

from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

import database
from api import api
from auth import init_oauth, login_required

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-key-change-this")

# Initialize OAuth
google = init_oauth(app)

# Register API blueprint
app.register_blueprint(api, url_prefix="/api")


# Initialize data on startup
database.init_running_clubs()
database.init_admin_emails()


@app.route("/")
def index():
    """Championship results page (main page)"""
    return render_template("championship.html")


@app.route("/register")
def register_page():
    """Registration page"""
    return render_template("index.html")


@app.route("/results")
def public_results():
    """Public race results page"""
    # Get query parameters for pre-selection
    selected_season = request.args.get("season")
    selected_race = request.args.get("race")

    return render_template(
        "public_results.html",
        selected_season=selected_season,
        selected_race=selected_race,
    )


@app.route("/participant/<participant_id>")
def participant_results(participant_id):
    """Participant results page"""
    results = database.get_participant_results(participant_id)
    participant = database.get_participant(participant_id)

    if not participant:
        flash("Participant not found")
        return redirect(url_for("index"))

    participant_name = f"{participant['first_name']} {participant['last_name']}"
    return render_template(
        "participant_results.html",
        participant=participant,
        participant_name=participant_name,
        results=results,
    )


@app.route("/robots.txt")
def robots_txt():
    return app.send_static_file("robots.txt")


@app.route("/register", methods=["POST"])
@app.route("/edit_participant/<participant_id>", methods=["POST"])
def register(participant_id=None):
    # Require authentication for edits
    if participant_id and "user" not in session:
        return redirect(url_for("login"))

    first_name = request.form.get("first_name", "").strip()
    last_name = request.form.get("last_name", "").strip()
    gender = request.form.get("gender", "")
    dob = request.form.get("dob", "")
    barcode = request.form.get("barcode", "").strip().upper()
    club = request.form.get("club", "")

    # Validation
    if not first_name:
        flash("First name is required")
        return redirect(url_for("participants" if participant_id else "register_page"))

    if not last_name:
        flash("Last name is required")
        return redirect(url_for("participants" if participant_id else "register_page"))

    if not gender:
        flash("Gender is required")
        return redirect(url_for("participants" if participant_id else "register_page"))

    if not dob:
        flash("Date of birth is required")
        return redirect(url_for("participants" if participant_id else "register_page"))

    if not database.validate_barcode(barcode):
        flash("Invalid barcode format (should be A followed by 6-7 digits)")
        return redirect(url_for("participants" if participant_id else "register_page"))

    # Validate club exists
    if not database.club_exists(club):
        flash("Please select a valid running club")
        return redirect(url_for("participants" if participant_id else "register_page"))

    # Check if barcode already exists (skip check if editing same participant)
    if participant_id != barcode and database.participant_exists(barcode):
        flash("This barcode is already registered")
        return redirect(url_for("participants" if participant_id else "register_page"))

    # Save or update Firestore
    try:
        data = {
            "first_name": first_name,
            "last_name": last_name,
            "gender": gender,
            "date_of_birth": dob,
            "barcode": barcode,
            "club": club,
        }

        if participant_id:
            database.update_participant(barcode, data)
            flash("Participant updated successfully!")
        else:
            database.create_participant(barcode, data)
            flash("Registration successful!")
    except Exception:
        flash("Operation failed. Please try again.")

    return redirect(url_for("participants" if participant_id else "register_page"))


@app.route("/login")
def login():
    redirect_uri = url_for("auth_callback", _external=True, _scheme="https")
    return google.authorize_redirect(redirect_uri)


@app.route("/auth/callback")
def auth_callback():
    token = google.authorize_access_token()
    user = token.get("userinfo")
    if user and database.is_admin_email(user.get("email")):
        session["user"] = user
        return redirect(url_for("participants"))
    else:
        flash("Access denied. Unauthorized email address.")
        return redirect(url_for("register_page"))


@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("index"))


@app.route("/participants")
@login_required
def participants():
    """View all registered participants"""
    participants = database.get_participants()
    return render_template(
        "participants.html", participants=participants, user=session.get("user")
    )


@app.route("/export_participants")
@login_required
def export_participants():
    """Export participants to CSV"""
    import csv
    import io

    from flask import make_response

    participants = database.get_participants()

    output = io.StringIO()
    writer = csv.writer(output)

    # Write header
    writer.writerow(["ID", "Fname", "LName", "Gender", "DOB", "Club"])

    # Write participant data
    for participant in participants:
        # Format date from YYYY-MM-DD to dd/mm/yyyy
        dob = participant.get("date_of_birth", "")
        if dob:
            try:
                from datetime import datetime

                date_obj = datetime.strptime(dob, "%Y-%m-%d")
                dob = date_obj.strftime("%d/%m/%Y")
            except ValueError:
                pass  # Keep original format if parsing fails

        writer.writerow(
            [
                participant.get("barcode", ""),
                participant.get("first_name", ""),
                participant.get("last_name", ""),
                participant.get("gender", ""),
                dob,
                participant.get("club", ""),
            ]
        )

    response = make_response(output.getvalue())
    response.headers["Content-Disposition"] = "attachment; filename=participants.csv"
    response.headers["Content-type"] = "text/csv"

    return response


@app.route("/clubs")
@login_required
def clubs():
    """View all running clubs"""
    clubs = database.get_clubs()
    return render_template("clubs.html", clubs=clubs, user=session.get("user"))


@app.route("/add_club", methods=["POST"])
@login_required
def add_club():
    """Add a new running club"""
    club_name = request.form.get("club_name", "").strip()
    short_names = request.form.get("short_names", "").strip()

    if not club_name:
        flash("Club name is required")
        return redirect(url_for("clubs"))

    # Check if club already exists
    if database.club_exists(club_name):
        flash("Club already exists")
        return redirect(url_for("clubs"))

    # Parse short names
    short_names_list = (
        [name.strip() for name in short_names.split(",") if name.strip()]
        if short_names
        else []
    )

    # Add new club
    try:
        database.add_club(club_name, short_names_list)
        flash("Club added successfully!")
    except Exception:
        flash("Failed to add club. Please try again.")

    return redirect(url_for("clubs"))


@app.route("/edit_club/<club_id>", methods=["GET"])
@login_required
def edit_club(club_id):
    """Show edit club form"""
    club = database.get_club(club_id)
    return render_template(
        "edit_club.html",
        club=club,
        club_id=club_id,
        user=session.get("user"),
    )


@app.route("/edit_club/<club_id>", methods=["POST"])
@login_required
def update_club(club_id):
    """Update existing club"""
    club_name = request.form.get("club_name", "").strip()
    short_names = request.form.get("short_names", "").strip()

    if not club_name:
        flash("Club name is required")
        return redirect(url_for("edit_club", club_id=club_id))

    # Parse short names
    short_names_list = (
        [name.strip() for name in short_names.split(",") if name.strip()]
        if short_names
        else []
    )

    try:
        database.update_club(
            club_id, {"name": club_name, "short_names": short_names_list}
        )
        flash("Club updated successfully!")
    except Exception:
        flash("Failed to update club.")

    return redirect(url_for("clubs"))


@app.route("/delete_club/<club_id>", methods=["POST"])
@login_required
def delete_club(club_id):
    """Delete a club"""
    try:
        database.delete_club(club_id)
        flash("Club deleted successfully!")
    except Exception:
        flash("Failed to delete club.")
    return redirect(url_for("clubs"))


@app.route("/upload_participants", methods=["POST"])
@login_required
def upload_participants():
    """Upload participants from CSV"""
    if "file" not in request.files:
        flash("No file selected")
        return redirect(url_for("participants"))

    file = request.files["file"]
    if file.filename == "":
        flash("No file selected")
        return redirect(url_for("participants"))

    try:
        import csv
        import io
        from datetime import datetime

        content = file.read().decode("utf-8")
        csv_reader = csv.reader(io.StringIO(content))

        # Skip header row
        next(csv_reader, None)

        # Get clubs list once for validation
        clubs = database.get_clubs()

        new_participants = []
        updated_participants = []
        seen_barcodes = set()
        file_duplicates = 0
        unchanged_records = 0
        invalid_rows = 0
        invalid_row_details = []

        for row in csv_reader:
            if len(row) < 6:
                invalid_rows += 1
                continue

            barcode = row[0].strip().upper()
            fname = row[1].strip()
            lname = row[2].strip()
            gender = row[3].strip()
            dob = row[4].strip()
            club = row[5].strip()

            # Skip if invalid barcode
            if not database.validate_barcode(barcode):
                invalid_rows += 1
                invalid_row_details.append(
                    f"Row {csv_reader.line_num}: Invalid barcode '{barcode}'"
                )
                continue

            # Skip duplicates in file
            if barcode in seen_barcodes:
                file_duplicates += 1
                continue

            # Convert date format from DD/MM/YYYY to YYYY-MM-DD
            try:
                if dob:
                    date_obj = datetime.strptime(dob, "%d/%m/%Y")
                    dob = date_obj.strftime("%Y-%m-%d")
            except ValueError:
                invalid_rows += 1
                invalid_row_details.append(
                    f"Row {csv_reader.line_num}: Invalid date '{row[4]}'"
                )
                continue

            # Skip if required fields missing or invalid gender
            if not all([fname, lname, gender, dob, club]):
                invalid_rows += 1
                invalid_row_details.append(
                    f"Row {csv_reader.line_num}: Missing required fields"
                )
                continue

            if gender not in ["Male", "Female"]:
                invalid_rows += 1
                invalid_row_details.append(
                    f"Row {csv_reader.line_num}: Invalid gender '{gender}'"
                )
                continue

            # Validate and normalize club name
            normalized_club = database.validate_and_normalize_club(club, clubs)
            if not normalized_club:
                invalid_rows += 1
                invalid_row_details.append(
                    f"Row {csv_reader.line_num}: Invalid club '{club}'"
                )
                continue

            # Check if participant exists in database
            existing_participant = database.get_participant(barcode)
            if existing_participant:
                # Compare data to see if update is needed
                new_data = {
                    "first_name": fname,
                    "last_name": lname,
                    "gender": gender,
                    "date_of_birth": dob,
                    "club": normalized_club,
                }

                # Check if any field has changed
                has_changes = False
                for key, value in new_data.items():
                    if existing_participant.get(key) != value:
                        has_changes = True
                        break

                if has_changes:
                    updated_participants.append((barcode, new_data))
                else:
                    unchanged_records += 1
                continue

            seen_barcodes.add(barcode)
            new_participants.append(
                {
                    "first_name": fname,
                    "last_name": lname,
                    "gender": gender,
                    "date_of_birth": dob,
                    "barcode": barcode,
                    "club": normalized_club,
                }
            )

        if new_participants or updated_participants:
            database.process_participants_batch(new_participants, updated_participants)

        message = f"Added {len(new_participants)} new participants."
        if len(updated_participants) > 0:
            message += f" Updated {len(updated_participants)} existing participants."
        if unchanged_records > 0:
            message += f" {unchanged_records} records unchanged."
        if file_duplicates > 0:
            message += f" Skipped {file_duplicates} duplicates in file."
        if invalid_rows > 0:
            message += f" Skipped {invalid_rows} invalid rows."
        flash(message)

        # Flash invalid row details
        for detail in invalid_row_details:
            flash(detail)

    except Exception:
        flash("Failed to process CSV file. Please check the format.")

    return redirect(url_for("participants"))


@app.route("/edit_participant/<participant_id>", methods=["GET"])
@login_required
def edit_participant(participant_id):
    """Show edit participant form"""
    participant = database.get_participant(participant_id)
    clubs = database.get_clubs()
    return render_template(
        "edit_participant.html",
        participant=participant,
        clubs=clubs,
        user=session.get("user"),
    )


@app.route("/delete_participant/<participant_id>", methods=["POST"])
@login_required
def delete_participant(participant_id):
    """Delete a participant"""
    try:
        database.delete_participant(participant_id)
        flash("Participant deleted successfully!")
    except Exception:
        flash("Failed to delete participant.")
    return redirect(url_for("participants"))


@app.route("/admins")
@login_required
def admins():
    """View all admin emails"""
    admin_emails = database.get_admin_emails()
    return render_template(
        "admins.html", admin_emails=admin_emails, user=session.get("user")
    )


@app.route("/add_admin", methods=["POST"])
@login_required
def add_admin():
    """Add a new admin email"""
    email = request.form.get("email", "").strip()

    if not email:
        flash("Email is required")
        return redirect(url_for("admins"))

    if email in database.get_admin_emails():
        flash("Email already exists")
        return redirect(url_for("admins"))

    try:
        database.add_admin_email(email)
        flash("Admin email added successfully!")
    except Exception:
        flash("Failed to add admin email.")

    return redirect(url_for("admins"))


@app.route("/remove_admin", methods=["POST"])
@login_required
def remove_admin():
    """Remove an admin email"""
    email = request.form.get("email", "").strip()

    if database.remove_admin_email(email):
        flash("Admin email removed successfully!")
    else:
        flash("Failed to remove admin email.")

    return redirect(url_for("admins"))


@app.route("/seasons")
@login_required
def seasons():
    """View all seasons"""
    season_names = database.get_seasons()
    seasons_with_data = []
    for season_name in season_names:
        season_data = database.get_season(season_name)
        if season_data:
            season_data["name"] = season_name
            seasons_with_data.append(season_data)
        else:
            seasons_with_data.append({"name": season_name, "age_category_size": 5})
    return render_template(
        "seasons.html", seasons=seasons_with_data, user=session.get("user")
    )


@app.route("/add_season", methods=["POST"])
@login_required
def add_season():
    """Add a new season"""
    season_name = request.form.get("season_name", "").strip()
    start_date = request.form.get("start_date", "").strip()
    is_default = request.form.get("is_default") == "true"
    individual_results_best_of = request.form.get(
        "individual_results_best_of", ""
    ).strip()

    try:
        age_category_size = int(request.form.get("age_category_size", 5))
    except ValueError:
        flash("Invalid age category size")
        return redirect(url_for("seasons"))

    if not season_name:
        flash("Season name is required")
        return redirect(url_for("seasons"))

    # Validate season name for Firestore compatibility
    if "/" in season_name:
        flash("Season name cannot contain forward slashes (/)")
        return redirect(url_for("seasons"))

    # Check if season already exists
    if database.get_season(season_name):
        flash("Season already exists")
        return redirect(url_for("seasons"))

    try:
        # If setting as default, clear other defaults first
        if is_default:
            database.clear_default_seasons()

        database.create_season(
            season_name,
            age_category_size,
            is_default,
            start_date,
            individual_results_best_of,
        )
        flash("Season added successfully!")
    except Exception as e:
        print(f"Error creating season: {e}")
        flash(f"Failed to add season: {str(e)}")

    return redirect(url_for("seasons"))


@app.route("/edit_season/<season_name>", methods=["GET"])
@login_required
def edit_season(season_name):
    """Show edit season form"""
    season = database.get_season(season_name)
    return render_template(
        "edit_season.html",
        season=season,
        season_name=season_name,
        user=session.get("user"),
    )


@app.route("/edit_season/<season_name>", methods=["POST"])
@login_required
def update_season(season_name):
    """Update existing season"""
    age_category_size = int(request.form.get("age_category_size", 5))
    start_date = request.form.get("start_date", "").strip()
    is_default = request.form.get("is_default") == "true"
    individual_results_best_of = request.form.get(
        "individual_results_best_of", ""
    ).strip()

    try:
        # If setting as default, clear other defaults first
        if is_default:
            database.clear_default_seasons()

        update_data = {
            "age_category_size": age_category_size,
            "start_date": start_date,
            "is_default": is_default,
        }
        if individual_results_best_of:
            update_data["individual_results_best_of"] = individual_results_best_of

        database.update_season(season_name, update_data)
        flash("Season updated successfully!")
    except Exception:
        flash("Failed to update season.")

    return redirect(url_for("seasons"))


@app.route("/delete_season/<season_name>", methods=["POST"])
@login_required
def delete_season(season_name):
    """Delete a season"""
    try:
        database.delete_season(season_name)
        flash("Season deleted successfully!")
    except Exception:
        flash("Failed to delete season.")
    return redirect(url_for("seasons"))


@app.route("/races")
@login_required
def races():
    """View all races"""
    seasons = database.get_seasons()
    all_races = []
    for season in seasons:
        races = database.get_races_by_season(season)
        for race in races:
            race["season"] = season
            all_races.append(race)
    return render_template("races.html", races=all_races, user=session.get("user"))


@app.route("/add_race")
@login_required
def add_race_page():
    """Show add race form"""
    return render_template("add_race.html", user=session.get("user"))


@app.route("/add_race", methods=["POST"])
@login_required
def add_race():
    """Add a new race"""
    name = request.form.get("name", "").strip()
    date = request.form.get("date", "")
    season = request.form.get("season", "")
    organising_clubs = request.form.getlist("organising_clubs")

    if not name:
        flash("Race name is required")
        return redirect(url_for("races"))

    if not date:
        flash("Race date is required")
        return redirect(url_for("races"))

    if not season:
        flash("Season is required")
        return redirect(url_for("races"))

    # Validate season exists
    if not database.get_season(season):
        flash("Selected season does not exist")
        return redirect(url_for("races"))

    try:
        race_data = {"date": date, "organising_clubs": organising_clubs}
        database.create_race(season, name, race_data)
        flash("Race added successfully!")
    except Exception:
        flash("Failed to add race.")

    return redirect(url_for("races"))


@app.route("/race_results/<season_name>/<race_name>")
@login_required
def race_results(season_name, race_name):
    """View race results"""
    results = database.get_race_results(season_name, race_name)

    return render_template(
        "race_results.html",
        results=results,
        race_name=race_name,
        season=season_name,
        user=session.get("user"),
    )


@app.route(
    "/delete_race_result/<season_name>/<race_name>/<finish_token>", methods=["POST"]
)
@login_required
def delete_race_result(season_name, race_name, finish_token):
    """Delete a race result"""
    try:
        database.delete_race_result(season_name, race_name, finish_token)
        flash("Race result deleted successfully!")
    except Exception:
        flash("Failed to delete race result.")

    return redirect(request.referrer or url_for("races"))


@app.route("/delete_all_race_results/<season_name>/<race_name>", methods=["POST"])
@login_required
def delete_all_race_results(season_name, race_name):
    """Delete all results for a race"""
    try:
        database.delete_all_race_results(season_name, race_name)
        flash("All race results deleted successfully!")
    except Exception:
        flash("Failed to delete race results.")

    return redirect(request.referrer or url_for("races"))


@app.route("/process_upload_results", methods=["POST"])
@login_required
def process_upload_results():
    """Process uploaded CSV results"""
    season_name = request.form.get("season_name", "")
    race_name = request.form.get("race_name", "")

    if not season_name or not race_name:
        flash("Season and race name are required")
        return redirect(request.referrer or url_for("races"))

    if "file" not in request.files:
        flash("No file selected")
        return redirect(request.referrer or url_for("races"))

    file = request.files["file"]
    if file.filename == "":
        flash("No file selected")
        return redirect(request.referrer or url_for("races"))

    try:
        import csv
        import io

        # Get season data once for age calculation
        season_data = database.get_season(season_name)
        season_start_date = season_data.get("start_date") if season_data else None

        if not season_start_date:
            flash("Season start date is required for results upload")
            return redirect(request.referrer or url_for("races"))

        content = file.read().decode("utf-8-sig")  # Handle BOM
        csv_reader = csv.reader(io.StringIO(content))

        results_data = []
        seen_tokens = set()
        duplicates = []
        invalid_barcodes = 0
        invalid_tokens = 0
        row_count = 0

        for row in csv_reader:
            row_count += 1
            if len(row) < 2:
                continue

            barcode = row[0].strip().lstrip("\ufeff")  # Remove BOM if present
            finish_token = row[1].strip()

            if not finish_token:
                continue

            # Validate barcode and position token formats
            if not database.validate_barcode(barcode):
                invalid_barcodes += 1
                continue

            if not database.validate_position_token(finish_token):
                invalid_tokens += 1
                continue

            if finish_token in seen_tokens:
                duplicates.append(finish_token)
                continue

            seen_tokens.add(finish_token)

            # Get participant data
            participant = database.get_participant(barcode)
            if participant:
                # Calculate age category using season start date
                try:
                    age_category = database.calculate_age_category(
                        season_start_date,
                        participant["date_of_birth"],
                        season_data.get("age_category_size", 5),
                    )
                except Exception:
                    age_category = "Unknown"

                participant_data = {
                    "first_name": participant["first_name"],
                    "last_name": participant["last_name"],
                    "gender": participant["gender"],
                    "age_category": age_category,
                    "club": participant["club"],
                    "parkrun_barcode_id": barcode,
                }
            else:
                # Unknown participant
                participant_data = {
                    "parkrun_barcode_id": barcode,
                }

            results_data.append(
                {"finish_token": finish_token, "participant": participant_data}
            )

        if results_data:
            database.add_race_results_batch(season_name, race_name, results_data)

        message = f"Uploaded {len(results_data)} results successfully!"
        if duplicates:
            message += f" Warning: {len(duplicates)} duplicate finish tokens were skipped: {', '.join(duplicates)}."
        if invalid_barcodes > 0:
            message += f" Skipped {invalid_barcodes} rows with invalid barcodes."
        if invalid_tokens > 0:
            message += f" Skipped {invalid_tokens} rows with invalid position tokens."

        flash(message)

    except Exception as e:
        flash(f"Failed to process CSV file: {str(e)}")

    return redirect(request.referrer or url_for("races"))


@app.route("/add_manual_result", methods=["POST"])
@login_required
def add_manual_result():
    """Add a manual race result"""
    season_name = request.form.get("season_name", "").strip()
    race_name = request.form.get("race_name", "").strip()
    barcode = request.form.get("barcode", "").strip()
    position_token = request.form.get(
        "position_token", ""
    ).strip()  # Template uses position_token

    if not all([season_name, race_name, barcode, position_token]):
        missing_fields = []
        if not season_name:
            missing_fields.append("season_name")
        if not race_name:
            missing_fields.append("race_name")
        if not barcode:
            missing_fields.append("barcode")
        if not position_token:
            missing_fields.append("position_token")
        flash(f"Missing required fields: {', '.join(missing_fields)}")
        return redirect(request.referrer or url_for("races"))

    # Validate barcode format
    if not database.validate_barcode(barcode):
        flash("Invalid barcode format")
        return redirect(request.referrer or url_for("races"))

    # Validate position token format
    if not database.validate_position_token(position_token):
        flash("Position token must be P followed by 1-4 digits (e.g., P1, P123)")
        return redirect(request.referrer or url_for("races"))

    try:
        # Get participant data
        participant = database.get_participant(barcode)
        if not participant:
            flash("Participant not found")
            return redirect(request.referrer or url_for("races"))

        # Get season data for age calculation
        season_data = database.get_season(season_name)
        season_start_date = season_data.get("start_date") if season_data else None

        if not season_start_date:
            flash("Season start date is required for results upload")
            return redirect(request.referrer or url_for("races"))

        # Calculate age category using season start date
        try:
            age_category = database.calculate_age_category(
                season_start_date,
                participant["date_of_birth"],
                season_data.get("age_category_size", 5),
            )
        except Exception:
            age_category = "Unknown"

        participant_data = {
            "first_name": participant["first_name"],
            "last_name": participant["last_name"],
            "gender": participant["gender"],
            "age_category": age_category,
            "club": participant["club"],
            "parkrun_barcode_id": barcode,
        }

        database.add_race_result(
            season_name, race_name, position_token, participant_data
        )
        flash("Manual result added successfully!")
    except Exception as e:
        print(f"Error adding manual result: {e}")
        flash(f"Failed to add manual result: {str(e)}")

    return redirect(request.referrer or url_for("races"))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
