import os
import unittest
from unittest.mock import Mock, patch
import sys

# Set environment variables for testing
os.environ["GOOGLE_CLOUD_PROJECT"] = "test-project"
os.environ["FLASK_SECRET_KEY"] = "test-secret-key"

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "shared_libs"))

import app


class TestAdmin(unittest.TestCase):
    def setUp(self):
        app.app.config["TESTING"] = True
        self.client = app.app.test_client()

    def test_participants_requires_login(self):
        response = self.client.get("/participants")
        self.assertEqual(response.status_code, 302)

    def test_clubs_requires_login(self):
        response = self.client.get("/clubs")
        self.assertEqual(response.status_code, 302)

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
        self.assertIn(b"Admin Emails", response.data)
        self.assertIn(b"test@example.com", response.data)

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
    @patch("database.get_season")
    def test_seasons_with_auth(self, mock_get_season, mock_get_seasons, mock_is_admin):
        mock_is_admin.return_value = True
        mock_get_seasons.return_value = ["2024 Season"]
        mock_get_season.return_value = {"age_category_size": 5}

        with self.client.session_transaction() as sess:
            sess["user"] = {"email": "test@example.com"}

        response = self.client.get("/seasons")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Seasons", response.data)

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

    def test_add_race_post_requires_auth(self):
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
        mock_get_races.return_value = [
            {"name": "Test Race", "date": "2024-01-01", "organising_clubs": []}
        ]

        with self.client.session_transaction() as sess:
            sess["user"] = {"email": "test@example.com"}

        response = self.client.get("/races")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Races", response.data)
        self.assertIn(b"Test Race", response.data)

    @patch("database.is_admin_email")
    @patch("database.get_seasons")
    @patch("database.get_clubs")
    def test_add_race_get_with_auth(
        self, mock_get_clubs, mock_get_seasons, mock_is_admin
    ):
        mock_is_admin.return_value = True
        mock_get_seasons.return_value = ["2024 Season"]
        mock_get_clubs.return_value = [{"name": "Test Club", "short_names": []}]

        with self.client.session_transaction() as sess:
            sess["user"] = {"email": "test@example.com"}

        response = self.client.get("/add_race")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Add Race", response.data)
        self.assertIn(b"2024 Season", response.data)
        self.assertIn(b"Test Club", response.data)

    def test_add_race_get_requires_auth(self):
        response = self.client.get("/add_race")
        self.assertEqual(response.status_code, 302)

    @patch("database.is_admin_email")
    @patch("database.get_season")
    @patch("database.create_race")
    def test_add_race_with_auth(self, mock_create, mock_get_season, mock_is_admin):
        mock_is_admin.return_value = True
        mock_get_season.return_value = {"age_category_size": 5}

        with self.client.session_transaction() as sess:
            sess["user"] = {"email": "test@example.com"}

        response = self.client.post(
            "/add_race",
            data={"name": "Test Race", "date": "2024-01-01", "season": "2024 Season"},
        )
        self.assertEqual(response.status_code, 302)
        mock_create.assert_called_once_with(
            "2024 Season", "Test Race", {"date": "2024-01-01", "organising_clubs": []}
        )

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
        self.assertIn(b"Race Results", response.data)

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
        self.assertIn(b"Edit Club", response.data)
        self.assertIn(b"test_club", response.data)
        self.assertIn(b"TC", response.data)

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
        self.assertIn(b"Edit Participant", response.data)
        self.assertIn(b"John", response.data)

    @patch("database.is_admin_email")
    @patch("database.delete_participant")
    def test_delete_participant_with_auth(self, mock_delete_participant, mock_is_admin):
        mock_is_admin.return_value = True

        with self.client.session_transaction() as sess:
            sess["user"] = {"email": "test@example.com"}

        response = self.client.post("/delete_participant/A123456")
        self.assertEqual(response.status_code, 302)
        mock_delete_participant.assert_called_once()

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
    @patch("database.get_participants")
    def test_export_participants_with_auth(self, mock_get_participants, mock_is_admin):
        mock_is_admin.return_value = True
        mock_get_participants.return_value = {
            "participants": [
                {
                    "barcode": "A123456",
                    "first_name": "John",
                    "last_name": "Doe",
                    "gender": "Male",
                    "date_of_birth": "1990-01-01",
                    "club": "Test Club",
                }
            ]
        }

        with self.client.session_transaction() as sess:
            sess["user"] = {"email": "test@example.com"}

        response = self.client.get("/export_participants")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "text/csv")

    def test_export_participants_no_auth(self):
        response = self.client.get("/export_participants")
        self.assertEqual(response.status_code, 302)

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
        self.assertIn(b"Edit Season", response.data)

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
    @patch("database.delete_season")
    def test_delete_season_with_auth(self, mock_delete, mock_is_admin):
        mock_is_admin.return_value = True

        with self.client.session_transaction() as sess:
            sess["user"] = {"email": "test@example.com"}

        response = self.client.post("/delete_season/2024")
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

    @patch("database.is_admin_email")
    @patch("database.validate_barcode")
    @patch("database.club_exists")
    @patch("database.participant_exists")
    @patch("database.update_participant")
    def test_edit_participant_with_auth(
        self, mock_update, mock_exists, mock_club_exists, mock_validate, mock_is_admin
    ):
        mock_is_admin.return_value = True
        mock_validate.return_value = True
        mock_club_exists.return_value = True
        mock_exists.return_value = False

        with self.client.session_transaction() as sess:
            sess["user"] = {"email": "test@example.com"}

        data = {
            "first_name": "Jane",
            "last_name": "Doe",
            "gender": "F",
            "dob": "1990-01-01",
            "barcode": "A654321",
            "club": "Test Club",
        }
        response = self.client.post("/edit_participant/test_id", data=data)
        self.assertEqual(response.status_code, 302)

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
                # Missing barcode and position_token
            },
        )
        self.assertEqual(response.status_code, 302)

    def test_index_redirect(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 302)

    @patch("database.is_admin_email")
    @patch("database.get_participants")
    def test_participants_with_auth(self, mock_get_participants, mock_is_admin):
        mock_is_admin.return_value = True
        mock_get_participants.return_value = {
            "participants": [],
            "total_count": 0,
            "page": 1,
            "page_size": 50,
            "total_pages": 0,
        }

        with self.client.session_transaction() as sess:
            sess["user"] = {"email": "test@example.com"}

        response = self.client.get("/participants")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Registered Participants", response.data)

    @patch("database.is_admin_email")
    @patch("database.get_clubs")
    def test_clubs_with_auth(self, mock_get_clubs, mock_is_admin):
        mock_is_admin.return_value = True
        mock_get_clubs.return_value = [{"name": "Test Club", "short_names": ["TC"]}]

        with self.client.session_transaction() as sess:
            sess["user"] = {"email": "test@example.com"}

        response = self.client.get("/clubs")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Running Clubs", response.data)
        self.assertIn(b"Test Club", response.data)


if __name__ == "__main__":
    unittest.main()
