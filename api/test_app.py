import unittest

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

    def test_get_club_id_by_name(self):
        result = get_club_id_by_name("Chandler's Ford Swifts")
        self.assertIsNotNone(result)

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


if __name__ == "__main__":
    unittest.main()
