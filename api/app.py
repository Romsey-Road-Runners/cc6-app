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
    title="CC6 and RR10 Race Series API",
    version="1.0",
    description="Public API for race and championship results",
    specs_url="/openapi.json",
    default="Race Series API",
    default_label="Race Series Endpoints",
)

# Enable CORS
CORS(
    app,
    origins=[
        "https://*.cc6.co.uk",
        "https://*.rr10.org.uk",
        "https://*.running.cafe",
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


@api.route("/seasons/<season_name>/races/<race_name>")
class RaceResults(Resource):
    @api.doc("get_race_results")
    @api.param("season_name", "Season name")
    @api.param("race_name", "Race name")
    @api.param("gender", "Filter by gender (Male/Female)", _in="query")
    @api.param("category", "Filter by age category", _in="query")
    @api.param("showMissingData", "Show results with missing data", _in="query")
    def get(self, season_name, race_name):
        """Get race results with optional filters"""
        from flask import request

        results = database.get_race_results(season_name, race_name)

        # Apply filters
        gender_filter = request.args.get("gender")
        category_filter = request.args.get("category")
        show_missing = request.args.get("showMissingData", "false").lower() == "true"

        filtered_results = []
        for result in results:
            participant = result.get("participant", {})

            # Skip results with missing data unless explicitly requested
            if not show_missing and not participant.get("first_name"):
                continue

            # Apply gender filter
            if gender_filter and participant.get("gender") != gender_filter:
                continue

            # Apply category filter
            if category_filter and participant.get("age_category") != category_filter:
                continue

            filtered_results.append(result)

        return {"name": race_name, "season": season_name, "results": filtered_results}


@api.route("/seasons/<season_name>/championship/team")
class TeamChampionship(Resource):
    @api.doc("get_team_championship")
    @api.param("season_name", "Season name")
    @api.param("gender", "Gender (Male/Female) - required", _in="query", required=True)
    @api.marshal_with(championship_model)
    def get(self, season_name):
        """Get team championship standings"""
        from flask import request

        gender = request.args.get("gender")
        if not gender:
            api.abort(400, "Gender parameter is required")

        races = database.get_races_by_season(season_name)
        if not races:
            api.abort(404, "No races found for season")

        # Championship calculation logic (simplified)
        all_clubs = {}

        for race in races:
            race_name = race["name"]
            organising_clubs = race.get("organising_clubs", [])
            results = database.get_race_results(season_name, race_name)

            # Filter by gender
            gender_results = [
                r for r in results if r.get("participant", {}).get("gender") == gender
            ]

            # Group by club
            club_participants = {}
            for result in gender_results:
                club = result.get("participant", {}).get("club")
                if club:
                    if club not in club_participants:
                        club_participants[club] = []
                    club_participants[club].append(result)

            # Calculate points for each club
            for club, participants in club_participants.items():
                if club not in all_clubs:
                    all_clubs[club] = {
                        "name": club,
                        "race_points": {},
                        "total_points": 0,
                    }

                if club in organising_clubs:
                    all_clubs[club]["race_points"][race_name] = "ORG"
                elif len(participants) >= 4:  # Sufficient runners
                    # Simplified scoring - just count participants
                    all_clubs[club]["race_points"][race_name] = len(participants)
                    all_clubs[club]["total_points"] += len(participants)
                else:
                    all_clubs[club]["race_points"][race_name] = "DQ"

        # Add organizing clubs that didn't have participants
        for race in races:
            for org_club in race.get("organising_clubs", []):
                if org_club not in all_clubs:
                    all_clubs[org_club] = {
                        "name": org_club,
                        "race_points": {},
                        "total_points": 0,
                    }
                if org_club in all_clubs:
                    all_clubs[org_club]["race_points"][race["name"]] = "ORG"

        # Apply organizing race adjustment
        for club_data in all_clubs.values():
            org_races = sum(
                1 for points in club_data["race_points"].values() if points == "ORG"
            )
            total_races = len(races)
            if org_races > 0 and club_data["total_points"] > 0:
                adjustment = (
                    total_races / (total_races - org_races)
                    if total_races > org_races
                    else 1
                )
                club_data["total_points"] = club_data["total_points"] * adjustment

        standings = list(all_clubs.values())
        standings.sort(
            key=lambda x: (
                x["total_points"] if isinstance(x["total_points"], (int, float)) else 0
            ),
            reverse=True,
        )

        return {
            "season": season_name,
            "gender": gender,
            "championship_type": "team",
            "championship_name": f"{season_name} Team Championship ({gender})",
            "races": races,
            "standings": standings,
        }


@api.route("/seasons/<season_name>/championship/individual")
class IndividualChampionship(Resource):
    @api.doc("get_individual_championship")
    @api.param("season_name", "Season name")
    @api.param("gender", "Gender (Male/Female) - required", _in="query", required=True)
    @api.marshal_with(championship_model)
    def get(self, season_name):
        """Get individual championship standings"""
        from flask import request

        gender = request.args.get("gender")
        if not gender:
            api.abort(400, "Gender parameter is required")

        races = database.get_races_by_season(season_name)
        if not races:
            api.abort(404, "No races found for season")

        season_data = database.get_season(season_name)
        best_of = season_data.get("individual_results_best_of", 3) if season_data else 3

        # Individual championship calculation (simplified)
        all_participants = {}

        for race in races:
            race_name = race["name"]
            results = database.get_race_results(season_name, race_name)

            # Filter by gender and valid names
            gender_results = [
                r
                for r in results
                if (
                    r.get("participant", {}).get("gender") == gender
                    and r.get("participant", {}).get("first_name")
                    and r.get("participant", {}).get("last_name")
                )
            ]

            for i, result in enumerate(gender_results, 1):
                participant = result.get("participant", {})
                name = f"{participant.get('first_name', '')} {participant.get('last_name', '')}".strip()

                if name not in all_participants:
                    all_participants[name] = {
                        "name": name,
                        "club": participant.get("club", ""),
                        "race_points": {},
                        "total_points": 0,
                    }

                all_participants[name]["race_points"][
                    race_name
                ] = i  # Position as points

        # Filter participants with sufficient races
        qualified_participants = {
            name: data
            for name, data in all_participants.items()
            if len(data["race_points"]) >= best_of
        }

        # Calculate total points (best N races)
        for participant_data in qualified_participants.values():
            race_scores = list(participant_data["race_points"].values())
            race_scores.sort()  # Lower is better (position)
            participant_data["total_points"] = sum(race_scores[:best_of])

        standings = list(qualified_participants.values())
        standings.sort(key=lambda x: x["total_points"])

        return {
            "season": season_name,
            "gender": gender,
            "championship_type": "individual",
            "championship_name": f"{season_name} Individual Championship ({gender})",
            "races": races,
            "standings": standings,
        }


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
