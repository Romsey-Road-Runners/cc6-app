from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    jsonify,
    session,
)
from google.cloud import firestore
import os
from auth import init_oauth, login_required
from database import db, init_running_clubs, get_club_id_by_name, validate_barcode

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-key-change-this")

# Initialize OAuth
google = init_oauth(app)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/clubs")
def get_clubs():
    """API endpoint to get running clubs"""
    clubs = db.collection("running_clubs").get()
    club_list = [club.to_dict()["name"] for club in clubs]
    return jsonify(club_list)


@app.route("/register", methods=["POST"])
def register():
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
        return redirect(url_for("index"))

    if not last_name:
        flash("Last name is required")
        return redirect(url_for("index"))

    if not email:
        flash("Email is required")
        return redirect(url_for("index"))

    if not gender:
        flash("Gender is required")
        return redirect(url_for("index"))

    if not dob:
        flash("Date of birth is required")
        return redirect(url_for("index"))

    if not validate_barcode(barcode):
        flash("Invalid barcode format (should be A followed by 6-7 digits)")
        return redirect(url_for("index"))

    club_id = get_club_id_by_name(club)
    if not club_id:
        flash("Please select a valid running club")
        return redirect(url_for("index"))

    # Check if barcode already exists
    existing = db.collection("participants").where("barcode", "==", barcode).get()
    if existing:
        flash("This barcode is already registered")
        return redirect(url_for("index"))

    # Save to Firestore
    try:
        db.collection("participants").add(
            {
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "gender": gender,
                "date_of_birth": dob,
                "barcode": barcode,
                "club_id": club_id,
                "registered_at": firestore.SERVER_TIMESTAMP,
            }
        )
        flash("Registration successful!")
    except Exception as e:
        flash("Registration failed. Please try again.")

    return redirect(url_for("index"))


@app.route("/login")
def login():
    redirect_uri = url_for("auth_callback", _external=True)
    return google.authorize_redirect(redirect_uri)


@app.route("/auth/callback")
def auth_callback():
    token = google.authorize_access_token()
    user = token.get("userinfo")
    if user and user.get("email") == "weston.sam@gmail.com":
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
    participants = (
        db.collection("participants")
        .order_by("registered_at", direction=firestore.Query.DESCENDING)
        .get()
    )
    return render_template(
        "participants.html", participants=participants, user=session.get("user")
    )


@app.route("/clubs")
@login_required
def clubs():
    """View all running clubs"""
    clubs = db.collection("running_clubs").order_by("name").get()
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
    existing = db.collection("running_clubs").where("name", "==", club_name).get()
    if existing:
        flash("Club already exists")
        return redirect(url_for("clubs"))

    # Add new club
    try:
        db.collection("running_clubs").add({"name": club_name})
        flash("Club added successfully!")
    except Exception as e:
        flash("Failed to add club. Please try again.")

    return redirect(url_for("clubs"))


if __name__ == "__main__":
    init_running_clubs()
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
