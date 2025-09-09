import unittest
from unittest.mock import Mock, patch

from app import app
from database import (
    get_club_id_by_name,
    init_running_clubs,
    validate_barcode,
)


class TestApp(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()
        init_running_clubs()

    def test_validate_barcode_valid(self):
        self.assertTrue(validate_barcode("A123456"))
        self.assertTrue(validate_barcode("A1234567"))
        self.assertTrue(validate_barcode("a123456"))

    def test_validate_barcode_invalid(self):
        self.assertFalse(validate_barcode("B123456"))
        self.assertFalse(validate_barcode("A12345"))
        self.assertFalse(validate_barcode("A12345678"))
        self.assertFalse(validate_barcode("123456"))

    def test_index_route(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)

    def test_get_clubs_api(self):
        response = self.client.get("/api/clubs")
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json, list)

    @patch("database.db")
    def test_get_club_id_by_name(self, mock_db):
        mock_doc = Mock()
        mock_doc.id = "club_id"
        mock_db.collection.return_value.where.return_value.get.return_value = [mock_doc]

        result = get_club_id_by_name("Chandler's Ford Swifts")
        self.assertEqual(result, "club_id")

    def test_participants_requires_login(self):
        response = self.client.get("/participants")
        self.assertEqual(response.status_code, 302)

    def test_clubs_requires_login(self):
        response = self.client.get("/clubs")
        self.assertEqual(response.status_code, 302)

    def test_register_missing_fields(self):
        response = self.client.post("/register", data={})
        self.assertEqual(response.status_code, 302)

    def test_register_valid_data(self):
        data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "gender": "Male",
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
            "email": "john@example.com",
            "gender": "Male",
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
            "email": "jane@example.com",
            "gender": "Female",
            "dob": "1990-01-01",
            "barcode": "A654321",
            "club": "Chandler's Ford Swifts",
        }
        response = self.client.post("/edit_participant/test_id", data=data)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.location)

    def test_edit_participant_with_auth(self):
        # Simulate logged in user
        with self.client.session_transaction() as sess:
            sess["user"] = {"email": "test@example.com"}

        data = {
            "first_name": "Jane",
            "last_name": "Doe",
            "email": "jane@example.com",
            "gender": "Female",
            "dob": "1990-01-01",
            "barcode": "A654321",
            "club": "Chandler's Ford Swifts",
        }
        response = self.client.post("/edit_participant/test_id", data=data)
        self.assertEqual(response.status_code, 302)

    def test_register_missing_first_name(self):
        data = {
            "last_name": "Doe",
            "email": "john@example.com",
            "gender": "Male",
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
            "email": "john@example.com",
            "gender": "Male",
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

    def test_admins_with_auth(self):
        with self.client.session_transaction() as sess:
            sess["user"] = {"email": "test@example.com"}

        response = self.client.get("/admins")
        self.assertEqual(response.status_code, 200)

    def test_add_admin_with_auth(self):
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

    def test_seasons_with_auth(self):
        with self.client.session_transaction() as sess:
            sess["user"] = {"email": "test@example.com"}

        response = self.client.get("/seasons")
        self.assertEqual(response.status_code, 200)

    def test_add_season_with_auth(self):
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

    def test_races_with_auth(self):
        with self.client.session_transaction() as sess:
            sess["user"] = {"email": "test@example.com"}

        response = self.client.get("/races")
        self.assertEqual(response.status_code, 200)

    def test_add_race_with_auth(self):
        with self.client.session_transaction() as sess:
            sess["user"] = {"email": "test@example.com"}

        response = self.client.post(
            "/add_race",
            data={"name": "Test Race", "date": "2024-01-01", "season": "2024 Season"},
        )
        self.assertEqual(response.status_code, 302)

    def test_api_seasons(self):
        response = self.client.get("/api/seasons")
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json, list)

    def test_race_results_requires_auth(self):
        response = self.client.get("/race_results/test_race_id")
        self.assertEqual(response.status_code, 302)

    def test_race_results_with_auth(self):
        with self.client.session_transaction() as sess:
            sess["user"] = {"email": "test@example.com"}

        response = self.client.get("/race_results/test_race_id")
        self.assertEqual(response.status_code, 302)

    @patch("database.get_all_seasons_with_ids")
    @patch("database.get_races_by_season")
    def test_api_seasons_with_id(self, mock_get_races, mock_get_seasons):
        mock_get_seasons.return_value = [{"id": "season1", "name": "2024 Season"}]
        mock_get_races.return_value = [
            {"id": "race1", "name": "Test Race", "date": "2024-01-01"}
        ]

        response = self.client.get("/api/seasons/season1")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["name"], "2024 Season")
        self.assertIn("races", response.json)

    @patch("database.get_all_seasons_with_ids")
    def test_api_seasons_not_found(self, mock_get_seasons):
        mock_get_seasons.return_value = []

        response = self.client.get("/api/seasons/nonexistent")
        self.assertEqual(response.status_code, 404)

    @patch("database.get_all_races")
    @patch("database.get_race_results")
    def test_api_races_with_results(self, mock_get_results, mock_get_races):
        mock_get_races.return_value = [
            {
                "id": "race1",
                "name": "Test Race",
                "date": "2024-01-01",
                "season": "2024 Season",
            }
        ]
        mock_get_results.return_value = [
            {
                "id": "result1",
                "barcode": "A123456",
                "position": "P0001",
                "participant_name": "John Doe",
                "gender": "Male",
                "age_category": "Senior",
            }
        ]

        response = self.client.get("/api/races/race1")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["name"], "Test Race")
        self.assertIn("results", response.json)
        self.assertEqual(len(response.json["results"]), 1)

    @patch("database.get_all_races")
    def test_api_races_not_found(self, mock_get_races):
        mock_get_races.return_value = []

        response = self.client.get("/api/races/nonexistent")
        self.assertEqual(response.status_code, 404)

    @patch("database.get_all_races")
    @patch("database.get_race_results")
    def test_api_races_filter_missing_data(self, mock_get_results, mock_get_races):
        mock_get_races.return_value = [
            {
                "id": "race1",
                "name": "Test Race",
                "date": "2024-01-01",
                "season": "2024 Season",
            }
        ]
        mock_get_results.return_value = [
            {
                "id": "result1",
                "participant_name": "John Doe",
                "gender": "Male",
                "age_category": "Senior",
            },
            {"id": "result2", "participant_name": "", "gender": "", "age_category": ""},
        ]

        response = self.client.get("/api/races/race1")
        self.assertEqual(len(response.json["results"]), 1)

        response = self.client.get("/api/races/race1?showMissingData=true")
        self.assertEqual(len(response.json["results"]), 2)

    @patch("database.get_all_races")
    @patch("database.get_race_results")
    def test_api_races_filter_category(self, mock_get_results, mock_get_races):
        mock_get_races.return_value = [
            {
                "id": "race1",
                "name": "Test Race",
                "date": "2024-01-01",
                "season": "2024 Season",
            }
        ]
        mock_get_results.return_value = [
            {
                "id": "result1",
                "participant_name": "John Doe",
                "gender": "Male",
                "age_category": "Senior",
            },
            {
                "id": "result2",
                "participant_name": "Jane Doe",
                "gender": "Female",
                "age_category": "V40",
            },
        ]

        response = self.client.get("/api/races/race1?category=Senior")
        self.assertEqual(len(response.json["results"]), 1)
        self.assertEqual(response.json["results"][0]["age_category"], "Senior")

    @patch("database.get_all_races")
    @patch("database.get_race_results")
    def test_api_races_filter_gender(self, mock_get_results, mock_get_races):
        mock_get_races.return_value = [
            {
                "id": "race1",
                "name": "Test Race",
                "date": "2024-01-01",
                "season": "2024 Season",
            }
        ]
        mock_get_results.return_value = [
            {
                "id": "result1",
                "participant_name": "John Doe",
                "gender": "Male",
                "age_category": "Senior",
            },
            {
                "id": "result2",
                "participant_name": "Jane Doe",
                "gender": "Female",
                "age_category": "V40",
            },
        ]

        response = self.client.get("/api/races/race1?gender=Female")
        self.assertEqual(len(response.json["results"]), 1)
        self.assertEqual(response.json["results"][0]["gender"], "Female")

    @patch("database.get_all_races")
    @patch("database.get_race_results")
    def test_api_races_filter_combined(self, mock_get_results, mock_get_races):
        mock_get_races.return_value = [
            {
                "id": "race1",
                "name": "Test Race",
                "date": "2024-01-01",
                "season": "2024 Season",
            }
        ]
        mock_get_results.return_value = [
            {
                "id": "result1",
                "participant_name": "John Doe",
                "gender": "Male",
                "age_category": "Senior",
            },
            {
                "id": "result2",
                "participant_name": "Jane Doe",
                "gender": "Female",
                "age_category": "Senior",
            },
            {
                "id": "result3",
                "participant_name": "Bob Smith",
                "gender": "Male",
                "age_category": "V40",
            },
        ]

        response = self.client.get("/api/races/race1?category=Senior&gender=Male")
        self.assertEqual(len(response.json["results"]), 1)
        self.assertEqual(response.json["results"][0]["participant_name"], "John Doe")


if __name__ == "__main__":
    unittest.main()
