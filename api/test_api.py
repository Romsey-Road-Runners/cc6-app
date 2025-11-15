import os
import unittest
from unittest.mock import patch
import sys

# Set environment variables for testing
os.environ["GOOGLE_CLOUD_PROJECT"] = "test-project"
os.environ["FLASK_SECRET_KEY"] = "test-secret-key"

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "shared_libs"))

import app


class TestAPI(unittest.TestCase):
    def setUp(self):
        app.app.config["TESTING"] = True
        self.client = app.app.test_client()

    @patch("database.get_clubs")
    def test_get_clubs_api(self, mock_get_clubs):
        mock_get_clubs.return_value = [{"name": "Test Club", "short_names": ["TC"]}]
        response = self.client.get("/clubs")
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json, list)

    @patch("database.get_default_season")
    @patch("database.get_seasons")
    def test_api_seasons(self, mock_get_seasons, mock_get_default):
        mock_get_seasons.return_value = ["2024 Season"]
        mock_get_default.return_value = None
        response = self.client.get("/seasons")
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json, dict)
        self.assertIn("seasons", response.json)
        self.assertIn("default_season", response.json)
        self.assertIn("default_race", response.json)

    @patch("database.get_season")
    @patch("database.get_races_by_season")
    def test_api_seasons_with_id(self, mock_get_races, mock_get_season):
        mock_get_season.return_value = {"age_category_size": 5}
        mock_get_races.return_value = [{"name": "Test Race", "date": "2024-01-01"}]

        response = self.client.get("/seasons/season1")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["name"], "season1")
        self.assertIn("races", response.json)

    @patch("database.get_season")
    def test_api_seasons_not_found(self, mock_get_season):
        mock_get_season.return_value = None

        response = self.client.get("/seasons/nonexistent")
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

        response = self.client.get("/seasons/season/races/race")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["name"], "race")
        self.assertIn("results", response.json)
        self.assertEqual(len(response.json["results"]), 1)

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
        response = self.client.get("/seasons/season/races/race?gender=Male")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json["results"]), 1)

        # Test category filter
        response = self.client.get("/seasons/season/races/race?category=Senior")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json["results"]), 1)

    @patch("database.get_race_results")
    def test_api_races_show_missing_data(self, mock_get_results):
        mock_get_results.return_value = [
            {"finish_token": "1", "participant": {"first_name": "John"}},
            {"finish_token": "2", "participant": {}},
        ]

        # Without showMissingData
        response = self.client.get("/seasons/season/races/race")
        self.assertEqual(len(response.json["results"]), 1)

        # With showMissingData
        response = self.client.get("/seasons/season/races/race?showMissingData=true")
        self.assertEqual(len(response.json["results"]), 2)

    def test_api_championship_missing_gender(self):
        response = self.client.get("/seasons/season/championship/team")
        self.assertEqual(response.status_code, 400)
        self.assertIn("Gender parameter is required", response.json["message"])

    @patch("database.get_races_by_season")
    def test_api_championship_no_races(self, mock_get_races):
        mock_get_races.return_value = []

        response = self.client.get("/seasons/season/championship/team?gender=Male")
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

        response = self.client.get("/seasons/season/championship/team?gender=Male")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["championship_type"], "team")

    def test_api_individual_championship_missing_gender(self):
        response = self.client.get("/seasons/season/championship/individual")
        self.assertEqual(response.status_code, 400)
        self.assertIn("Gender parameter is required", response.json["message"])

    @patch("database.get_races_by_season")
    def test_api_individual_championship_no_races(self, mock_get_races):
        mock_get_races.return_value = []

        response = self.client.get(
            "/seasons/season/championship/individual?gender=Male"
        )
        self.assertEqual(response.status_code, 404)

    @patch("database.get_races_by_season")
    @patch("database.get_race_results")
    @patch("database.get_season")
    def test_api_individual_championship_with_results(
        self, mock_get_season, mock_get_results, mock_get_races
    ):
        mock_get_season.return_value = {"individual_results_best_of": 3}
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

        response = self.client.get(
            "/seasons/season/championship/individual?gender=Male"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["championship_type"], "individual")

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

        response = self.client.get("/participants/A123456/results")
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json, list)
        self.assertEqual(len(response.json), 1)
        mock_get_results.assert_called_with("A123456")

    @patch("database.get_participant_results")
    def test_api_participant_results_empty(self, mock_get_results):
        mock_get_results.return_value = []

        response = self.client.get("/participants/A999999/results")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json), 0)

    @patch("database.get_default_season")
    @patch("database.get_seasons")
    @patch("database.get_races_by_season")
    def test_api_seasons_with_default_race(
        self, mock_get_races, mock_get_seasons, mock_get_default
    ):
        """Test default race selection logic"""
        mock_get_seasons.return_value = ["2024 Season"]
        mock_get_default.return_value = "2024 Season"
        mock_get_races.return_value = [
            {"name": "Race 2", "date": "2024-02-01"},
            {"name": "Race 1", "date": "2024-01-01"},
        ]

        response = self.client.get("/seasons")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["default_race"], "Race 2")  # Most recent

    @patch("database.get_default_season")
    @patch("database.get_seasons")
    @patch("database.get_races_by_season")
    def test_api_seasons_no_races_for_default(
        self, mock_get_races, mock_get_seasons, mock_get_default
    ):
        """Test no races for default season"""
        mock_get_seasons.return_value = ["2024 Season"]
        mock_get_default.return_value = "2024 Season"
        mock_get_races.return_value = []  # No races

        response = self.client.get("/seasons")
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.json["default_race"])

    @patch("database.get_races_by_season")
    @patch("database.get_race_results")
    def test_api_championship_organizing_clubs_logic(
        self, mock_get_results, mock_get_races
    ):
        """Test organizing clubs logic in championship"""
        mock_get_races.return_value = [
            {"name": "Race1", "organising_clubs": ["Club A"]}
        ]
        mock_get_results.return_value = [
            {"participant": {"first_name": "John", "gender": "Male", "club": "Club A"}},
            {"participant": {"first_name": "Jane", "gender": "Male", "club": "Club B"}},
        ]

        response = self.client.get("/seasons/season/championship/team?gender=Male")
        self.assertEqual(response.status_code, 200)
        # Verify organizing club gets "ORG" status
        standings = response.json["standings"]
        club_a_data = next((s for s in standings if s["name"] == "Club A"), None)
        self.assertIsNotNone(club_a_data)
        self.assertEqual(club_a_data["race_points"]["Race1"], "ORG")

    @patch("database.get_races_by_season")
    @patch("database.get_race_results")
    def test_api_championship_sufficient_runners(
        self, mock_get_results, mock_get_races
    ):
        """Test sufficient runners logic"""
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

        response = self.client.get("/seasons/season/championship/team?gender=Male")
        self.assertEqual(response.status_code, 200)
        # Verify club gets points (not DQ) with sufficient runners
        standings = response.json["standings"]
        club_a_data = next((s for s in standings if s["name"] == "Club A"), None)
        self.assertIsNotNone(club_a_data)
        self.assertNotEqual(club_a_data["total_points"], "DQ")

    @patch("database.get_races_by_season")
    @patch("database.get_race_results")
    def test_api_championship_no_organizing_adjustment(
        self, mock_get_results, mock_get_races
    ):
        """Test no organizing race adjustment"""
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

        response = self.client.get("/seasons/season/championship/team?gender=Male")
        self.assertEqual(response.status_code, 200)
        # Verify club gets points and no adjustment is applied (Club A doesn't organize)
        standings = response.json["standings"]
        club_a_data = next((s for s in standings if s["name"] == "Club A"), None)
        self.assertIsNotNone(club_a_data)
        self.assertNotEqual(club_a_data["total_points"], "DQ")
        # No adjustment since Club A doesn't organize: 4 participants × 2 races = 8 points
        self.assertEqual(club_a_data["total_points"], 8)

    @patch("database.get_races_by_season")
    @patch("database.get_race_results")
    def test_api_individual_championship_name_filtering(
        self, mock_get_results, mock_get_races
    ):
        """Test individual championship name filtering"""
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

        response = self.client.get(
            "/seasons/season/championship/individual?gender=Male"
        )
        self.assertEqual(response.status_code, 200)
        # Should only include valid names
        standings = response.json["standings"]
        self.assertEqual(len(standings), 0)  # No one has 3+ races with valid names

    @patch("database.get_races_by_season")
    @patch("database.get_race_results")
    def test_api_individual_championship_sufficient_races(
        self, mock_get_results, mock_get_races
    ):
        """Test individual championship sufficient races logic"""
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

        response = self.client.get(
            "/seasons/season/championship/individual?gender=Male"
        )
        self.assertEqual(response.status_code, 200)
        # Should include participant with 3+ races
        standings = response.json["standings"]
        self.assertEqual(len(standings), 1)
        self.assertEqual(standings[0]["name"], "John Doe")


if __name__ == "__main__":
    unittest.main()
