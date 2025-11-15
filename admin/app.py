import os
import sys

# Add parent directory to path for shared modules
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "shared_libs"))

from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_compress import Compress
import database
from auth import init_oauth, login_required

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-key-change-this")
Compress(app)

# Initialize OAuth
google = init_oauth(app)

# Initialize data on startup
database.init_running_clubs()
database.init_admin_emails()


@app.route("/")
def index():
    """Admin dashboard"""
    return redirect(url_for("participants"))


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
        return redirect(url_for("login"))


@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))


@app.route("/participants")
@login_required
def participants():
    """View all registered participants"""
    page = int(request.args.get("page", 1))
    search = request.args.get("search", "").strip()
    result = database.get_participants(page=page, search=search if search else None)
    return render_template(
        "participants.html",
        participants=result["participants"],
        pagination=result,
        search=search,
        user=session.get("user"),
    )


@app.route("/clubs")
@login_required
def clubs():
    """View all running clubs"""
    clubs = database.get_clubs()
    return render_template("clubs.html", clubs=clubs, user=session.get("user"))


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


@app.route("/admins")
@login_required
def admins():
    """View all admin emails"""
    admin_emails = database.get_admin_emails()
    return render_template(
        "admins.html", admin_emails=admin_emails, user=session.get("user")
    )


@app.route("/api/participants")
@login_required
def api_participants():
    """Get participants as JSON"""
    result = database.get_participants()
    if isinstance(result, dict) and "participants" in result:
        return result["participants"]
    return result


@app.route("/add_admin", methods=["POST"])
@login_required
def add_admin():
    """Add admin email"""
    email = request.form.get("email", "").strip()
    if email:
        try:
            database.add_admin_email(email)
            flash(f"Admin email {email} added successfully")
        except Exception as e:
            flash(f"Error adding admin: {str(e)}")
    return redirect(url_for("admins"))


@app.route("/remove_admin", methods=["POST"])
@login_required
def remove_admin():
    """Remove admin email"""
    email = request.form.get("email", "").strip()
    if email:
        try:
            database.remove_admin_email(email)
            flash(f"Admin email {email} removed successfully")
        except Exception as e:
            flash(f"Error removing admin: {str(e)}")
    return redirect(url_for("admins"))


@app.route("/add_season", methods=["POST"])
@login_required
def add_season():
    """Add new season"""
    season_name = request.form.get("season_name", "").strip()
    if season_name:
        try:
            database.create_season(season_name)
            flash(f"Season {season_name} created successfully")
        except Exception as e:
            flash(f"Error creating season: {str(e)}")
    return redirect(url_for("seasons"))


@app.route("/add_race", methods=["POST"])
@login_required
def add_race():
    """Add new race"""
    name = request.form.get("name", "").strip()
    date = request.form.get("date", "").strip()
    season = request.form.get("season", "").strip()

    if name and date and season:
        try:
            database.create_race(season, name, date)
            flash(f"Race {name} created successfully")
        except Exception as e:
            flash(f"Error creating race: {str(e)}")
    return redirect(url_for("races"))


@app.route("/race_results/<season>/<race>")
@login_required
def race_results(season, race):
    """View race results"""
    results = database.get_race_results(season, race)
    return render_template(
        "race_results.html",
        results=results,
        season=season,
        race=race,
        user=session.get("user"),
    )


@app.route("/add_club", methods=["POST"])
@login_required
def add_club():
    """Add new club"""
    club_name = request.form.get("club_name", "").strip()
    if club_name:
        try:
            database.add_club(club_name, [])
            flash(f"Club {club_name} added successfully")
        except Exception as e:
            flash(f"Error adding club: {str(e)}")
    return redirect(url_for("clubs"))


@app.route("/edit_club/<club_name>")
@login_required
def edit_club_get(club_name):
    """Edit club form"""
    club = database.get_club(club_name)
    if club:
        club_data = club.to_dict()
        club_data["name"] = club_name
        return render_template(
            "edit_club.html", club=club_data, user=session.get("user")
        )
    return redirect(url_for("clubs"))


@app.route("/edit_club/<club_name>", methods=["POST"])
@app.route("/update_club/<club_id>", methods=["POST"], endpoint="update_club")
@login_required
def edit_club_post(club_name=None, club_id=None):
    """Update club"""
    # Handle both parameter names
    club_name = club_name or club_id
    new_name = request.form.get("club_name", "").strip()
    if new_name:
        try:
            database.update_club(club_name, new_name, [])
            flash("Club updated successfully")
        except Exception as e:
            flash(f"Error updating club: {str(e)}")
    return redirect(url_for("clubs"))


@app.route("/delete_club/<club_name>", methods=["POST"])
@login_required
def delete_club(club_name):
    """Delete club"""
    try:
        database.delete_club(club_name)
        flash(f"Club {club_name} deleted successfully")
    except Exception as e:
        flash(f"Error deleting club: {str(e)}")
    return redirect(url_for("clubs"))


@app.route("/edit_participant/<participant_id>")
@login_required
def edit_participant_get(participant_id):
    """Edit participant form"""
    participant = database.get_participant(participant_id)
    clubs = database.get_clubs()
    if participant:
        return render_template(
            "edit_participant.html",
            participant=participant,
            clubs=clubs,
            user=session.get("user"),
        )
    return redirect(url_for("participants"))


