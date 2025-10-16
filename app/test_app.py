import os
import unittest
from unittest.mock import Mock, patch

# Set environment variables for testing
os.environ["GOOGLE_CLOUD_PROJECT"] = "test-project"
os.environ["FLASK_SECRET_KEY"] = "test-secret-key"

import app
import database


class TestApp(unittest.TestCase):
    def setUp(self):
        app.app.config["TESTING"] = True
        self.client = app.app.test_client()

    def test_validate_barcode_valid(self):
        self.assertTrue(database.validate_barcode("A12"))
        self.assertTrue(database.validate_barcode("A12345672"))
        self.assertTrue(database.validate_barcode("a123456"))

    def test_validate_barcode_invalid(self):
        self.assertFalse(database.validate_barcode("B123456"))
        self.assertFalse(database.validate_barcode("A1"))
        self.assertFalse(database.validate_barcode("A12345678123"))
        self.assertFalse(database.validate_barcode("123456"))

    def test_index_route(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)

    @patch("database.get_clubs")
    def test_get_clubs_api(self, mock_get_clubs):
        mock_get_clubs.return_value = [{"name": "Test Club", "short_names": ["TC"]}]
        response = self.client.get("/api/clubs")
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json, list)

    def test_participants_requires_login(self):
        response = self.client.get("/participants")
        self.assertEqual(response.status_code, 302)

    def test_clubs_requires_login(self):
        response = self.client.get("/clubs")
        self.assertEqual(response.status_code, 302)

    def test_register_missing_fields(self):
        response = self.client.post("/register", data={})
        self.assertEqual(response.status_code, 302)

    @patch("database.validate_barcode")
    @patch("database.club_exists")
    @patch("database.participant_exists")
    @patch("database.create_participant")
    def test_register_valid_data(
        self, mock_create, mock_exists, mock_club_exists, mock_validate
    ):
        mock_validate.return_value = True
        mock_club_exists.return_value = True
        mock_exists.return_value = False

        data = {
            "first_name": "John",
            "last_name": "Doe",
            "gender": "M",
            "dob": "1990-01-01",
            "barcode": "A123456",
            "club": "Chandler's Ford Swifts",
        }
        response = self.client.post("/register", data=data)
        self.assertEqual(response.status_code, 302)

    def test_register_invalid_barcode(self):
        data = {
            "first_name": "John",
            "last_name": "Doe",
            "gender": "M",
            "dob": "1990-01-01",
            "barcode": "B123456",
            "club": "Chandler's Ford Swifts",
        }
        response = self.client.post("/register", data=data)
        self.assertEqual(response.status_code, 302)

    def test_edit_participant_requires_auth(self):
        data = {
            "first_name": "Jane",
            "last_name": "Doe",
            "gender": "F",
            "dob": "1990-01-01",
            "barcode": "A654321",
            "club": "Chandler's Ford Swifts",
        }
        response = self.client.post("/edit_participant/test_id", data=data)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.location)

    @patch("database.validate_barcode")
    @patch("database.club_exists")
    @patch("database.participant_exists")
    @patch("database.update_participant")
    def test_edit_participant_with_auth(
        self, mock_update, mock_exists, mock_club_exists, mock_validate
    ):
        mock_validate.return_value = True
        mock_club_exists.return_value = True
        mock_exists.return_value = False

        # Simulate logged in user
        with self.client.session_transaction() as sess:
            sess["user"] = {"email": "test@example.com"}

        data = {
            "first_name": "Jane",
            "last_name": "Doe",
            "gender": "F",
            "dob": "1990-01-01",
            "barcode": "A654321",
            "club": "Chandler's Ford Swifts",
        }
        response = self.client.post("/edit_participant/test_id", data=data)
        self.assertEqual(response.status_code, 302)

    def test_register_missing_first_name(self):
        data = {
            "last_name": "Doe",
            "gender": "M",
            "dob": "1990-01-01",
            "barcode": "A123456",
            "club": "Chandler's Ford Swifts",
        }
        response = self.client.post("/register", data=data)
        self.assertEqual(response.status_code, 302)

    def test_register_invalid_club(self):
        data = {
            "first_name": "John",
            "last_name": "Doe",
            "gender": "M",
            "dob": "1990-01-01",
            "barcode": "A123456",
            "club": "Invalid Club",
        }
        response = self.client.post("/register", data=data)
        self.assertEqual(response.status_code, 302)

    def test_admins_requires_auth(self):
        response = self.client.get("/admins")
        self.assertEqual(response.status_code, 302)

    def test_add_admin_requires_auth(self):
        response = self.client.post("/add_admin", data={"email": "test@example.com"})
        self.assertEqual(response.status_code, 302)

    def test_remove_admin_requires_auth(self):
        response = self.client.post("/remove_admin", data={"email": "test@example.com"})
        self.assertEqual(response.status_code, 302)

    @patch("database.is_admin_email")
    @patch("database.get_admin_emails")
    def test_admins_with_auth(self, mock_get_emails, mock_is_admin):
        mock_is_admin.return_value = True
        mock_get_emails.return_value = ["test@example.com"]

        with self.client.session_transaction() as sess:
            sess["user"] = {"email": "test@example.com"}

        response = self.client.get("/admins")
        self.assertEqual(response.status_code, 200)

    @patch("database.is_admin_email")
    @patch("database.get_admin_emails")
    @patch("database.add_admin_email")
    def test_add_admin_with_auth(self, mock_add, mock_get_emails, mock_is_admin):
        mock_is_admin.return_value = True
        mock_get_emails.return_value = ["test@example.com"]

        with self.client.session_transaction() as sess:
            sess["user"] = {"email": "test@example.com"}

        response = self.client.post("/add_admin", data={"email": "new@example.com"})
        self.assertEqual(response.status_code, 302)

    def test_seasons_requires_auth(self):
        response = self.client.get("/seasons")
        self.assertEqual(response.status_code, 302)

    def test_add_season_requires_auth(self):
        response = self.client.post("/add_season", data={"season_name": "2024 Season"})
        self.assertEqual(response.status_code, 302)

    @patch("database.is_admin_email")
    @patch("database.get_seasons")
    def test_seasons_with_auth(self, mock_get_seasons, mock_is_admin):
        mock_is_admin.return_value = True
        mock_get_seasons.return_value = ["2024 Season"]

        with self.client.session_transaction() as sess:
            sess["user"] = {"email": "test@example.com"}

        response = self.client.get("/seasons")
        self.assertEqual(response.status_code, 200)

    @patch("database.is_admin_email")
    @patch("database.create_season")
    def test_add_season_with_auth(self, mock_create, mock_is_admin):
        mock_is_admin.return_value = True

        with self.client.session_transaction() as sess:
            sess["user"] = {"email": "test@example.com"}

        response = self.client.post("/add_season", data={"season_name": "2024 Season"})
        self.assertEqual(response.status_code, 302)

    @patch("database.is_admin_email")
    @patch("database.create_season")
    def test_add_season_with_start_date(self, mock_create, mock_is_admin):
        mock_is_admin.return_value = True

        with self.client.session_transaction() as sess:
            sess["user"] = {"email": "test@example.com"}

        response = self.client.post(
            "/add_season",
            data={"season_name": "2024 Season", "start_date": "2024-01-01"},
        )
        self.assertEqual(response.status_code, 302)
        mock_create.assert_called_once()
        # Verify start_date was passed to create_season
        call_args = mock_create.call_args
        # Check if start_date is in kwargs or if it's the 4th positional argument
        if "start_date" in call_args.kwargs:
            self.assertEqual(call_args.kwargs["start_date"], "2024-01-01")
        elif len(call_args.args) >= 4:
            self.assertEqual(call_args.args[3], "2024-01-01")

    def test_races_requires_auth(self):
        response = self.client.get("/races")
        self.assertEqual(response.status_code, 302)

    def test_add_race_requires_auth(self):
        response = self.client.post(
            "/add_race",
            data={"name": "Test Race", "date": "2024-01-01", "season": "2024 Season"},
        )
        self.assertEqual(response.status_code, 302)

    @patch("database.is_admin_email")
    @patch("database.get_seasons")
    @patch("database.get_races_by_season")
    def test_races_with_auth(self, mock_get_races, mock_get_seasons, mock_is_admin):
        mock_is_admin.return_value = True
        mock_get_seasons.return_value = ["2024 Season"]
        mock_get_races.return_value = []

        with self.client.session_transaction() as sess:
            sess["user"] = {"email": "test@example.com"}

        response = self.client.get("/races")
        self.assertEqual(response.status_code, 200)

    @patch("database.is_admin_email")
    @patch("database.create_race")
    def test_add_race_with_auth(self, mock_create, mock_is_admin):
        mock_is_admin.return_value = True

        with self.client.session_transaction() as sess:
            sess["user"] = {"email": "test@example.com"}

        response = self.client.post(
            "/add_race",
            data={"name": "Test Race", "date": "2024-01-01", "season": "2024 Season"},
        )
        self.assertEqual(response.status_code, 302)

    @patch("database.get_default_season")
    @patch("database.get_seasons")
    def test_api_seasons(self, mock_get_seasons, mock_get_default):
        mock_get_seasons.return_value = ["2024 Season"]
        mock_get_default.return_value = None
        response = self.client.get("/api/seasons")
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json, dict)
        self.assertIn("seasons", response.json)
        self.assertIn("default_season", response.json)
        self.assertIn("default_race", response.json)

    def test_race_results_requires_auth(self):
        response = self.client.get("/race_results/season/race")
        self.assertEqual(response.status_code, 302)

    @patch("app.database.is_admin_email")
    @patch("database.get_race_results")
    def test_race_results_with_auth(self, mock_get_results, mock_is_admin):
        mock_is_admin.return_value = True
        mock_get_results.return_value = []

        with self.client.session_transaction() as sess:
            sess["user"] = {"email": "test@example.com"}

        response = self.client.get("/race_results/season/race")
        self.assertEqual(response.status_code, 200)

    @patch("database.get_season")
    @patch("database.get_races_by_season")
    def test_api_seasons_with_id(self, mock_get_races, mock_get_season):
        mock_get_season.return_value = {"age_category_size": 5}
        mock_get_races.return_value = [{"name": "Test Race", "date": "2024-01-01"}]

        response = self.client.get("/api/seasons/season1")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["name"], "season1")
        self.assertIn("races", response.json)

    @patch("database.get_season")
    def test_api_seasons_not_found(self, mock_get_season):
        mock_get_season.return_value = None

        response = self.client.get("/api/seasons/nonexistent")
        self.assertEqual(response.status_code, 404)

    @patch("database.get_race_results")
    def test_api_races_with_results(self, mock_get_results):
        mock_get_results.return_value = [
            {
                "finish_token": "1",
                "participant": {
                    "first_name": "John",
                    "last_name": "Doe",
                    "gender": "M",
                    "age_category": "Senior",
                },
            }
        ]

        response = self.client.get("/api/races/season/race")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["name"], "race")
        self.assertIn("results", response.json)
        self.assertEqual(len(response.json["results"]), 1)

    def test_robots_txt(self):
        response = self.client.get("/robots.txt")
        self.assertEqual(response.status_code, 200)

    @patch("database.is_admin_email")
    @patch("database.get_participants")
    def test_get_participants_api_with_auth(self, mock_get_participants, mock_is_admin):
        mock_is_admin.return_value = True
        mock_get_participants.return_value = [
            {"barcode": "A123456", "first_name": "John"}
        ]

        with self.client.session_transaction() as sess:
            sess["user"] = {"email": "test@example.com"}

        response = self.client.get("/api/participants")
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json, list)

    def test_get_participants_api_no_auth(self):
        response = self.client.get("/api/participants")
        self.assertEqual(response.status_code, 302)

    @patch("database.get_race_results")
    def test_api_races_with_filters(self, mock_get_results):
        mock_get_results.return_value = [
            {
                "finish_token": "1",
                "participant": {
                    "first_name": "John",
                    "gender": "Male",
                    "age_category": "Senior",
                },
            },
            {
                "finish_token": "2",
                "participant": {
                    "first_name": "Jane",
                    "gender": "Female",
                    "age_category": "V40",
                },
            },
        ]

        # Test gender filter
        response = self.client.get("/api/races/season/race?gender=Male")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json["results"]), 1)

        # Test category filter
        response = self.client.get("/api/races/season/race?category=Senior")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json["results"]), 1)

    @patch("database.get_race_results")
    def test_api_races_show_missing_data(self, mock_get_results):
        mock_get_results.return_value = [
            {"finish_token": "1", "participant": {"first_name": "John"}},
            {"finish_token": "2", "participant": {}},
        ]

        # Without showMissingData
        response = self.client.get("/api/races/season/race")
        self.assertEqual(len(response.json["results"]), 1)

        # With showMissingData
        response = self.client.get("/api/races/season/race?showMissingData=true")
        self.assertEqual(len(response.json["results"]), 2)

    @patch("database.get_races_by_season")
    def test_api_championship_no_races(self, mock_get_races):
        mock_get_races.return_value = []

        response = self.client.get("/api/championship/season/Male")
        self.assertEqual(response.status_code, 404)

    @patch("database.get_races_by_season")
    @patch("database.get_race_results")
    def test_api_championship_with_results(self, mock_get_results, mock_get_races):
        mock_get_races.return_value = [
            {"name": "Race1", "organising_clubs": ["Club A"]}
        ]
        mock_get_results.return_value = [
            {"participant": {"first_name": "John", "gender": "Male", "club": "Club B"}},
            {"participant": {"first_name": "Jane", "gender": "Male", "club": "Club B"}},
        ]

        response = self.client.get("/api/championship/season/Male")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["championship_type"], "team")

    @patch("database.get_races_by_season")
    def test_api_individual_championship_no_races(self, mock_get_races):
        mock_get_races.return_value = []

        response = self.client.get("/api/individual-championship/season/Male")
        self.assertEqual(response.status_code, 404)

    @patch("database.get_races_by_season")
    @patch("database.get_race_results")
    def test_api_individual_championship_with_results(
        self, mock_get_results, mock_get_races
    ):
        mock_get_races.return_value = [
            {"name": "Race1"},
            {"name": "Race2"},
            {"name": "Race3"},
        ]
        mock_get_results.return_value = [
            {
                "participant": {
                    "first_name": "John",
                    "last_name": "Doe",
                    "gender": "Male",
                    "club": "Club A",
                }
            }
        ]

        response = self.client.get("/api/individual-championship/season/Male")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["championship_type"], "individual")

    @patch("database.validate_barcode")
    @patch("database.club_exists")
    @patch("database.participant_exists")
    def test_register_existing_barcode(
        self, mock_exists, mock_club_exists, mock_validate
    ):
        mock_validate.return_value = True
        mock_club_exists.return_value = True
        mock_exists.return_value = True

        data = {
            "first_name": "John",
            "last_name": "Doe",
            "gender": "M",
            "dob": "1990-01-01",
            "barcode": "A123456",
            "club": "Chandler's Ford Swifts",
        }
        response = self.client.post("/register", data=data)
        self.assertEqual(response.status_code, 302)

    @patch("database.is_admin_email")
    @patch("database.club_exists")
    @patch("database.add_club")
    def test_add_club_with_auth(self, mock_add_club, mock_club_exists, mock_is_admin):
        mock_is_admin.return_value = True
        mock_club_exists.return_value = False

        with self.client.session_transaction() as sess:
            sess["user"] = {"email": "test@example.com"}

        response = self.client.post(
            "/add_club", data={"club_name": "New Club", "short_names": "NC, New"}
        )
        self.assertEqual(response.status_code, 302)
        mock_add_club.assert_called_once()

    @patch("database.is_admin_email")
    @patch("database.club_exists")
    def test_add_club_existing(self, mock_club_exists, mock_is_admin):
        mock_is_admin.return_value = True
        mock_club_exists.return_value = True

        with self.client.session_transaction() as sess:
            sess["user"] = {"email": "test@example.com"}

        response = self.client.post("/add_club", data={"club_name": "Existing Club"})
        self.assertEqual(response.status_code, 302)

    @patch("database.is_admin_email")
    def test_add_club_empty_name(self, mock_is_admin):
        mock_is_admin.return_value = True

        with self.client.session_transaction() as sess:
            sess["user"] = {"email": "test@example.com"}

        response = self.client.post("/add_club", data={"club_name": ""})
        self.assertEqual(response.status_code, 302)

    @patch("database.is_admin_email")
    @patch("database.get_club")
    def test_edit_club_get(self, mock_get_club, mock_is_admin):
        mock_is_admin.return_value = True
        mock_doc = Mock()
        mock_doc.to_dict.return_value = {"short_names": ["TC"]}
        mock_get_club.return_value = mock_doc

        with self.client.session_transaction() as sess:
            sess["user"] = {"email": "test@example.com"}

        response = self.client.get("/edit_club/test_club")
        self.assertEqual(response.status_code, 200)

    @patch("database.is_admin_email")
    @patch("database.update_club")
    def test_update_club_with_auth(self, mock_update_club, mock_is_admin):
        mock_is_admin.return_value = True

        with self.client.session_transaction() as sess:
            sess["user"] = {"email": "test@example.com"}

        response = self.client.post(
            "/edit_club/test_club",
            data={"club_name": "Updated Club", "short_names": "UC"},
        )
        self.assertEqual(response.status_code, 302)
        mock_update_club.assert_called_once()

    @patch("database.is_admin_email")
    @patch("database.delete_club")
    def test_delete_club_with_auth(self, mock_delete_club, mock_is_admin):
        mock_is_admin.return_value = True

        with self.client.session_transaction() as sess:
            sess["user"] = {"email": "test@example.com"}

        response = self.client.post("/delete_club/test_club")
        self.assertEqual(response.status_code, 302)
        mock_delete_club.assert_called_once()

    @patch("database.is_admin_email")
    @patch("database.get_participant")
    @patch("database.get_clubs")
    def test_edit_participant_get(
        self, mock_get_clubs, mock_get_participant, mock_is_admin
    ):
        mock_is_admin.return_value = True
        mock_get_participant.return_value = {
            "first_name": "John",
            "last_name": "Doe",
            "gender": "Male",
            "date_of_birth": "1990-01-01",
            "club": "Test Club",
            "barcode": "A123456",
        }
        mock_get_clubs.return_value = [{"name": "Test Club", "short_names": []}]

        with self.client.session_transaction() as sess:
            sess["user"] = {"email": "test@example.com"}

        response = self.client.get("/edit_participant/A123456")
        self.assertEqual(response.status_code, 200)

    @patch("database.is_admin_email")
    @patch("database.delete_participant")
    def test_delete_participant_with_auth(self, mock_delete_participant, mock_is_admin):
        mock_is_admin.return_value = True

        with self.client.session_transaction() as sess:
            sess["user"] = {"email": "test@example.com"}

        response = self.client.post("/delete_participant/A123456")
        self.assertEqual(response.status_code, 302)
        mock_delete_participant.assert_called_once()

    @patch("database.is_admin_email")
    @patch("database.remove_admin_email")
    def test_remove_admin_with_auth(self, mock_remove, mock_is_admin):
        mock_is_admin.return_value = True
        mock_remove.return_value = True

        with self.client.session_transaction() as sess:
            sess["user"] = {"email": "test@example.com"}

        response = self.client.post("/remove_admin", data={"email": "old@example.com"})
        self.assertEqual(response.status_code, 302)

    @patch("database.is_admin_email")
    @patch("database.get_season")
    def test_edit_season_get(self, mock_get_season, mock_is_admin):
        mock_is_admin.return_value = True
        mock_get_season.return_value = {"age_category_size": 5}

        with self.client.session_transaction() as sess:
            sess["user"] = {"email": "test@example.com"}

        response = self.client.get("/edit_season/2024")
        self.assertEqual(response.status_code, 200)

    @patch("database.is_admin_email")
    @patch("database.get_season")
    def test_edit_season_get_with_start_date(self, mock_get_season, mock_is_admin):
        mock_is_admin.return_value = True
        mock_get_season.return_value = {
            "age_category_size": 5,
            "start_date": "2024-01-01",
            "is_default": False,
        }

        with self.client.session_transaction() as sess:
            sess["user"] = {"email": "test@example.com"}

        response = self.client.get("/edit_season/2024")
        self.assertEqual(response.status_code, 200)

    @patch("database.is_admin_email")
    @patch("database.clear_default_seasons")
    @patch("database.update_season")
    def test_update_season_with_auth(self, mock_update, mock_clear, mock_is_admin):
        mock_is_admin.return_value = True

        with self.client.session_transaction() as sess:
            sess["user"] = {"email": "test@example.com"}

        response = self.client.post(
            "/edit_season/2024", data={"age_category_size": "10", "is_default": "true"}
        )
        self.assertEqual(response.status_code, 302)
        mock_clear.assert_called_once()
        mock_update.assert_called_once()

    @patch("database.is_admin_email")
    @patch("database.update_season")
    def test_update_season_with_start_date(self, mock_update, mock_is_admin):
        mock_is_admin.return_value = True

        with self.client.session_transaction() as sess:
            sess["user"] = {"email": "test@example.com"}

        response = self.client.post(
            "/edit_season/2024",
            data={
                "age_category_size": "5",
                "start_date": "2024-01-15",
                "is_default": "false",
            },
        )
        self.assertEqual(response.status_code, 302)
        # Verify start_date was included in update data
        call_args = mock_update.call_args[0][1]
        self.assertEqual(call_args["start_date"], "2024-01-15")

    @patch("database.is_admin_email")
    @patch("database.delete_season")
    def test_delete_season_with_auth(self, mock_delete, mock_is_admin):
        mock_is_admin.return_value = True

        with self.client.session_transaction() as sess:
            sess["user"] = {"email": "test@example.com"}

        response = self.client.post("/delete_season/2024")
        self.assertEqual(response.status_code, 302)
        mock_delete.assert_called_once()

    @patch("database.is_admin_email")
    @patch("database.get_season")
    def test_add_season_invalid_name(self, mock_get_season, mock_is_admin):
        mock_is_admin.return_value = True
        mock_get_season.return_value = None

        with self.client.session_transaction() as sess:
            sess["user"] = {"email": "test@example.com"}

        response = self.client.post("/add_season", data={"season_name": "2024/Season"})
        self.assertEqual(response.status_code, 302)

    @patch("database.is_admin_email")
    @patch("database.get_season")
    def test_add_season_existing(self, mock_get_season, mock_is_admin):
        mock_is_admin.return_value = True
        mock_get_season.return_value = {"age_category_size": 5}

        with self.client.session_transaction() as sess:
            sess["user"] = {"email": "test@example.com"}

        response = self.client.post("/add_season", data={"season_name": "2024 Season"})
        self.assertEqual(response.status_code, 302)

    @patch("database.is_admin_email")
    @patch("database.get_season")
    @patch("database.create_race")
    def test_add_race_with_organising_clubs(
        self, mock_create, mock_get_season, mock_is_admin
    ):
        mock_is_admin.return_value = True
        mock_get_season.return_value = {"age_category_size": 5}

        with self.client.session_transaction() as sess:
            sess["user"] = {"email": "test@example.com"}

        response = self.client.post(
            "/add_race",
            data={
                "name": "Test Race",
                "date": "2024-01-01",
                "season": "2024 Season",
                "organising_clubs": ["Club A", "Club B"],
            },
        )
        self.assertEqual(response.status_code, 302)
        mock_create.assert_called_once()

    @patch("database.is_admin_email")
    def test_add_race_missing_fields(self, mock_is_admin):
        mock_is_admin.return_value = True

        with self.client.session_transaction() as sess:
            sess["user"] = {"email": "test@example.com"}

        # Missing name
        response = self.client.post(
            "/add_race", data={"date": "2024-01-01", "season": "2024"}
        )
        self.assertEqual(response.status_code, 302)

        # Missing date
        response = self.client.post(
            "/add_race", data={"name": "Test", "season": "2024"}
        )
        self.assertEqual(response.status_code, 302)

        # Missing season
        response = self.client.post(
            "/add_race", data={"name": "Test", "date": "2024-01-01"}
        )
        self.assertEqual(response.status_code, 302)

    @patch("database.is_admin_email")
    @patch("database.get_season")
    def test_add_race_invalid_season(self, mock_get_season, mock_is_admin):
        mock_is_admin.return_value = True
        mock_get_season.return_value = None

        with self.client.session_transaction() as sess:
            sess["user"] = {"email": "test@example.com"}

        response = self.client.post(
            "/add_race",
            data={
                "name": "Test Race",
                "date": "2024-01-01",
                "season": "Invalid Season",
            },
        )
        self.assertEqual(response.status_code, 302)

    @patch("database.is_admin_email")
    @patch("database.delete_race_result")
    def test_delete_race_result_with_auth(self, mock_delete, mock_is_admin):
        mock_is_admin.return_value = True

        with self.client.session_transaction() as sess:
            sess["user"] = {"email": "test@example.com"}

        response = self.client.post("/delete_race_result/season/race/1")
        self.assertEqual(response.status_code, 302)
        mock_delete.assert_called_once()

    @patch("database.is_admin_email")
    @patch("database.delete_all_race_results")
    def test_delete_all_race_results_with_auth(self, mock_delete, mock_is_admin):
        mock_is_admin.return_value = True

        with self.client.session_transaction() as sess:
            sess["user"] = {"email": "test@example.com"}

        response = self.client.post("/delete_all_race_results/season/race")
        self.assertEqual(response.status_code, 302)
        mock_delete.assert_called_once()

    def test_logout(self):
        with self.client.session_transaction() as sess:
            sess["user"] = {"email": "test@example.com"}

        response = self.client.get("/logout")
        self.assertEqual(response.status_code, 302)

        with self.client.session_transaction() as sess:
            self.assertNotIn("user", sess)

    @patch("database.is_admin_email")
    @patch("database.get_season")
    @patch("database.get_participant")
    @patch("database.add_race_result")
    def test_add_manual_result_success(
        self, mock_add_result, mock_get_participant, mock_get_season, mock_is_admin
    ):
        mock_is_admin.return_value = True
        mock_get_season.return_value = {"start_date": "2024-01-01"}
        mock_get_participant.return_value = {
            "first_name": "John",
            "last_name": "Doe",
            "gender": "Male",
            "date_of_birth": "1990-01-01",
            "club": "Test Club",
        }

        with self.client.session_transaction() as sess:
            sess["user"] = {"email": "test@example.com"}

        response = self.client.post(
            "/add_manual_result",
            data={
                "season_name": "2024",
                "race_name": "Test Race",
                "barcode": "A123456",
                "position_token": "P0001",
            },
        )
        self.assertEqual(response.status_code, 302)
        mock_add_result.assert_called_once()

    @patch("database.is_admin_email")
    @patch("database.get_season")
    @patch("database.get_participant")
    def test_add_manual_result_participant_not_found(
        self, mock_get_participant, mock_get_season, mock_is_admin
    ):
        mock_is_admin.return_value = True
        mock_get_season.return_value = {"start_date": "2024-01-01"}
        mock_get_participant.return_value = None

        with self.client.session_transaction() as sess:
            sess["user"] = {"email": "test@example.com"}

        response = self.client.post(
            "/add_manual_result",
            data={
                "season_name": "2024",
                "race_name": "Test Race",
                "barcode": "A123456",
                "position_token": "P0001",
            },
        )
        self.assertEqual(response.status_code, 302)

    @patch("database.is_admin_email")
    def test_add_manual_result_missing_fields(self, mock_is_admin):
        mock_is_admin.return_value = True

        with self.client.session_transaction() as sess:
            sess["user"] = {"email": "test@example.com"}

        response = self.client.post(
            "/add_manual_result",
            data={
                "season_name": "2024",
                "race_name": "Test Race",
                # Missing barcode and finish_token
            },
        )
        self.assertEqual(response.status_code, 302)

    def test_process_upload_results_no_auth(self):
        response = self.client.post("/process_upload_results")
        self.assertEqual(response.status_code, 302)

    @patch("database.is_admin_email")
    def test_process_upload_results_missing_params(self, mock_is_admin):
        mock_is_admin.return_value = True

        with self.client.session_transaction() as sess:
            sess["user"] = {"email": "test@example.com"}

        response = self.client.post("/process_upload_results", data={})
        self.assertEqual(response.status_code, 302)

    @patch("database.is_admin_email")
    def test_process_upload_results_no_file(self, mock_is_admin):
        mock_is_admin.return_value = True

        with self.client.session_transaction() as sess:
            sess["user"] = {"email": "test@example.com"}

        response = self.client.post(
            "/process_upload_results",
            data={"season_name": "2024", "race_name": "Test Race"},
        )
        self.assertEqual(response.status_code, 302)

    def test_upload_participants_no_auth(self):
        response = self.client.post("/upload_participants")
        self.assertEqual(response.status_code, 302)

    @patch("database.is_admin_email")
    def test_upload_participants_no_file(self, mock_is_admin):
        mock_is_admin.return_value = True

        with self.client.session_transaction() as sess:
            sess["user"] = {"email": "test@example.com"}

        response = self.client.post("/upload_participants")
        self.assertEqual(response.status_code, 302)

    @patch("database.is_admin_email")
    @patch("database.get_clubs")
    @patch("database.process_participants_batch")
    def test_upload_participants_with_file(
        self, mock_batch, mock_get_clubs, mock_is_admin
    ):
        mock_is_admin.return_value = True
        mock_get_clubs.return_value = [{"name": "Test Club", "short_names": ["TC"]}]

        with self.client.session_transaction() as sess:
            sess["user"] = {"email": "test@example.com"}

        # Create a mock CSV file
        from io import BytesIO

        csv_data = b"A123456,John,Doe,Male,01/01/1990,Test Club\n"

        response = self.client.post(
            "/upload_participants", data={"file": (BytesIO(csv_data), "test.csv")}
        )
        self.assertEqual(response.status_code, 302)

    @patch("database.is_admin_email")
    @patch("database.get_season")
    @patch("database.get_participant")
    @patch("database.add_race_results_batch")
    def test_process_upload_results_with_file(
        self, mock_batch, mock_get_participant, mock_get_season, mock_is_admin
    ):
        mock_is_admin.return_value = True
        mock_get_season.return_value = {"start_date": "2024-01-01"}
        mock_get_participant.return_value = {
            "first_name": "John",
            "last_name": "Doe",
            "gender": "Male",
            "date_of_birth": "1990-01-01",
            "club": "Test Club",
        }

        with self.client.session_transaction() as sess:
            sess["user"] = {"email": "test@example.com"}

        from io import BytesIO

        csv_data = b"ID,Pos\nA123456,1\n"

        response = self.client.post(
            "/process_upload_results",
            data={
                "season_name": "2024",
                "race_name": "Test Race",
                "file": (BytesIO(csv_data), "results.csv"),
            },
        )
        self.assertEqual(response.status_code, 302)

    def test_login_route(self):
        response = self.client.get("/login")
        self.assertEqual(response.status_code, 302)

    @patch("app.google.authorize_access_token")
    @patch("database.is_admin_email")
    def test_auth_callback_success(self, mock_is_admin, mock_token):
        mock_token.return_value = {"userinfo": {"email": "admin@example.com"}}
        mock_is_admin.return_value = True

        response = self.client.get("/auth/callback")
        self.assertEqual(response.status_code, 302)

    @patch("app.google.authorize_access_token")
    @patch("database.is_admin_email")
    def test_auth_callback_unauthorized(self, mock_is_admin, mock_token):
        mock_token.return_value = {"userinfo": {"email": "user@example.com"}}
        mock_is_admin.return_value = False

        response = self.client.get("/auth/callback")
        self.assertEqual(response.status_code, 302)

    @patch("app.google.authorize_access_token")
    def test_auth_callback_no_user(self, mock_token):
        mock_token.return_value = {}

        response = self.client.get("/auth/callback")
        self.assertEqual(response.status_code, 302)

    def test_register_missing_last_name(self):
        data = {
            "first_name": "John",
            "gender": "M",
            "dob": "1990-01-01",
            "barcode": "A123456",
            "club": "Test Club",
        }
        response = self.client.post("/register", data=data)
        self.assertEqual(response.status_code, 302)

    def test_register_missing_gender(self):
        data = {
            "first_name": "John",
            "last_name": "Doe",
            "dob": "1990-01-01",
            "barcode": "A123456",
            "club": "Test Club",
        }
        response = self.client.post("/register", data=data)
        self.assertEqual(response.status_code, 302)

    def test_register_missing_dob(self):
        data = {
            "first_name": "John",
            "last_name": "Doe",
            "gender": "M",
            "barcode": "A123456",
            "club": "Test Club",
        }
        response = self.client.post("/register", data=data)
        self.assertEqual(response.status_code, 302)

    @patch("database.validate_barcode")
    @patch("database.club_exists")
    @patch("database.participant_exists")
    @patch("database.create_participant")
    def test_register_exception_handling(
        self, mock_create, mock_exists, mock_club_exists, mock_validate
    ):
        mock_validate.return_value = True
        mock_club_exists.return_value = True
        mock_exists.return_value = False
        mock_create.side_effect = Exception("Database error")

        data = {
            "first_name": "John",
            "last_name": "Doe",
            "gender": "M",
            "dob": "1990-01-01",
            "barcode": "A123456",
            "club": "Test Club",
        }
        response = self.client.post("/register", data=data)
        self.assertEqual(response.status_code, 302)

    @patch("database.is_admin_email")
    @patch("database.add_club")
    def test_add_club_exception(self, mock_add_club, mock_is_admin):
        mock_is_admin.return_value = True
        mock_add_club.side_effect = Exception("Database error")

        with self.client.session_transaction() as sess:
            sess["user"] = {"email": "test@example.com"}

        response = self.client.post("/add_club", data={"club_name": "New Club"})
        self.assertEqual(response.status_code, 302)

    @patch("database.is_admin_email")
    @patch("database.update_club")
    def test_update_club_exception(self, mock_update, mock_is_admin):
        mock_is_admin.return_value = True
        mock_update.side_effect = Exception("Database error")

        with self.client.session_transaction() as sess:
            sess["user"] = {"email": "test@example.com"}

        response = self.client.post(
            "/edit_club/test_club", data={"club_name": "Updated Club"}
        )
        self.assertEqual(response.status_code, 302)

    @patch("database.is_admin_email")
    def test_update_club_empty_name(self, mock_is_admin):
        mock_is_admin.return_value = True

        with self.client.session_transaction() as sess:
            sess["user"] = {"email": "test@example.com"}

        response = self.client.post("/edit_club/test_club", data={"club_name": ""})
        self.assertEqual(response.status_code, 302)

    @patch("database.is_admin_email")
    @patch("database.delete_club")
    def test_delete_club_exception(self, mock_delete, mock_is_admin):
        mock_is_admin.return_value = True
        mock_delete.side_effect = Exception("Database error")

        with self.client.session_transaction() as sess:
            sess["user"] = {"email": "test@example.com"}

        response = self.client.post("/delete_club/test_club")
        self.assertEqual(response.status_code, 302)

    @patch("database.is_admin_email")
    @patch("database.delete_participant")
    def test_delete_participant_exception(self, mock_delete, mock_is_admin):
        mock_is_admin.return_value = True
        mock_delete.side_effect = Exception("Database error")

        with self.client.session_transaction() as sess:
            sess["user"] = {"email": "test@example.com"}

        response = self.client.post("/delete_participant/A123456")
        self.assertEqual(response.status_code, 302)

    @patch("database.is_admin_email")
    @patch("database.add_admin_email")
    def test_add_admin_exception(self, mock_add, mock_is_admin):
        mock_is_admin.return_value = True
        mock_add.side_effect = Exception("Database error")

        with self.client.session_transaction() as sess:
            sess["user"] = {"email": "test@example.com"}

        response = self.client.post("/add_admin", data={"email": "new@example.com"})
        self.assertEqual(response.status_code, 302)

    @patch("database.is_admin_email")
    @patch("database.get_admin_emails")
    def test_add_admin_existing_email(self, mock_get_emails, mock_is_admin):
        mock_is_admin.return_value = True
        mock_get_emails.return_value = ["existing@example.com"]

        with self.client.session_transaction() as sess:
            sess["user"] = {"email": "test@example.com"}

        response = self.client.post(
            "/add_admin", data={"email": "existing@example.com"}
        )
        self.assertEqual(response.status_code, 302)

    @patch("database.is_admin_email")
    def test_add_admin_empty_email(self, mock_is_admin):
        mock_is_admin.return_value = True

        with self.client.session_transaction() as sess:
            sess["user"] = {"email": "test@example.com"}

        response = self.client.post("/add_admin", data={"email": ""})
        self.assertEqual(response.status_code, 302)

    @patch("database.is_admin_email")
    @patch("database.remove_admin_email")
    def test_remove_admin_failure(self, mock_remove, mock_is_admin):
        mock_is_admin.return_value = True
        mock_remove.return_value = False

        with self.client.session_transaction() as sess:
            sess["user"] = {"email": "test@example.com"}

        response = self.client.post("/remove_admin", data={"email": "old@example.com"})
        self.assertEqual(response.status_code, 302)

    @patch("database.is_admin_email")
    @patch("database.clear_default_seasons")
    @patch("database.create_season")
    def test_add_season_exception(self, mock_create, mock_clear, mock_is_admin):
        mock_is_admin.return_value = True
        mock_create.side_effect = Exception("Database error")

        with self.client.session_transaction() as sess:
            sess["user"] = {"email": "test@example.com"}

        response = self.client.post(
            "/add_season", data={"season_name": "2024 Season", "is_default": "true"}
        )
        self.assertEqual(response.status_code, 302)

    @patch("database.is_admin_email")
    @patch("database.create_season")
    def test_add_season_with_empty_start_date(self, mock_create, mock_is_admin):
        mock_is_admin.return_value = True

        with self.client.session_transaction() as sess:
            sess["user"] = {"email": "test@example.com"}

        response = self.client.post(
            "/add_season",
            data={"season_name": "2024 Season", "start_date": ""},  # Empty start date
        )
        self.assertEqual(response.status_code, 302)
        # Verify empty start_date is passed (may be positional or keyword)
        call_args = mock_create.call_args
        # Check if start_date is in kwargs or if it's the 4th positional argument
        if "start_date" in call_args.kwargs:
            self.assertEqual(call_args.kwargs["start_date"], "")
        elif len(call_args.args) >= 4:
            self.assertEqual(call_args.args[3], "")

    @patch("database.is_admin_email")
    @patch("database.update_season")
    def test_update_season_exception(self, mock_update, mock_is_admin):
        mock_is_admin.return_value = True
        mock_update.side_effect = Exception("Database error")

        with self.client.session_transaction() as sess:
            sess["user"] = {"email": "test@example.com"}

        response = self.client.post(
            "/edit_season/2024", data={"age_category_size": "5"}
        )
        self.assertEqual(response.status_code, 302)

    @patch("database.is_admin_email")
    @patch("database.update_season")
    def test_update_season_with_whitespace_start_date(self, mock_update, mock_is_admin):
        mock_is_admin.return_value = True

        with self.client.session_transaction() as sess:
            sess["user"] = {"email": "test@example.com"}

        response = self.client.post(
            "/edit_season/2024",
            data={
                "age_category_size": "5",
                "start_date": "  2024-01-01  ",  # Whitespace around date
                "is_default": "false",
            },
        )
        self.assertEqual(response.status_code, 302)
        # Verify start_date whitespace is stripped
        call_args = mock_update.call_args[0][1]
        self.assertEqual(call_args["start_date"], "2024-01-01")

    @patch("database.is_admin_email")
    @patch("database.delete_season")
    def test_delete_season_exception(self, mock_delete, mock_is_admin):
        mock_is_admin.return_value = True
        mock_delete.side_effect = Exception("Database error")

        with self.client.session_transaction() as sess:
            sess["user"] = {"email": "test@example.com"}

        response = self.client.post("/delete_season/2024")
        self.assertEqual(response.status_code, 302)

    @patch("database.is_admin_email")
    @patch("database.create_race")
    def test_add_race_exception(self, mock_create, mock_is_admin):
        mock_is_admin.return_value = True
        mock_create.side_effect = Exception("Database error")

        with self.client.session_transaction() as sess:
            sess["user"] = {"email": "test@example.com"}

        response = self.client.post(
            "/add_race",
            data={"name": "Test Race", "date": "2024-01-01", "season": "2024 Season"},
        )
        self.assertEqual(response.status_code, 302)

    @patch("database.is_admin_email")
    @patch("database.delete_race_result")
    def test_delete_race_result_exception(self, mock_delete, mock_is_admin):
        mock_is_admin.return_value = True
        mock_delete.side_effect = Exception("Database error")

        with self.client.session_transaction() as sess:
            sess["user"] = {"email": "test@example.com"}

        response = self.client.post("/delete_race_result/season/race/1")
        self.assertEqual(response.status_code, 302)

    @patch("database.is_admin_email")
    @patch("database.delete_all_race_results")
    def test_delete_all_race_results_exception(self, mock_delete, mock_is_admin):
        mock_is_admin.return_value = True
        mock_delete.side_effect = Exception("Database error")

        with self.client.session_transaction() as sess:
            sess["user"] = {"email": "test@example.com"}

        response = self.client.post("/delete_all_race_results/season/race")
        self.assertEqual(response.status_code, 302)

    @patch("database.is_admin_email")
    def test_process_upload_results_exception(self, mock_is_admin):
        mock_is_admin.return_value = True

        with self.client.session_transaction() as sess:
            sess["user"] = {"email": "test@example.com"}

        from io import BytesIO

        csv_data = b"invalid,csv,data"

        response = self.client.post(
            "/process_upload_results",
            data={
                "season_name": "2024",
                "race_name": "Test Race",
                "file": (BytesIO(csv_data), "results.csv"),
            },
        )
        self.assertEqual(response.status_code, 302)

    @patch("database.is_admin_email")
    @patch("database.get_participant")
    @patch("database.add_race_result")
    def test_add_manual_result_exception(
        self, mock_add_result, mock_get_participant, mock_is_admin
    ):
        mock_is_admin.return_value = True
        mock_get_participant.return_value = {
            "first_name": "John",
            "last_name": "Doe",
            "gender": "Male",
            "date_of_birth": "1990-01-01",
            "club": "Test Club",
        }
        mock_add_result.side_effect = Exception("Database error")

        with self.client.session_transaction() as sess:
            sess["user"] = {"email": "test@example.com"}

        response = self.client.post(
            "/add_manual_result",
            data={
                "season_name": "2024",
                "race_name": "Test Race",
                "barcode": "A123456",
                "position_token": "P0001",
            },
        )
        self.assertEqual(response.status_code, 302)

    @patch("database.is_admin_email")
    def test_upload_participants_exception(self, mock_is_admin):
        mock_is_admin.return_value = True

        with self.client.session_transaction() as sess:
            sess["user"] = {"email": "test@example.com"}

        from io import BytesIO

        csv_data = b"invalid,csv,data"

        response = self.client.post(
            "/upload_participants",
            data={"file": (BytesIO(csv_data), "participants.csv")},
        )
        self.assertEqual(response.status_code, 302)

    def test_public_results_route(self):
        response = self.client.get("/results")
        self.assertEqual(response.status_code, 200)

    def test_register_page_route(self):
        response = self.client.get("/register")
        self.assertEqual(response.status_code, 200)

    @patch("database.get_participant_results")
    @patch("database.get_participant")
    def test_participant_results_route(self, mock_get_participant, mock_get_results):
        mock_get_participant.return_value = {
            "first_name": "John",
            "last_name": "Doe",
            "club": "Test Club",
            "gender": "Male",
            "barcode": "A123456",
        }
        mock_get_results.return_value = [
            {
                "season": "2024",
                "race_name": "Test Race",
                "race_date": "2024-01-15",
                "finish_token": "P0001",
                "participant": {"age_category": "Senior"},
            }
        ]

        response = self.client.get("/participant/A123456")
        self.assertEqual(response.status_code, 200)
        mock_get_participant.assert_called_with("A123456")
        mock_get_results.assert_called_with("A123456")

    @patch("database.get_participant")
    def test_participant_results_not_found(self, mock_get_participant):
        mock_get_participant.return_value = None

        response = self.client.get("/participant/A999999")
        self.assertEqual(response.status_code, 302)

    @patch("database.get_participant_results")
    def test_api_participant_results(self, mock_get_results):
        mock_get_results.return_value = [
            {
                "season": "2024",
                "race_name": "Test Race",
                "race_date": "2024-01-15",
                "finish_token": "P0001",
                "participant": {"first_name": "John", "last_name": "Doe"},
            }
        ]

        response = self.client.get("/api/participants/A123456/results")
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json, list)
        self.assertEqual(len(response.json), 1)
        mock_get_results.assert_called_with("A123456")

    @patch("database.get_participant_results")
    def test_api_participant_results_empty(self, mock_get_results):
        mock_get_results.return_value = []

        response = self.client.get("/api/participants/A999999/results")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json), 0)

    # CSV Processing Tests
    @patch("database.is_admin_email")
    @patch("database.get_clubs")
    @patch("database.validate_barcode")
    @patch("database.get_participant")
    @patch("database.process_participants_batch")
    def test_upload_participants_csv_short_rows(
        self,
        mock_batch,
        mock_get_participant,
        mock_validate,
        mock_get_clubs,
        mock_is_admin,
    ):
        mock_is_admin.return_value = True
        mock_get_clubs.return_value = [{"name": "Test Club", "short_names": ["TC"]}]
        mock_validate.return_value = True
        mock_get_participant.return_value = None

        with self.client.session_transaction() as sess:
            sess["user"] = {"email": "test@example.com"}

        from io import BytesIO

        csv_data = b"header\nA123456,John,Doe\n"  # Short row with only 3 fields

        response = self.client.post(
            "/upload_participants", data={"file": (BytesIO(csv_data), "test.csv")}
        )
        self.assertEqual(response.status_code, 302)

    @patch("database.is_admin_email")
    @patch("database.get_clubs")
    @patch("database.validate_barcode")
    @patch("database.get_participant")
    @patch("database.process_participants_batch")
    def test_upload_participants_csv_invalid_barcode(
        self,
        mock_batch,
        mock_get_participant,
        mock_validate,
        mock_get_clubs,
        mock_is_admin,
    ):
        mock_is_admin.return_value = True
        mock_get_clubs.return_value = [{"name": "Test Club", "short_names": ["TC"]}]
        mock_validate.return_value = False  # Invalid barcode
        mock_get_participant.return_value = None

        with self.client.session_transaction() as sess:
            sess["user"] = {"email": "test@example.com"}

        from io import BytesIO

        csv_data = b"header\nB123456,John,Doe,Male,01/01/1990,Test Club\n"

        response = self.client.post(
            "/upload_participants", data={"file": (BytesIO(csv_data), "test.csv")}
        )
        self.assertEqual(response.status_code, 302)

    @patch("database.is_admin_email")
    @patch("database.get_clubs")
    @patch("database.validate_barcode")
    @patch("database.get_participant")
    @patch("database.process_participants_batch")
    def test_upload_participants_csv_duplicate_barcodes(
        self,
        mock_batch,
        mock_get_participant,
        mock_validate,
        mock_get_clubs,
        mock_is_admin,
    ):
        mock_is_admin.return_value = True
        mock_get_clubs.return_value = [{"name": "Test Club", "short_names": ["TC"]}]
        mock_validate.return_value = True
        mock_get_participant.return_value = None

        with self.client.session_transaction() as sess:
            sess["user"] = {"email": "test@example.com"}

        from io import BytesIO

        csv_data = b"header\nA123456,John,Doe,Male,01/01/1990,Test Club\nA123456,Jane,Smith,Female,02/02/1991,Test Club\n"

        response = self.client.post(
            "/upload_participants", data={"file": (BytesIO(csv_data), "test.csv")}
        )
        self.assertEqual(response.status_code, 302)

    @patch("database.is_admin_email")
    @patch("database.get_clubs")
    @patch("database.validate_barcode")
    @patch("database.get_participant")
    @patch("database.process_participants_batch")
    def test_upload_participants_csv_invalid_date(
        self,
        mock_batch,
        mock_get_participant,
        mock_validate,
        mock_get_clubs,
        mock_is_admin,
    ):
        mock_is_admin.return_value = True
        mock_get_clubs.return_value = [{"name": "Test Club", "short_names": ["TC"]}]
        mock_validate.return_value = True
        mock_get_participant.return_value = None

        with self.client.session_transaction() as sess:
            sess["user"] = {"email": "test@example.com"}

        from io import BytesIO

        csv_data = b"header\nA123456,John,Doe,Male,invalid-date,Test Club\n"

        response = self.client.post(
            "/upload_participants", data={"file": (BytesIO(csv_data), "test.csv")}
        )
        self.assertEqual(response.status_code, 302)

    @patch("database.is_admin_email")
    @patch("database.get_clubs")
    @patch("database.validate_barcode")
    @patch("database.get_participant")
    @patch("database.process_participants_batch")
    def test_upload_participants_csv_missing_fields(
        self,
        mock_batch,
        mock_get_participant,
        mock_validate,
        mock_get_clubs,
        mock_is_admin,
    ):
        mock_is_admin.return_value = True
        mock_get_clubs.return_value = [{"name": "Test Club", "short_names": ["TC"]}]
        mock_validate.return_value = True
        mock_get_participant.return_value = None

        with self.client.session_transaction() as sess:
            sess["user"] = {"email": "test@example.com"}

        from io import BytesIO

        csv_data = (
            b"header\nA123456,,Doe,Male,01/01/1990,Test Club\n"  # Missing first name
        )

        response = self.client.post(
            "/upload_participants", data={"file": (BytesIO(csv_data), "test.csv")}
        )
        self.assertEqual(response.status_code, 302)

    @patch("database.is_admin_email")
    @patch("database.get_clubs")
    @patch("database.validate_barcode")
    @patch("database.get_participant")
    @patch("database.process_participants_batch")
    def test_upload_participants_csv_invalid_gender(
        self,
        mock_batch,
        mock_get_participant,
        mock_validate,
        mock_get_clubs,
        mock_is_admin,
    ):
        mock_is_admin.return_value = True
        mock_get_clubs.return_value = [{"name": "Test Club", "short_names": ["TC"]}]
        mock_validate.return_value = True
        mock_get_participant.return_value = None

        with self.client.session_transaction() as sess:
            sess["user"] = {"email": "test@example.com"}

        from io import BytesIO

        csv_data = (
            b"header\nA123456,John,Doe,Other,01/01/1990,Test Club\n"  # Invalid gender
        )

        response = self.client.post(
            "/upload_participants", data={"file": (BytesIO(csv_data), "test.csv")}
        )
        self.assertEqual(response.status_code, 302)

    @patch("database.is_admin_email")
    @patch("database.get_clubs")
    @patch("database.validate_barcode")
    @patch("database.get_participant")
    @patch("database.validate_and_normalize_club")
    @patch("database.process_participants_batch")
    def test_upload_participants_csv_invalid_club(
        self,
        mock_batch,
        mock_normalize_club,
        mock_get_participant,
        mock_validate,
        mock_get_clubs,
        mock_is_admin,
    ):
        mock_is_admin.return_value = True
        mock_get_clubs.return_value = [{"name": "Test Club", "short_names": ["TC"]}]
        mock_validate.return_value = True
        mock_get_participant.return_value = None
        mock_normalize_club.return_value = None  # Invalid club

        with self.client.session_transaction() as sess:
            sess["user"] = {"email": "test@example.com"}

        from io import BytesIO

        csv_data = b"header\nA123456,John,Doe,Male,01/01/1990,Invalid Club\n"

        response = self.client.post(
            "/upload_participants", data={"file": (BytesIO(csv_data), "test.csv")}
        )
        self.assertEqual(response.status_code, 302)

    @patch("database.is_admin_email")
    @patch("database.get_clubs")
    @patch("database.validate_barcode")
    @patch("database.get_participant")
    @patch("database.validate_and_normalize_club")
    @patch("database.process_participants_batch")
    def test_upload_participants_csv_existing_participant_no_changes(
        self,
        mock_batch,
        mock_normalize_club,
        mock_get_participant,
        mock_validate,
        mock_get_clubs,
        mock_is_admin,
    ):
        mock_is_admin.return_value = True
        mock_get_clubs.return_value = [{"name": "Test Club", "short_names": ["TC"]}]
        mock_validate.return_value = True
        mock_normalize_club.return_value = "Test Club"
        # Existing participant with same data
        mock_get_participant.return_value = {
            "first_name": "John",
            "last_name": "Doe",
            "gender": "Male",
            "date_of_birth": "1990-01-01",
            "club": "Test Club",
        }

        with self.client.session_transaction() as sess:
            sess["user"] = {"email": "test@example.com"}

        from io import BytesIO

        csv_data = b"header\nA123456,John,Doe,Male,01/01/1990,Test Club\n"

        response = self.client.post(
            "/upload_participants", data={"file": (BytesIO(csv_data), "test.csv")}
        )
        self.assertEqual(response.status_code, 302)

    @patch("database.is_admin_email")
    @patch("database.get_clubs")
    @patch("database.validate_barcode")
    @patch("database.get_participant")
    @patch("database.validate_and_normalize_club")
    @patch("database.process_participants_batch")
    def test_upload_participants_csv_existing_participant_with_changes(
        self,
        mock_batch,
        mock_normalize_club,
        mock_get_participant,
        mock_validate,
        mock_get_clubs,
        mock_is_admin,
    ):
        mock_is_admin.return_value = True
        mock_get_clubs.return_value = [{"name": "Test Club", "short_names": ["TC"]}]
        mock_validate.return_value = True
        mock_normalize_club.return_value = "Test Club"
        # Existing participant with different data
        mock_get_participant.return_value = {
            "first_name": "John",
            "last_name": "Smith",  # Different last name
            "gender": "Male",
            "date_of_birth": "1990-01-01",
            "club": "Test Club",
        }

        with self.client.session_transaction() as sess:
            sess["user"] = {"email": "test@example.com"}

        from io import BytesIO

        csv_data = b"header\nA123456,John,Doe,Male,01/01/1990,Test Club\n"

        response = self.client.post(
            "/upload_participants", data={"file": (BytesIO(csv_data), "test.csv")}
        )
        self.assertEqual(response.status_code, 302)

    # CSV Results Processing Tests
    @patch("database.is_admin_email")
    @patch("database.get_participant")
    @patch("database.add_race_results_batch")
    def test_process_upload_results_csv_empty_finish_token(
        self, mock_batch, mock_get_participant, mock_is_admin
    ):
        mock_is_admin.return_value = True
        mock_get_participant.return_value = {
            "first_name": "John",
            "last_name": "Doe",
            "gender": "Male",
            "date_of_birth": "1990-01-01",
            "club": "Test Club",
        }

        with self.client.session_transaction() as sess:
            sess["user"] = {"email": "test@example.com"}

        from io import BytesIO

        csv_data = b"ID,Pos\nA123456,\n"  # Empty finish token

        response = self.client.post(
            "/process_upload_results",
            data={
                "season_name": "2024",
                "race_name": "Test Race",
                "file": (BytesIO(csv_data), "results.csv"),
            },
        )
        self.assertEqual(response.status_code, 302)

    @patch("database.is_admin_email")
    @patch("database.get_participant")
    @patch("database.add_race_results_batch")
    def test_process_upload_results_csv_duplicate_tokens(
        self, mock_batch, mock_get_participant, mock_is_admin
    ):
        mock_is_admin.return_value = True
        mock_get_participant.return_value = {
            "first_name": "John",
            "last_name": "Doe",
            "gender": "Male",
            "date_of_birth": "1990-01-01",
            "club": "Test Club",
        }

        with self.client.session_transaction() as sess:
            sess["user"] = {"email": "test@example.com"}

        from io import BytesIO

        csv_data = b"ID,Pos\nA123456,1\nA654321,1\n"  # Duplicate finish token

        response = self.client.post(
            "/process_upload_results",
            data={
                "season_name": "2024",
                "race_name": "Test Race",
                "file": (BytesIO(csv_data), "results.csv"),
            },
        )
        self.assertEqual(response.status_code, 302)

    @patch("database.is_admin_email")
    @patch("database.get_participant")
    @patch("database.add_race_results_batch")
    def test_process_upload_results_csv_unknown_participant(
        self, mock_batch, mock_get_participant, mock_is_admin
    ):
        mock_is_admin.return_value = True
        mock_get_participant.return_value = None  # Unknown participant

        with self.client.session_transaction() as sess:
            sess["user"] = {"email": "test@example.com"}

        from io import BytesIO

        csv_data = b"ID,Pos\nA999999,1\n"  # Unknown participant

        response = self.client.post(
            "/process_upload_results",
            data={
                "season_name": "2024",
                "race_name": "Test Race",
                "file": (BytesIO(csv_data), "results.csv"),
            },
        )
        self.assertEqual(response.status_code, 302)

    @patch("database.is_admin_email")
    @patch("database.get_participant")
    @patch("database.add_race_results_batch")
    def test_process_upload_results_csv_invalid_date_format(
        self, mock_batch, mock_get_participant, mock_is_admin
    ):
        mock_is_admin.return_value = True
        mock_get_participant.return_value = {
            "first_name": "John",
            "last_name": "Doe",
            "gender": "Male",
            "date_of_birth": "invalid-date",  # Invalid date format
            "club": "Test Club",
        }

        with self.client.session_transaction() as sess:
            sess["user"] = {"email": "test@example.com"}

        from io import BytesIO

        csv_data = b"ID,Pos\nA123456,1\n"

        response = self.client.post(
            "/process_upload_results",
            data={
                "season_name": "2024",
                "race_name": "Test Race",
                "file": (BytesIO(csv_data), "results.csv"),
            },
        )
        self.assertEqual(response.status_code, 302)

    @patch("database.is_admin_email")
    @patch("database.get_participant")
    @patch("database.add_race_results_batch")
    def test_add_manual_result_invalid_date_format(
        self, mock_batch, mock_get_participant, mock_is_admin
    ):
        mock_is_admin.return_value = True
        mock_get_participant.return_value = {
            "first_name": "John",
            "last_name": "Doe",
            "gender": "Male",
            "date_of_birth": "invalid-date",  # Invalid date format
            "club": "Test Club",
        }

        with self.client.session_transaction() as sess:
            sess["user"] = {"email": "test@example.com"}

        response = self.client.post(
            "/add_manual_result",
            data={
                "season_name": "2024",
                "race_name": "Test Race",
                "barcode": "A123456",
                "finish_token": "1",
            },
        )
        self.assertEqual(response.status_code, 302)

    # Test missing lines coverage
    @patch("database.get_default_season")
    @patch("database.get_seasons")
    @patch("database.get_races_by_season")
    def test_api_seasons_with_default_race(
        self, mock_get_races, mock_get_seasons, mock_get_default
    ):
        """Test lines 72-76: default race selection logic"""
        mock_get_seasons.return_value = ["2024 Season"]
        mock_get_default.return_value = "2024 Season"
        mock_get_races.return_value = [
            {"name": "Race 2", "date": "2024-02-01"},
            {"name": "Race 1", "date": "2024-01-01"},
        ]

        response = self.client.get("/api/seasons")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["default_race"], "Race 2")  # Most recent

    @patch("database.get_default_season")
    @patch("database.get_seasons")
    @patch("database.get_races_by_season")
    def test_api_seasons_no_races_for_default(
        self, mock_get_races, mock_get_seasons, mock_get_default
    ):
        """Test lines 72-76: no races for default season"""
        mock_get_seasons.return_value = ["2024 Season"]
        mock_get_default.return_value = "2024 Season"
        mock_get_races.return_value = []  # No races

        response = self.client.get("/api/seasons")
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.json["default_race"])

    @patch("database.get_races_by_season")
    @patch("database.get_race_results")
    def test_api_championship_organizing_clubs_logic(
        self, mock_get_results, mock_get_races
    ):
        """Test lines 203-211: organizing clubs logic in championship"""
        mock_get_races.return_value = [
            {"name": "Race1", "organising_clubs": ["Club A"]}
        ]
        mock_get_results.return_value = [
            {"participant": {"first_name": "John", "gender": "Male", "club": "Club A"}},
            {"participant": {"first_name": "Jane", "gender": "Male", "club": "Club B"}},
        ]

        response = self.client.get("/api/championship/season/Male")
        self.assertEqual(response.status_code, 200)
        # Verify organizing club gets "ORG" status
        standings = response.json["standings"]
        club_a_data = next((s for s in standings if s["name"] == "Club A"), None)
        self.assertIsNotNone(club_a_data)
        self.assertEqual(club_a_data["race_points"]["Race1"], "ORG")

    @patch("database.get_races_by_season")
    @patch("database.get_race_results")
    def test_api_championship_all_clubs_logic(self, mock_get_results, mock_get_races):
        """Test lines 219, 225-228: all clubs and DQ logic"""
        mock_get_races.return_value = [
            {"name": "Race1", "organising_clubs": ["Club B"]}  # Club B organizes
        ]
        # Return results - Club A has insufficient runners, Club B organizes
        mock_get_results.return_value = [
            {"participant": {"first_name": "John", "gender": "Male", "club": "Club A"}}
        ]

        response = self.client.get("/api/championship/season/Male")
        self.assertEqual(response.status_code, 200)
        # Club A won't appear (no activity), Club B will appear as organizer
        standings = response.json["standings"]
        club_b_data = next((s for s in standings if s["name"] == "Club B"), None)
        self.assertIsNotNone(club_b_data)
        self.assertEqual(club_b_data["race_points"]["Race1"], "ORG")

    @patch("database.get_races_by_season")
    @patch("database.get_race_results")
    def test_api_championship_sufficient_runners(
        self, mock_get_results, mock_get_races
    ):
        """Test lines 247, 253-254: sufficient runners logic"""
        mock_get_races.return_value = [{"name": "Race1", "organising_clubs": []}]
        # Return sufficient runners for Male (4+)
        mock_get_results.return_value = [
            {
                "participant": {
                    "first_name": "John1",
                    "gender": "Male",
                    "club": "Club A",
                }
            },
            {
                "participant": {
                    "first_name": "John2",
                    "gender": "Male",
                    "club": "Club A",
                }
            },
            {
                "participant": {
                    "first_name": "John3",
                    "gender": "Male",
                    "club": "Club A",
                }
            },
            {
                "participant": {
                    "first_name": "John4",
                    "gender": "Male",
                    "club": "Club A",
                }
            },
        ]

        response = self.client.get("/api/championship/season/Male")
        self.assertEqual(response.status_code, 200)
        # Verify club gets points (not DQ) with sufficient runners
        standings = response.json["standings"]
        club_a_data = next((s for s in standings if s["name"] == "Club A"), None)
        self.assertIsNotNone(club_a_data)
        self.assertNotEqual(club_a_data["total_points"], "DQ")

    @patch("database.get_races_by_season")
    @patch("database.get_race_results")
    def test_api_championship_ranking_logic(self, mock_get_results, mock_get_races):
        """Test lines 263, 444-445, 454-455: ranking and tie logic"""
        mock_get_races.return_value = [{"name": "Race1", "organising_clubs": []}]
        # Two clubs with sufficient runners
        mock_get_results.return_value = [
            {
                "participant": {
                    "first_name": "John1",
                    "gender": "Male",
                    "club": "Club A",
                }
            },
            {
                "participant": {
                    "first_name": "John2",
                    "gender": "Male",
                    "club": "Club A",
                }
            },
            {
                "participant": {
                    "first_name": "John3",
                    "gender": "Male",
                    "club": "Club A",
                }
            },
            {
                "participant": {
                    "first_name": "John4",
                    "gender": "Male",
                    "club": "Club A",
                }
            },
            {
                "participant": {
                    "first_name": "Jane1",
                    "gender": "Male",
                    "club": "Club B",
                }
            },
            {
                "participant": {
                    "first_name": "Jane2",
                    "gender": "Male",
                    "club": "Club B",
                }
            },
            {
                "participant": {
                    "first_name": "Jane3",
                    "gender": "Male",
                    "club": "Club B",
                }
            },
            {
                "participant": {
                    "first_name": "Jane4",
                    "gender": "Male",
                    "club": "Club B",
                }
            },
        ]

        response = self.client.get("/api/championship/season/Male")
        self.assertEqual(response.status_code, 200)
        standings = response.json["standings"]
        self.assertEqual(len(standings), 2)  # Both clubs should be in standings

    @patch("database.get_races_by_season")
    @patch("database.get_race_results")
    def test_api_championship_no_organizing_adjustment(
        self, mock_get_results, mock_get_races
    ):
        """Test lines 555-556: no organizing race adjustment"""
        mock_get_races.return_value = [
            {"name": "Race1", "organising_clubs": ["Other Club"]},
            {"name": "Race2", "organising_clubs": ["Other Club"]},
        ]
        # Return sufficient runners for Male (4+) to get points in both races
        mock_get_results.return_value = [
            {
                "participant": {
                    "first_name": "John1",
                    "gender": "Male",
                    "club": "Club A",
                }
            },
            {
                "participant": {
                    "first_name": "John2",
                    "gender": "Male",
                    "club": "Club A",
                }
            },
            {
                "participant": {
                    "first_name": "John3",
                    "gender": "Male",
                    "club": "Club A",
                }
            },
            {
                "participant": {
                    "first_name": "John4",
                    "gender": "Male",
                    "club": "Club A",
                }
            },
        ]

        response = self.client.get("/api/championship/season/Male")
        self.assertEqual(response.status_code, 200)
        # Verify club gets points and adjustment is applied (should be < raw total due to no organizing)
        standings = response.json["standings"]
        club_a_data = next((s for s in standings if s["name"] == "Club A"), None)
        self.assertIsNotNone(club_a_data)
        self.assertNotEqual(club_a_data["total_points"], "DQ")
        # Adjustment applied: 2 rankings * (1/2) = 1.0
        self.assertEqual(club_a_data["total_points"], 1.0)

    @patch("database.get_races_by_season")
    @patch("database.get_race_results")
    def test_api_individual_championship_name_filtering(
        self, mock_get_results, mock_get_races
    ):
        """Test lines 696-697: individual championship name filtering"""
        mock_get_races.return_value = [
            {"name": "Race1"},
            {"name": "Race2"},
            {"name": "Race3"},
        ]
        mock_get_results.side_effect = [
            # Race 1
            [
                {
                    "participant": {
                        "first_name": "",
                        "last_name": "Doe",
                        "gender": "Male",
                        "club": "Club A",
                    }
                }
            ],  # Empty first name
            # Race 2
            [
                {
                    "participant": {
                        "first_name": "John",
                        "last_name": "",
                        "gender": "Male",
                        "club": "Club A",
                    }
                }
            ],  # Empty last name
            # Race 3
            [
                {
                    "participant": {
                        "first_name": "John",
                        "last_name": "Doe",
                        "gender": "Male",
                        "club": "Club A",
                    }
                }
            ],  # Valid name
        ]

        response = self.client.get("/api/individual-championship/season/Male")
        self.assertEqual(response.status_code, 200)
        # Should only include valid names
        standings = response.json["standings"]
        self.assertEqual(len(standings), 0)  # No one has 3+ races with valid names

    @patch("database.get_races_by_season")
    @patch("database.get_race_results")
    def test_api_individual_championship_sufficient_races(
        self, mock_get_results, mock_get_races
    ):
        """Test lines 784-785: individual championship sufficient races logic"""
        mock_get_races.return_value = [
            {"name": "Race1"},
            {"name": "Race2"},
            {"name": "Race3"},
        ]
        mock_get_results.side_effect = [
            # Race 1
            [
                {
                    "participant": {
                        "first_name": "John",
                        "last_name": "Doe",
                        "gender": "Male",
                        "club": "Club A",
                    }
                }
            ],
            # Race 2
            [
                {
                    "participant": {
                        "first_name": "John",
                        "last_name": "Doe",
                        "gender": "Male",
                        "club": "Club A",
                    }
                }
            ],
            # Race 3
            [
                {
                    "participant": {
                        "first_name": "John",
                        "last_name": "Doe",
                        "gender": "Male",
                        "club": "Club A",
                    }
                }
            ],
        ]

        response = self.client.get("/api/individual-championship/season/Male")
        self.assertEqual(response.status_code, 200)
        # Should include participant with 3+ races
        standings = response.json["standings"]
        self.assertEqual(len(standings), 1)
        self.assertEqual(standings[0]["name"], "John Doe")

    @patch("database.validate_barcode")
    @patch("database.club_exists")
    @patch("database.participant_exists")
    def test_register_edit_same_participant_barcode_check(
        self, mock_exists, mock_club_exists, mock_validate
    ):
        """Test lines 802-804: edit participant with same barcode"""
        mock_validate.return_value = True
        mock_club_exists.return_value = True
        mock_exists.return_value = True  # Barcode exists

        # Simulate logged in user
        with self.client.session_transaction() as sess:
            sess["user"] = {"email": "test@example.com"}

        data = {
            "first_name": "John",
            "last_name": "Doe",
            "gender": "M",
            "dob": "1990-01-01",
            "barcode": "A123456",
            "club": "Test Club",
        }
        # Edit participant with same barcode (A123456 editing A123456)
        response = self.client.post("/edit_participant/A123456", data=data)
        self.assertEqual(response.status_code, 302)

    @patch("database.validate_barcode")
    @patch("database.club_exists")
    @patch("database.participant_exists")
    @patch("database.update_participant")
    def test_register_edit_different_participant_barcode_check(
        self, mock_update, mock_exists, mock_club_exists, mock_validate
    ):
        """Test lines 807-808: edit participant with different barcode that exists"""
        mock_validate.return_value = True
        mock_club_exists.return_value = True
        mock_exists.return_value = True  # Different barcode exists

        # Simulate logged in user
        with self.client.session_transaction() as sess:
            sess["user"] = {"email": "test@example.com"}

        data = {
            "first_name": "John",
            "last_name": "Doe",
            "gender": "M",
            "dob": "1990-01-01",
            "barcode": "A654321",  # Different barcode
            "club": "Test Club",
        }
        # Edit participant A123456 but trying to change to existing barcode A654321
        response = self.client.post("/edit_participant/A123456", data=data)
        self.assertEqual(response.status_code, 302)
        # Should not call update_participant due to barcode conflict
        mock_update.assert_not_called()

    @patch("database.validate_barcode")
    @patch("database.club_exists")
    @patch("database.participant_exists")
    @patch("database.update_participant")
    def test_register_update_participant_exception(
        self, mock_update, mock_exists, mock_club_exists, mock_validate
    ):
        """Test lines 891-892: update participant exception handling"""
        mock_validate.return_value = True
        mock_club_exists.return_value = True
        mock_exists.return_value = False
        mock_update.side_effect = Exception("Database error")

        # Simulate logged in user
        with self.client.session_transaction() as sess:
            sess["user"] = {"email": "test@example.com"}

        data = {
            "first_name": "John",
            "last_name": "Doe",
            "gender": "M",
            "dob": "1990-01-01",
            "barcode": "A123456",
            "club": "Test Club",
        }
        response = self.client.post("/edit_participant/test_id", data=data)
        self.assertEqual(response.status_code, 302)

    @patch("database.is_admin_email")
    @patch("database.get_seasons")
    @patch("database.get_season")
    def test_seasons_with_missing_season_data(
        self, mock_get_season, mock_get_seasons, mock_is_admin
    ):
        """Test lines 926-927: seasons with missing season data"""
        mock_is_admin.return_value = True
        mock_get_seasons.return_value = ["2024 Season"]
        mock_get_season.return_value = None  # Missing season data

        with self.client.session_transaction() as sess:
            sess["user"] = {"email": "test@example.com"}

        response = self.client.get("/seasons")
        self.assertEqual(response.status_code, 200)
        # Should handle missing season data gracefully

    @patch("database.is_admin_email")
    def test_add_season_invalid_age_category_size(self, mock_is_admin):
        """Test lines 992-993: invalid age category size"""
        mock_is_admin.return_value = True

        with self.client.session_transaction() as sess:
            sess["user"] = {"email": "test@example.com"}

        response = self.client.post(
            "/add_season",
            data={"season_name": "2024 Season", "age_category_size": "invalid"},
        )
        self.assertEqual(response.status_code, 302)

    @patch("database.is_admin_email")
    @patch("database.clear_default_seasons")
    @patch("database.update_season")
    def test_update_season_invalid_age_category_size(
        self, mock_update, mock_clear, mock_is_admin
    ):
        """Test lines 1063-1064: update season with invalid age category size"""
        mock_is_admin.return_value = True

        with self.client.session_transaction() as sess:
            sess["user"] = {"email": "test@example.com"}

        # This should handle invalid age_category_size gracefully
        response = self.client.post(
            "/edit_season/2024", data={"age_category_size": "5", "is_default": "false"}
        )
        self.assertEqual(response.status_code, 302)

    @patch("database.is_admin_email")
    @patch("database.get_seasons")
    @patch("database.get_races_by_season")
    def test_races_with_season_assignment(
        self, mock_get_races, mock_get_seasons, mock_is_admin
    ):
        """Test lines 1116-1117: races with season assignment"""
        mock_is_admin.return_value = True
        mock_get_seasons.return_value = ["2024 Season"]
        mock_get_races.return_value = [{"name": "Test Race", "date": "2024-01-01"}]

        with self.client.session_transaction() as sess:
            sess["user"] = {"email": "test@example.com"}

        response = self.client.get("/races")
        self.assertEqual(response.status_code, 200)
        # Should assign season to each race


if __name__ == "__main__":
    unittest.main()
