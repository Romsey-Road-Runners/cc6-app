import unittest
from unittest.mock import patch

from app import app


class TestCORS(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    @patch("database.get_clubs")
    def test_cors_headers_cc6_domain(self, mock_get_clubs):
        """Test CORS headers work for CC6 domain"""
        mock_get_clubs.return_value = []

        response = self.app.get(
            "/api/clubs", headers={"Origin": "https://app.cc6.co.uk"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("Access-Control-Allow-Origin", response.headers)
        self.assertEqual(
            response.headers["Access-Control-Allow-Origin"], "https://app.cc6.co.uk"
        )

    @patch("database.get_clubs")
    def test_cors_headers_rr10_domain(self, mock_get_clubs):
        """Test CORS headers work for RR10 domain"""
        mock_get_clubs.return_value = []

        response = self.app.get(
            "/api/clubs", headers={"Origin": "https://www.rr10.org.uk"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("Access-Control-Allow-Origin", response.headers)
        self.assertEqual(
            response.headers["Access-Control-Allow-Origin"], "https://www.rr10.org.uk"
        )

    @patch("database.get_clubs")
    def test_cors_headers_localhost(self, mock_get_clubs):
        """Test CORS headers work for localhost development"""
        mock_get_clubs.return_value = []

        response = self.app.get(
            "/api/clubs", headers={"Origin": "http://localhost:3000"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("Access-Control-Allow-Origin", response.headers)
        self.assertEqual(
            response.headers["Access-Control-Allow-Origin"], "http://localhost:3000"
        )

    @patch("database.get_seasons")
    @patch("database.get_default_season")
    @patch("database.get_races_by_season")
    def test_cors_preflight_request(self, mock_races, mock_default, mock_seasons):
        """Test CORS preflight OPTIONS request"""
        mock_seasons.return_value = []
        mock_default.return_value = None
        mock_races.return_value = []

        response = self.app.options(
            "/api/seasons",
            headers={
                "Origin": "https://app.cc6.co.uk",
                "Access-Control-Request-Method": "GET",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("Access-Control-Allow-Origin", response.headers)
        self.assertIn("Access-Control-Allow-Methods", response.headers)


if __name__ == "__main__":
    unittest.main()
