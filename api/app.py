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
from authlib.integrations.flask_client import OAuth
import re
import os
from functools import wraps

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-key-change-this")

# Initialize Firestore
db = firestore.Client()

# Initialize OAuth
oauth = OAuth(app)
google = oauth.register(
    name="google",
    client_id=os.environ.get("GOOGLE_CLIENT_ID"),
    client_secret=os.environ.get("GOOGLE_CLIENT_SECRET"),
    authorize_url="https://accounts.google.com/o/oauth2/auth",
    access_token_url="https://oauth2.googleapis.com/token",
    userinfo_endpoint="https://openidconnect.googleapis.com/v1/userinfo",
    jwks_uri="https://www.googleapis.com/oauth2/v3/certs",
    client_kwargs={"scope": "openid email profile"},
)


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)

    return decorated_function


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
    clubs = db.collection("running_clubs").where("name", "==", club_name).get()
    return clubs[0].id if clubs else None


def validate_barcode(barcode):
    """Validate Parkrun barcode format (A followed by 6-7 digits)"""
    return re.match(r"^A\d{6,7}$", barcode.upper()) is not None


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
