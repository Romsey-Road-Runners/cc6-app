from flask import Blueprint, request
from flask_cors import CORS
from flask_restx import Api, Resource, fields

import database
from auth import login_required

api_bp = Blueprint("api", __name__)
api = Api(
    api_bp,
    doc="/",
    title="CC6 Race Series API",
    version="1.0",
    description="Public API for race and championship results",
    spec_path="/openapi.json",
    default="CC6 API",
    default_label="CC6 Race Series Endpoints",
)

# Enable CORS for public APIs with subdomain wildcard
CORS(
    api_bp,
    origins=[
        "https://*.cc6.co.uk",
        "https://*.rr10.org.uk",
        "http://localhost:*",  # For development
        "https://localhost:*",  # For HTTPS development
    ],
)

# Define models for documentation
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

race_result_model = api.model(
    "RaceResult",
    {
        "finish_token": fields.String(description="Finish position token"),
        "participant": fields.Nested(participant_model),
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


@api.route("/clubs")
class ClubList(Resource):
    @api.doc("get_clubs")
    @api.marshal_list_with(club_model)
    def get(self):
        """Get all running clubs"""
        return database.get_clubs()


@api.route("/participants")
class ParticipantList(Resource):
    @api.doc("get_participants", doc=False)
    @api.param("page", "Page number", type="integer", default=1)
    @api.param("page_size", "Page size", type="integer", default=50)
    @api.param("search", "Search term", type="string")
    @login_required
    def get(self):
        """Get participants with pagination and search (requires authentication)"""
        page = int(request.args.get("page", 1))
        page_size = int(request.args.get("page_size", 50))
        search = request.args.get("search")
        return database.get_participants(page=page, page_size=page_size, search=search)


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
    @api.doc(
        "get_race_results",
        description="Get race results. Use /seasons endpoint to get available season names, then /seasons/{season_name} to get race names.",
    )
    @api.param(
        "season_name", "Season name (get available seasons from /seasons endpoint)"
    )
    @api.param(
        "race_name",
        "Race name (get available races from /seasons/{season_name} endpoint)",
    )
    @api.param("gender", "Gender filter", type="string")
    @api.param("category", "Age category filter", type="string")
    @api.param("showMissingData", "Show results with missing data", type="boolean")
    def get(self, season_name, race_name):
        """Get race results with optional filters"""
        results = database.get_race_results(season_name, race_name)

        show_missing = request.args.get("showMissingData", "false").lower() == "true"
        if not show_missing:
            results = [r for r in results if r.get("participant", {}).get("first_name")]

        category = request.args.get("category")
        if category:
            results = [
                r
                for r in results
                if r.get("participant", {}).get("age_category") == category
            ]

        gender = request.args.get("gender")
        if gender:
            results = [
                r for r in results if r.get("participant", {}).get("gender") == gender
            ]

        return {
            "season": season_name,
            "name": race_name,
            "results": results,
        }


@api.route("/seasons/<season_name>/championship/team")
class TeamChampionship(Resource):
    @api.doc(
        "get_team_championship",
        description="Get team championship standings. Use /seasons endpoint to get available season names.",
    )
    @api.param(
        "season_name", "Season name (get available seasons from /seasons endpoint)"
    )
    @api.param(
        "gender",
        "Gender (required)",
        type="string",
        required=True,
        enum=["Male", "Female"],
    )
    @api.marshal_with(championship_model)
    def get(self, season_name):
        """Get team championship standings"""
        gender = request.args.get("gender")

        if not gender:
            api.abort(400, "Gender parameter is required")

        races = database.get_races_by_season(season_name)

        if not races:
            api.abort(404, "No races found for season")

        club_points = {}

        for race in races:
            results = database.get_race_results(season_name, race["name"])
            # Filter by gender and valid participants
            gender_results = [
                r
                for r in results
                if r.get("participant", {}).get("gender") == gender
                and r.get("participant", {}).get("first_name")
            ]

            # Group by club and calculate points
            club_finishers = {}
            for i, result in enumerate(gender_results):
                club = result.get("participant", {}).get("club")
                if club:
                    if club not in club_finishers:
                        club_finishers[club] = []
                    club_finishers[club].append(i + 1)  # position (1-based)

            # First, add organizing clubs to club_points if they're not already there
            organising_clubs = race.get("organising_clubs", [])
            for org_club in organising_clubs:
                if org_club not in club_points:
                    club_points[org_club] = {
                        "total_points": 0,
                        "total_positions": 0,
                        "race_points": {},
                    }
                club_points[org_club]["race_points"][race["name"]] = "ORG"

            # Get all clubs that have ever participated (reuse results from above)
            all_clubs = set()
            for result in results:
                club = result.get("participant", {}).get("club")
                if club:
                    all_clubs.add(club)

            # Calculate points for each club (top 4 men, top 3 women)
            top_count = 4 if gender == "Male" else 3

            # Mark all clubs as DQ for this race initially
            for club in all_clubs:
                if club not in club_points:
                    club_points[club] = {
                        "total_points": 0,
                        "total_positions": 0,
                        "race_points": {},
                    }
                if club not in organising_clubs:
                    club_points[club]["race_points"][race["name"]] = "DQ"

            # Award points only to clubs with sufficient runners
            for club, positions in club_finishers.items():
                if club not in organising_clubs:
                    if len(positions) >= top_count:
                        top_positions = sorted(positions)[:top_count]
                        race_points = sum(top_positions)

                        club_points[club]["race_points"][race["name"]] = {
                            "points": race_points,
                            "positions": top_positions,
                        }
                        club_points[club]["total_points"] += race_points
                        club_points[club]["total_positions"] += race_points

        # Calculate club rankings for each race
        for race in races:
            race_clubs = []
            for club, data in club_points.items():
                race_data = data["race_points"].get(race["name"])
                if race_data and isinstance(race_data, dict) and "points" in race_data:
                    race_clubs.append((club, race_data["points"]))

            # Sort by points (lower is better) and assign rankings with ties
            race_clubs.sort(key=lambda x: x[1])
            current_rank = 1
            for i, (club, points) in enumerate(race_clubs):
                if i > 0 and points != race_clubs[i - 1][1]:
                    current_rank = i + 1
                race_data = club_points[club]["race_points"][race["name"]]
                race_data["rank"] = current_rank

        # Calculate total rankings and separate qualified/disqualified clubs
        qualified_clubs = []
        disqualified_clubs = []

        for club, data in club_points.items():
            # Check if club has DQ in any race (disqualified)
            has_dq = any(v == "DQ" for v in data["race_points"].values())
            # Check if club has points or is organizing
            has_activity = data["total_positions"] > 0 or any(
                v == "ORG" for v in data["race_points"].values()
            )

            if has_activity:
                # Calculate total rankings
                total_rankings = 0
                organized_races = 0
                for race_data in data["race_points"].values():
                    if isinstance(race_data, dict) and "rank" in race_data:
                        total_rankings += race_data["rank"]
                    elif race_data == "ORG":
                        organized_races += 1

                # Apply adjustment for clubs that didn't organize a race
                if organized_races == 0 and total_rankings > 0 and len(races) > 1:
                    total_races = len(races)
                    total_rankings = total_rankings * ((total_races - 1) / total_races)

                club_data = {
                    "name": club,
                    "total_points": "DQ" if has_dq else round(total_rankings, 2),
                    "race_points": data["race_points"],
                }
                if has_dq:
                    disqualified_clubs.append(club_data)
                else:
                    qualified_clubs.append(club_data)

        qualified_clubs.sort(key=lambda x: x["total_points"])
        disqualified_clubs.sort(key=lambda x: x["name"])

        standings = qualified_clubs + disqualified_clubs

        return {
            "season": season_name,
            "gender": gender,
            "championship_type": "team",
            "championship_name": f"{gender} Team Championship",
            "races": races,
            "standings": standings,
        }


@api.route("/seasons/<season_name>/championship/individual")
class IndividualChampionship(Resource):
    @api.doc(
        "get_individual_championship",
        description="Get individual championship standings. Use /seasons endpoint to get available season names.",
    )
    @api.param(
        "season_name", "Season name (get available seasons from /seasons endpoint)"
    )
    @api.param(
        "gender",
        "Gender (required)",
        type="string",
        required=True,
        enum=["Male", "Female"],
    )
    @api.param("category", "Age category filter", type="string")
    @api.marshal_with(championship_model)
    def get(self, season_name):
        """Get individual championship standings"""
        season = database.get_season(season_name)
        gender = request.args.get("gender")
        category = request.args.get("category")

        if not gender:
            api.abort(400, "Gender parameter is required")

        races = database.get_races_by_season(season_name)
        if not races:
            api.abort(404, "No races found for season")

        participant_results = {}
        races_with_results = []

        for race in races:
            results = database.get_race_results(season_name, race["name"])
            # Filter by gender and valid participants
            gender_results = [
                r
                for r in results
                if r.get("participant", {}).get("gender") == gender
                and r.get("participant", {}).get("first_name")
            ]

            # Filter by category if specified
            if category:
                gender_results = [
                    r
                    for r in gender_results
                    if r.get("participant", {}).get("age_category") == category
                ]

            # Only process races that have results
            if gender_results:
                races_with_results.append(race)

                # Store individual positions
                for i, result in enumerate(gender_results):
                    participant = result.get("participant", {})
                    name = f"{participant.get('first_name', '')} {participant.get('last_name', '')}".strip()
                    club = participant.get("club", "")
                    age_category = participant.get("age_category", "")

                    if name and name != " ":
                        if name not in participant_results:
                            participant_results[name] = {
                                "club": club,
                                "gender": participant.get("gender"),
                                "age_category": age_category,
                                "participant_id": participant.get("parkrun_barcode_id"),
                                "race_positions": {},
                                "total": 0,
                            }
                        participant_results[name]["race_positions"][race["name"]] = (
                            i + 1
                        )

        # Calculate best results for each participant
        standings = []
        best_of = int(season.get("individual_results_best_of", 3)) if season else 3
        # Use minimum of best_of or races with actual results
        actual_best_of = min(best_of, len(races_with_results))

        for name, data in participant_results.items():
            positions = list(data["race_positions"].values())
            if len(positions) >= actual_best_of:
                best_x = sorted(positions)[:actual_best_of]
                total = sum(best_x)
                standings.append(
                    {
                        "name": name,
                        "club": data["club"],
                        "gender": data["gender"],
                        "age_category": data["age_category"],
                        "participant_id": data.get("participant_id"),
                        "total_points": total,
                        "race_positions": data["race_positions"],
                    }
                )

        standings.sort(key=lambda x: x["total_points"])

        championship_name = f"{gender} Individual Championship"
        if category:
            championship_name = f"{gender} {category} Individual Championship"

        return {
            "season": season_name,
            "category": category,
            "championship_type": "individual",
            "championship_name": championship_name,
            "races": races_with_results,
            "standings": standings,
            "best_of": actual_best_of,
        }