@app.route("/edit_participant/<participant_id>", methods=["POST"])
@login_required
def edit_participant_post(participant_id):
    """Update participant"""
    first_name = request.form.get("first_name", "").strip()
    last_name = request.form.get("last_name", "").strip()
    gender = request.form.get("gender", "").strip()
    dob = request.form.get("dob", "").strip()
    barcode = request.form.get("barcode", "").strip()
    club = request.form.get("club", "").strip()

    if all([first_name, last_name, gender, dob, barcode, club]):
        try:
            database.update_participant(
                participant_id,
                {
                    "first_name": first_name,
                    "last_name": last_name,
                    "gender": gender,
                    "date_of_birth": dob,
                    "barcode": barcode,
                    "club": club,
                },
            )
            flash("Participant updated successfully")
        except Exception as e:
            flash(f"Error updating participant: {str(e)}")
    return redirect(url_for("participants"))


@app.route("/delete_participant/<participant_id>", methods=["POST"])
@login_required
def delete_participant(participant_id):
    """Delete participant"""
    try:
        database.delete_participant(participant_id)
        flash("Participant deleted successfully")
    except Exception as e:
        flash(f"Error deleting participant: {str(e)}")
    return redirect(url_for("participants"))


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

        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
        csv_input = csv.reader(stream)
        next(csv_input)

        clubs = database.get_clubs()
        participants = []

        for row in csv_input:
            if len(row) >= 6:
                participants.append(
                    {
                        "barcode": row[0],
                        "first_name": row[1],
                        "last_name": row[2],
                        "gender": row[3],
                        "date_of_birth": row[4],
                        "club": row[5],
                    }
                )

        database.process_participants_batch(participants, clubs)
        flash(f"Processed {len(participants)} participants")
    except Exception as e:
        flash(f"Error processing file: {str(e)}")

    return redirect(url_for("participants"))


@app.route("/process_upload_results", methods=["POST"])
@login_required
def process_upload_results():
    """Upload race results from CSV"""
    season_name = request.form.get("season_name", "").strip()
    race_name = request.form.get("race_name", "").strip()

    if not season_name or not race_name:
        flash("Season and race name are required")
        return redirect(url_for("races"))

    if "file" not in request.files:
        flash("No file selected")
        return redirect(url_for("races"))

    file = request.files["file"]
    if file.filename == "":
        flash("No file selected")
        return redirect(url_for("races"))

    try:
        import csv
        import io

        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
        csv_input = csv.reader(stream)
        next(csv_input)

        results = []
        for row in csv_input:
            if len(row) >= 2:
                participant = database.get_participant(row[0])
                if participant:
                    results.append(
                        {
                            "participant_id": row[0],
                            "finish_token": row[1],
                            "participant": participant,
                        }
                    )

        database.add_race_results_batch(season_name, race_name, results)
        flash(f"Processed {len(results)} results")
    except Exception as e:
        flash(f"Error processing results: {str(e)}")

    return redirect(url_for("races"))


@app.route("/add_manual_result", methods=["POST"])
@login_required
def add_manual_result():
    """Add manual race result"""
    season_name = request.form.get("season_name", "").strip()
    race_name = request.form.get("race_name", "").strip()
    barcode = request.form.get("barcode", "").strip()
    position_token = request.form.get("position_token", "").strip()

    if all([season_name, race_name, barcode, position_token]):
        try:
            participant = database.get_participant(barcode)
            if participant:
                database.add_race_result(
                    season_name, race_name, barcode, position_token, participant
                )
                flash("Result added successfully")
            else:
                flash("Participant not found")
        except Exception as e:
            flash(f"Error adding result: {str(e)}")

    return redirect(url_for("races"))


@app.route("/edit_season/<season_name>")
@login_required
def edit_season(season_name):
    """Edit season form"""
    season = database.get_season(season_name)
    if season:
        season["name"] = season_name
        return render_template(
            "edit_season.html", season=season, user=session.get("user")
        )
    return redirect(url_for("seasons"))


@app.route("/edit_season/<season_name>", methods=["POST"])
@login_required
def update_season(season_name):
    """Update season"""
    age_category_size = request.form.get("age_category_size", "5").strip()
    is_default = request.form.get("is_default") == "true"

    try:
        if is_default:
            database.clear_default_seasons()

        update_data = {
            "age_category_size": int(age_category_size),
            "is_default": is_default,
        }
        database.update_season(season_name, update_data)
        flash("Season updated successfully")
    except Exception as e:
        flash(f"Error updating season: {str(e)}")

    return redirect(url_for("seasons"))


@app.route("/delete_season/<season_name>", methods=["POST"])
@login_required
def delete_season(season_name):
    """Delete season"""
    try:
        database.delete_season(season_name)
        flash(f"Season {season_name} deleted successfully")
    except Exception as e:
        flash(f"Error deleting season: {str(e)}")
    return redirect(url_for("seasons"))


@app.route("/delete_all_race_results/<season_name>/<race_name>", methods=["POST"])
@login_required
def delete_all_race_results(season_name, race_name):
    """Delete all race results"""
    try:
        database.delete_all_race_results(season_name, race_name)
        flash("All race results deleted successfully")
    except Exception as e:
        flash(f"Error deleting results: {str(e)}")
    return redirect(url_for("race_results", season=season_name, race=race_name))


@app.route(
    "/delete_race_result/<season_name>/<race_name>/<finish_token>", methods=["POST"]
)
@login_required
def delete_race_result(season_name, race_name, finish_token):
    """Delete single race result"""
    try:
        database.delete_race_result(season_name, race_name, finish_token)
        flash("Race result deleted successfully")
    except Exception as e:
        flash(f"Error deleting result: {str(e)}")
    return redirect(url_for("race_results", season=season_name, race=race_name))


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


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
