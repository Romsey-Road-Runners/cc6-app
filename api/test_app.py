import unittest
from app import app
from database import validate_barcode, get_club_id_by_name, init_running_clubs


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


if __name__ == "__main__":
    unittest.main()
