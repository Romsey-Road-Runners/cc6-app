from flask import Blueprint, jsonify, request

import database
from auth import login_required

api = Blueprint("api", __name__)


@api.route("/clubs")
def get_clubs():
    """API endpoint to get running clubs"""
    return jsonify(database.get_clubs())


@api.route("/participants")
@login_required
def get_participants_api():
    """API endpoint to get participants"""
    return jsonify(database.get_participants())


@api.route("/seasons")
def get_seasons():
    """API endpoint to get seasons with IDs and default season"""
    seasons = database.get_seasons()
    default_season = database.get_default_season()
    default_race = None

    if default_season:
        races = database.get_races_by_season(default_season)
        if races:
            # Sort races by date (most recent first)
            races.sort(key=lambda x: x.get("date", ""), reverse=True)
            default_race = races[0]["name"]

    return jsonify(
        {
            "seasons": seasons,
            "default_season": default_season,
            "default_race": default_race,
        }
    )


@api.route("/seasons/<season_name>")
def get_season_with_races(season_name):
    """API endpoint to get season with nested races"""
    season = database.get_season(season_name)
    if not season:
        return jsonify({"error": "Season not found"}), 404

    races = database.get_races_by_season(season_name)
    return jsonify(
        {
            "name": season_name,
            "age_category_size": season.get("age_category_size", 5),
            "races": races,
        }
    )


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

    return jsonify(
        {
            "season": season_name,
            "name": race_name,
            "results": results,
        }
    )


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

        # Get all clubs that have ever participated
        all_clubs = set()
        for result in database.get_race_results(season_name, race["name"]):
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

    return jsonify(
        {
            "season": season_name,
            "gender": gender,
            "championship_type": "team",
            "championship_name": f"{gender} Team Championship",
            "races": races,
            "standings": standings,
        }
    )


@api.route("/individual-championship/<season_name>/<gender>")
def get_individual_championship_results(season_name, gender):
    """API endpoint to get individual championship standings"""
    season = database.get_season(season_name)
    category = request.args.get("category")

    races = database.get_races_by_season(season_name)
    if not races:
        return jsonify({"error": "No races found for season"}), 404

    participant_results = {}

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

        # Store individual positions
        for i, result in enumerate(gender_results):
            participant = result.get("participant", {})
            name = f"{participant.get('first_name', '')} {participant.get('last_name', '')}".strip()
            club = participant.get("club", "")

            if name and name != " ":
                if name not in participant_results:
                    participant_results[name] = {
                        "club": club,
                        "race_positions": {},
                        "total": 0,
                    }
                participant_results[name]["race_positions"][race["name"]] = i + 1

    # Calculate best results for each participant
    standings = []
    best_of = int(season.get("individual_results_best_of", 3)) if season else 3
    # Use minimum of best_of or available races
    actual_best_of = min(best_of, len(races))

    for name, data in participant_results.items():
        positions = list(data["race_positions"].values())
        if len(positions) >= actual_best_of:
            best_x = sorted(positions)[:actual_best_of]
            total = sum(best_x)
            standings.append(
                {
                    "name": name,
                    "club": data["club"],
                    "total_points": total,
                    "race_positions": data["race_positions"],
                }
            )

    standings.sort(key=lambda x: x["total_points"])

    championship_name = f"{gender} Individual Championship"
    if category:
        championship_name = f"{gender} {category} Individual Championship"

    return jsonify(
        {
            "season": season_name,
            "gender": gender,
            "category": category,
            "championship_type": "individual",
            "championship_name": championship_name,
            "races": races,
            "standings": standings,
            "best_of": actual_best_of,
        }
    )
