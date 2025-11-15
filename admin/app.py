import os
import sys

# Add parent directory to path for shared modules
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "shared_libs"))

from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_compress import Compress
import database
from auth import init_oauth, login_required

app = Flask(__name__, template_folder="../app/templates", static_folder="../app/static")
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


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8081))
    app.run(host="0.0.0.0", port=port)
