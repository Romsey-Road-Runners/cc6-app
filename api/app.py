import os

from flask import (
    Flask,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

import database
from auth import init_oauth, login_required

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-key-change-this")

# Initialize OAuth
google = init_oauth(app)

# Initialize running clubs and admin emails on app startup
database.init_running_clubs()
database.init_admin_emails()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/robots.txt")
def robots_txt():
    return app.send_static_file("robots.txt")


@app.route("/api/clubs")
def get_clubs():
    """API endpoint to get running clubs"""
    return jsonify(database.get_all_clubs())


@app.route("/register", methods=["POST"])
@app.route("/edit_participant/<participant_id>", methods=["POST"])
def register(participant_id=None):
    # Require authentication for edits
    if participant_id and "user" not in session:
        return redirect(url_for("login"))

    first_name = request.form.get("first_name", "").strip()
    last_name = request.form.get("last_name", "").strip()
    email = request.form.get("email", "").strip()
    gender = request.form.get("gender", "")
    dob = request.form.get("dob", "")
    barcode = request.form.get("barcode", "").strip().upper()
    club = request.form.get("club", "")

    # Validation
    if not first_name:
        flash("First name is required")
        return redirect(url_for("participants" if participant_id else "index"))

    if not last_name:
        flash("Last name is required")
        return redirect(url_for("participants" if participant_id else "index"))

    if not email:
        flash("Email is required")
        return redirect(url_for("participants" if participant_id else "index"))

    if not gender:
        flash("Gender is required")
        return redirect(url_for("participants" if participant_id else "index"))

    if not dob:
        flash("Date of birth is required")
        return redirect(url_for("participants" if participant_id else "index"))

    if not database.validate_barcode(barcode):
        flash("Invalid barcode format (should be A followed by 6-7 digits)")
        return redirect(url_for("participants" if participant_id else "index"))

    # Validate club exists
    if not database.club_exists(club):
        flash("Please select a valid running club")
        return redirect(url_for("participants" if participant_id else "index"))

    # Check if barcode already exists
    if database.barcode_exists(barcode, participant_id):
        flash("This barcode is already registered")
        return redirect(url_for("participants" if participant_id else "index"))

    # Save or update Firestore
    try:
        data = {
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "gender": gender,
            "date_of_birth": dob,
            "barcode": barcode,
            "club": club,
        }

        if participant_id:
            database.update_participant(participant_id, data)
            flash("Participant updated successfully!")
        else:
            database.create_participant(data)
            flash("Registration successful!")
    except Exception:
        flash("Operation failed. Please try again.")

    return redirect(url_for("participants" if participant_id else "index"))


@app.route("/login")
def login():
    redirect_uri = url_for("auth_callback", _external=True)
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
        return redirect(url_for("index"))


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


@app.route("/clubs")
@login_required
def clubs():
    """View all running clubs"""
    clubs = database.get_all_clubs()
    return render_template("clubs.html", clubs=clubs, user=session.get("user"))


@app.route("/add_club", methods=["POST"])
@login_required
def add_club():
    """Add a new running club"""
    club_name = request.form.get("club_name", "").strip()

    if not club_name:
        flash("Club name is required")
        return redirect(url_for("clubs"))

    # Check if club already exists
    if database.club_exists(club_name):
        flash("Club already exists")
        return redirect(url_for("clubs"))

    # Add new club
    try:
        database.add_club(club_name)
        flash("Club added successfully!")
    except Exception:
        flash("Failed to add club. Please try again.")

    return redirect(url_for("clubs"))


@app.route("/edit_participant/<participant_id>", methods=["GET"])
@login_required
def edit_participant(participant_id):
    """Show edit participant form"""
    participant = database.get_participant(participant_id)
    clubs = database.get_all_clubs()
    return render_template(
        "edit_participant.html",
        participant=participant,
        clubs=clubs,
        user=session.get("user"),
    )


@app.route("/delete_participant/<participant_id>", methods=["POST"])
@login_required
def delete_participant(participant_id):
    """Soft delete a participant"""
    try:
        database.soft_delete_participant(participant_id)
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


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
