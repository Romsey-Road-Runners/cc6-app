from flask import Blueprint, jsonify, make_response, request

import database
from auth import login_required

api = Blueprint("api", __name__)


@api.route("/clubs")
def get_clubs():
    """API endpoint to get running clubs"""
    response = make_response(jsonify(database.get_clubs()))
    response.headers["Cache-Control"] = "public, max-age=3600"
    return response


@api.route("/participants")
@login_required
def get_participants_api():
    """API endpoint to get participants with pagination and search"""
    page = int(request.args.get("page", 1))
    page_size = int(request.args.get("page_size", 50))
    search = request.args.get("search")

    return jsonify(
        database.get_participants(page=page, page_size=page_size, search=search)
    )


@api.route("/participants/<participant_id>/results")
def get_participant_results(participant_id):
    """API endpoint to get all results for a participant"""
    results = database.get_participant_results(participant_id)
    response = make_response(jsonify(results))
    response.headers["Cache-Control"] = "public, max-age=3600"
    return response


@api.route("/seasons")
def get_seasons():
    """API endpoint to get seasons with IDs and default season"""
    seasons = database.get_seasons()
    default_season = database.get_default_season()
    default_race = None

    if default_season:
        races = database.get_races_by_season(default_season)
        if races:
            from datetime import datetime

            today = datetime.now().date()
            # Filter to only past/today races, then sort by date (most recent first)
            past_races = [
                r
                for r in races
                if datetime.strptime(r.get("date", "1900-01-01"), "%Y-%m-%d").date()
                <= today
            ]
            if past_races:
                past_races.sort(key=lambda x: x.get("date", ""), reverse=True)
                default_race = past_races[0]["name"]

    response = make_response(
        jsonify(
            {
                "seasons": seasons,
                "default_season": default_season,
                "default_race": default_race,
            }
        )
    )
    response.headers["Cache-Control"] = "public, max-age=3600"
    return response


@api.route("/seasons/<season_name>")
def get_season_with_races(season_name):
    """API endpoint to get season with nested races"""
    season = database.get_season(season_name)
    if not season:
        return jsonify({"error": "Season not found"}), 404

    races = database.get_races_by_season(season_name)
    response = make_response(
        jsonify(
            {
                "name": season_name,
                "age_category_size": season.get("age_category_size", 5),
                "races": races,
            }
        )
    )
    response.headers["Cache-Control"] = "public, max-age=3600"
    return response


@api.route("/races/<season_name>/<race_name>")
def get_race_with_results(season_name, race_name):
    """API endpoint to get race with nested results"""
    results = database.get_race_results(season_name, race_name)

    # Filter out results without participant data unless showMissingData is true
    show_missing = request.args.get("showMissingData", "false").lower() == "true"
    if not show_missing:
        results = [r for r in results if r.get("participant", {}).get("first_name")]

    # Filter by category if specified
    category = request.args.get("category")
    if category:
        results = [
            r
            for r in results
            if r.get("participant", {}).get("age_category") == category
        ]

    # Filter by gender if specified
    gender = request.args.get("gender")
    if gender:
        results = [
            r for r in results if r.get("participant", {}).get("gender") == gender
        ]

    response = make_response(
        jsonify(
            {
                "season": season_name,
                "name": race_name,
                "results": results,
            }
        )
    )

    # Cache for 1 hour (race results don't change often)
    response.headers["Cache-Control"] = "public, max-age=3600"
    return response


@api.route("/championship/<season_name>/<gender>")
def get_championship_results(season_name, gender):
    """API endpoint to get championship standings"""
    races = database.get_races_by_season(season_name)

    if not races:
        return jsonify({"error": "No races found for season"}), 404

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

    response = make_response(
        jsonify(
            {
                "season": season_name,
                "gender": gender,
                "championship_type": "team",
                "championship_name": f"{gender} Team Championship",
                "races": races,
                "standings": standings,
            }
        )
    )

    # Cache for 1 hour (championship calculations are expensive)
    response.headers["Cache-Control"] = "public, max-age=3600"
    return response


@api.route("/individual-championship/<season_name>/<gender>")
def get_individual_championship_results(season_name, gender):
    """API endpoint to get individual championship standings"""
    season = database.get_season(season_name)
    category = request.args.get("category")

    races = database.get_races_by_season(season_name)
    if not races:
        return jsonify({"error": "No races found for season"}), 404

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
                            "age_category": age_category,
                            "participant_id": participant.get("parkrun_barcode_id"),
                            "race_positions": {},
                            "total": 0,
                        }
                    participant_results[name]["race_positions"][race["name"]] = i + 1

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

    response = make_response(
        jsonify(
            {
                "season": season_name,
                "gender": gender,
                "category": category,
                "championship_type": "individual",
                "championship_name": championship_name,
                "races": races_with_results,
                "standings": standings,
                "best_of": actual_best_of,
            }
        )
    )

    # Cache for 1 hour (championship calculations are expensive)
    response.headers["Cache-Control"] = "public, max-age=3600"
    return response
