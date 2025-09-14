import unittest
from unittest.mock import patch

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


if __name__ == "__main__":
    unittest.main()
