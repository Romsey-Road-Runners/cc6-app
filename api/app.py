import os
import sys

# Add parent directory to path for shared modules
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "shared_libs"))

from flask import Flask
from flask_compress import Compress
from flask_cors import CORS
from flask_restx import Api, Resource, fields
import database

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-key-change-this")
Compress(app)

# Initialize data on startup
database.init_running_clubs()

# Create API
api = Api(
    app,
    doc="/",
    title="CC6 Race Series API",
    version="1.0",
    description="Public API for race and championship results",
    spec_path="/openapi.json",
    default="CC6 API",
    default_label="CC6 Race Series Endpoints",
)

# Enable CORS
CORS(
    app,
    origins=[
        "https://*.cc6.co.uk",
        "https://*.rr10.org.uk",
        "http://localhost:*",
        "https://localhost:*",
    ],
)

# Models
club_model = api.model(
    "Club",
    {
        "name": fields.String(required=True, description="Club name"),
        "short_names": fields.List(
            fields.String, description="Club short names/aliases"
        ),
    },
)

participant_model = api.model(
    "Participant",
    {
        "first_name": fields.String(description="First name"),
        "last_name": fields.String(description="Last name"),
        "gender": fields.String(description="Gender"),
        "age_category": fields.String(description="Age category"),
        "club": fields.String(description="Club name"),
        "parkrun_barcode_id": fields.String(description="Parkrun barcode ID"),
    },
)

race_model = api.model(
    "Race",
    {
        "name": fields.String(required=True, description="Race name"),
        "date": fields.String(required=True, description="Race date"),
        "organising_clubs": fields.List(fields.String, description="Organizing clubs"),
    },
)

season_model = api.model(
    "Season",
    {
        "name": fields.String(required=True, description="Season name"),
        "age_category_size": fields.Integer(description="Age category size"),
        "races": fields.List(fields.Nested(race_model)),
    },
)

championship_standing_model = api.model(
    "ChampionshipStanding",
    {
        "name": fields.String(required=True, description="Club or participant name"),
        "total_points": fields.Raw(description="Total points or DQ"),
        "race_points": fields.Raw(description="Points per race"),
    },
)

championship_model = api.model(
    "Championship",
    {
        "season": fields.String(required=True, description="Season name"),
        "gender": fields.String(description="Gender filter"),
        "championship_type": fields.String(
            required=True, description="Championship type"
        ),
        "championship_name": fields.String(
            required=True, description="Championship name"
        ),
        "races": fields.List(fields.Nested(race_model)),
        "standings": fields.List(fields.Nested(championship_standing_model)),
    },
)


# Endpoints
@api.route("/clubs")
class ClubList(Resource):
    @api.doc("get_clubs")
    @api.marshal_list_with(club_model)
    def get(self):
        """Get all running clubs"""
        return database.get_clubs()


@api.route("/participants/<participant_id>/results")
class ParticipantResults(Resource):
    @api.doc("get_participant_results")
    @api.param("participant_id", "Participant ID")
    def get(self, participant_id):
        """Get all results for a participant"""
        return database.get_participant_results(participant_id)


@api.route("/seasons")
class SeasonList(Resource):
    @api.doc("get_seasons")
    def get(self):
        """Get all seasons with default season and race"""
        seasons = database.get_seasons()
        default_season = database.get_default_season()
        default_race = None

        if default_season:
            races = database.get_races_by_season(default_season)
            if races:
                from datetime import datetime

                today = datetime.now().date()
                past_races = [
                    r
                    for r in races
                    if datetime.strptime(r.get("date", "1900-01-01"), "%Y-%m-%d").date()
                    <= today
                ]
                if past_races:
                    past_races.sort(key=lambda x: x.get("date", ""), reverse=True)
                    default_race = past_races[0]["name"]

        return {
            "seasons": seasons,
            "default_season": default_season,
            "default_race": default_race,
        }


@api.route("/seasons/<season_name>")
class Season(Resource):
    @api.doc(
        "get_season",
        description="Get season details. Use /seasons endpoint to get list of available season names.",
    )
    @api.param(
        "season_name", "Season name (get available seasons from /seasons endpoint)"
    )
    @api.marshal_with(season_model)
    def get(self, season_name):
        """Get season with nested races"""
        season = database.get_season(season_name)
        if not season:
            api.abort(404, "Season not found")

        races = database.get_races_by_season(season_name)
        return {
            "name": season_name,
            "age_category_size": season.get("age_category_size", 5),
            "races": races,
        }


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
