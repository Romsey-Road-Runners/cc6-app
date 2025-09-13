import unittest
from unittest.mock import Mock, patch

import database


class TestDatabase(unittest.TestCase):

    def test_validate_barcode_valid(self):
        self.assertTrue(database.validate_barcode("A12"))
        self.assertTrue(database.validate_barcode("A1234567"))
        self.assertTrue(database.validate_barcode("a123456"))

    def test_validate_barcode_invalid(self):
        self.assertFalse(database.validate_barcode("B123456"))
        self.assertFalse(database.validate_barcode("A1"))
        self.assertFalse(database.validate_barcode("A12345678123"))

    @patch("database.db")
    def test_get_clubs(self, mock_db):
        mock_club = Mock()
        mock_club.to_dict.return_value = {"short_names": ["TC"]}
        mock_club.id = "Test Club"
        mock_db.collection.return_value.order_by.return_value.get.return_value = [
            mock_club
        ]

        result = database.get_clubs()

        mock_db.collection.assert_called_with("clubs")
        self.assertEqual(result, [{"name": "Test Club", "short_names": ["TC"]}])

    @patch("database.db")
    def test_club_exists_true(self, mock_db):
        mock_doc = Mock()
        mock_doc.exists = True
        mock_db.collection.return_value.document.return_value.get.return_value = (
            mock_doc
        )

        result = database.club_exists("Test Club")
        self.assertTrue(result)

    @patch("database.db")
    def test_club_exists_false(self, mock_db):
        mock_doc = Mock()
        mock_doc.exists = False
        mock_db.collection.return_value.document.return_value.get.return_value = (
            mock_doc
        )

        result = database.club_exists("Test Club")
        self.assertFalse(result)

    @patch("database.db")
    def test_participant_exists_true(self, mock_db):
        mock_doc = Mock()
        mock_doc.exists = True
        mock_db.collection.return_value.document.return_value.get.return_value = (
            mock_doc
        )

        result = database.participant_exists("A123456")
        self.assertTrue(result)

    @patch("database.db")
    def test_participant_exists_false(self, mock_db):
        mock_doc = Mock()
        mock_doc.exists = False
        mock_db.collection.return_value.document.return_value.get.return_value = (
            mock_doc
        )

        result = database.participant_exists("A123456")
        self.assertFalse(result)

    @patch("database.db")
    def test_create_participant(self, mock_db):
        data = {"first_name": "John", "last_name": "Doe"}
        database.create_participant("A123456", data)

        mock_db.collection.assert_called_with("participants")
        mock_db.collection.return_value.document.assert_called_with("A123456")

    @patch("database.db")
    def test_update_participant(self, mock_db):
        data = {"first_name": "Jane"}
        database.update_participant("A123456", data)

        mock_db.collection.return_value.document.assert_called_with("A123456")
        mock_db.collection.return_value.document.return_value.update.assert_called_with(
            data
        )

    @patch("database.db")
    def test_get_participants(self, mock_db):
        mock_participant = Mock()
        mock_participant.to_dict.return_value = {"first_name": "John"}
        mock_participant.id = "A123456"
        mock_db.collection.return_value.get.return_value = [mock_participant]

        result = database.get_participants()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["barcode"], "A123456")

    @patch("database.db")
    def test_get_participant(self, mock_db):
        mock_doc = Mock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {"first_name": "John"}
        mock_doc.id = "A123456"
        mock_db.collection.return_value.document.return_value.get.return_value = (
            mock_doc
        )

        result = database.get_participant("A123456")

        mock_db.collection.assert_called_with("participants")
        mock_db.collection.return_value.document.assert_called_with("A123456")
        self.assertEqual(result["barcode"], "A123456")

    @patch("database.db")
    def test_add_club(self, mock_db):
        club_name = "New Club"
        database.add_club(club_name)

        mock_db.collection.assert_called_with("clubs")
        mock_db.collection.return_value.document.assert_called_with(club_name)

    @patch("database.db")
    def test_delete_participant(self, mock_db):
        database.delete_participant("A123456")

        mock_db.collection.return_value.document.assert_called_with("A123456")
        mock_db.collection.return_value.document.return_value.delete.assert_called_once()

    @patch("database.db")
    def test_get_admin_emails(self, mock_db):
        mock_admin = Mock()
        mock_admin.id = "admin@test.com"
        mock_db.collection.return_value.get.return_value = [mock_admin]

        result = database.get_admin_emails()
        self.assertEqual(result, ["admin@test.com"])

    @patch("database.db")
    def test_is_admin_email_true(self, mock_db):
        mock_doc = Mock()
        mock_doc.exists = True
        mock_db.collection.return_value.document.return_value.get.return_value = (
            mock_doc
        )

        result = database.is_admin_email("admin@test.com")
        self.assertTrue(result)

    @patch("database.db")
    def test_is_admin_email_false(self, mock_db):
        mock_doc = Mock()
        mock_doc.exists = False
        mock_db.collection.return_value.document.return_value.get.return_value = (
            mock_doc
        )

        result = database.is_admin_email("user@test.com")
        self.assertFalse(result)

    @patch("database.db")
    def test_add_admin_email(self, mock_db):
        database.add_admin_email("new@test.com")

        mock_db.collection.assert_called_with("admin_emails")
        mock_db.collection.return_value.document.assert_called_with("new@test.com")

    @patch("database.db")
    def test_remove_admin_email(self, mock_db):
        database.remove_admin_email("admin@test.com")

        mock_db.collection.return_value.document.assert_called_with("admin@test.com")
        mock_db.collection.return_value.document.return_value.delete.assert_called_once()

    @patch("database.db")
    def test_get_seasons(self, mock_db):
        mock_season = Mock()
        mock_season.id = "2024 Season"
        mock_db.collection.return_value.order_by.return_value.get.return_value = [
            mock_season
        ]

        result = database.get_seasons()

        mock_db.collection.assert_called_with("season")
        self.assertEqual(result, ["2024 Season"])

    @patch("database.db")
    def test_create_season(self, mock_db):
        season_name = "2024 Season"
        age_category_size = 5
        database.create_season(season_name, age_category_size)

        mock_db.collection.assert_called_with("season")
        mock_db.collection.return_value.document.assert_called_with(season_name)

    @patch("database.db")
    def test_create_race(self, mock_db):
        database.create_race("2024 Season", "Test Race", {"date": "2024-01-01"})

        mock_db.collection.assert_called_with("season")

    @patch("database.db")
    def test_get_race_results(self, mock_db):
        mock_result = Mock()
        mock_result.to_dict.return_value = {
            "participant": {"first_name": "John", "last_name": "Doe"}
        }
        mock_result.id = "1"

        mock_db.collection.return_value.document.return_value.collection.return_value.document.return_value.collection.return_value.get.return_value = [
            mock_result
        ]

        result = database.get_race_results("2024 Season", "Test Race")

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["finish_token"], "1")

    @patch("database.db")
    def test_get_races_by_season(self, mock_db):
        mock_race = Mock()
        mock_race.to_dict.return_value = {
            "date": "2024-01-01",
            "organising_clubs": ["Test Club"],
        }
        mock_race.id = "Test Race"

        mock_db.collection.return_value.document.return_value.collection.return_value.get.return_value = [
            mock_race
        ]

        result = database.get_races_by_season("2024 Season")

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["name"], "Test Race")

    @patch("database.db")
    def test_delete_race_result(self, mock_db):
        database.delete_race_result("2024 Season", "Test Race", "1")

        mock_db.collection.assert_called_with("season")

    def test_validate_and_normalize_club(self):
        clubs = [
            {"name": "Test Club", "short_names": ["TC", "Test"]},
            {"name": "Another Club", "short_names": ["AC"]},
        ]

        # Test exact match
        result = database.validate_and_normalize_club("Test Club", clubs)
        self.assertEqual(result, "Test Club")

        # Test short name match
        result = database.validate_and_normalize_club("TC", clubs)
        self.assertEqual(result, "Test Club")

        # Test no match
        result = database.validate_and_normalize_club("Unknown Club", clubs)
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
