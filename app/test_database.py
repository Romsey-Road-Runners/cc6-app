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

    def test_calculate_age_category(self):
        # Test Senior category
        self.assertEqual(database.calculate_age_category(25, "Male"), "Senior")
        self.assertEqual(database.calculate_age_category(39, "Female"), "Senior")

        # Test V40 category
        self.assertEqual(database.calculate_age_category(40, "Male"), "V40")
        self.assertEqual(database.calculate_age_category(44, "Female"), "V40")

        # Test V45 category
        self.assertEqual(database.calculate_age_category(45, "Male"), "V45")

        # Test V80+ category
        self.assertEqual(database.calculate_age_category(85, "Male"), "V80")

        # Test with different category size
        self.assertEqual(database.calculate_age_category(45, "Male", 10), "V40")
        self.assertEqual(database.calculate_age_category(55, "Male", 10), "V50")

    @patch("database.db")
    @patch("database.firestore")
    def test_get_default_season(self, mock_firestore, mock_db):
        mock_season = Mock()
        mock_season.id = "2024 Season"
        mock_db.collection.return_value.where.return_value.get.return_value = [
            mock_season
        ]

        result = database.get_default_season()
        self.assertEqual(result, "2024 Season")

        mock_db.collection.assert_called_with("season")
        mock_firestore.FieldFilter.assert_called_with("is_default", "==", True)

    @patch("database.db")
    @patch("database.firestore")
    def test_get_default_season_none(self, mock_firestore, mock_db):
        mock_db.collection.return_value.where.return_value.get.return_value = []

        result = database.get_default_season()
        self.assertIsNone(result)

    @patch("database.db")
    def test_clear_default_seasons(self, mock_db):
        mock_season = Mock()
        mock_season.reference = Mock()
        mock_db.collection.return_value.where.return_value.get.return_value = [
            mock_season
        ]
        mock_batch = Mock()
        mock_db.batch.return_value = mock_batch

        database.clear_default_seasons()

        mock_batch.update.assert_called_with(
            mock_season.reference, {"is_default": False}
        )
        mock_batch.commit.assert_called_once()

    @patch("database.db")
    def test_get_season(self, mock_db):
        mock_doc = Mock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {"age_category_size": 5, "is_default": True}
        mock_db.collection.return_value.document.return_value.get.return_value = (
            mock_doc
        )

        result = database.get_season("2024 Season")
        self.assertEqual(result["age_category_size"], 5)
        self.assertTrue(result["is_default"])

    @patch("database.db")
    def test_get_season_not_found(self, mock_db):
        mock_doc = Mock()
        mock_doc.exists = False
        mock_db.collection.return_value.document.return_value.get.return_value = (
            mock_doc
        )

        result = database.get_season("Nonexistent Season")
        self.assertIsNone(result)

    @patch("database.db")
    def test_update_season(self, mock_db):
        data = {"age_category_size": 10, "is_default": True}
        database.update_season("2024 Season", data)

        mock_db.collection.return_value.document.assert_called_with("2024 Season")
        mock_db.collection.return_value.document.return_value.update.assert_called_with(
            data
        )

    @patch("database.db")
    def test_delete_season(self, mock_db):
        database.delete_season("2024 Season")

        mock_db.collection.return_value.document.assert_called_with("2024 Season")
        mock_db.collection.return_value.document.return_value.delete.assert_called_once()

    @patch("database.db")
    def test_get_club(self, mock_db):
        mock_doc = Mock()
        mock_db.collection.return_value.document.return_value.get.return_value = (
            mock_doc
        )

        result = database.get_club("Test Club")
        self.assertEqual(result, mock_doc)

    @patch("database.db")
    def test_update_club(self, mock_db):
        data = {"short_names": ["TC", "Test"]}
        database.update_club("Test Club", data)

        mock_db.collection.return_value.document.return_value.update.assert_called_with(
            data
        )

    @patch("database.db")
    def test_delete_club(self, mock_db):
        database.delete_club("Test Club")

        mock_db.collection.return_value.document.return_value.delete.assert_called_once()

    @patch("database.db")
    def test_add_race_result(self, mock_db):
        participant_data = {"first_name": "John", "last_name": "Doe"}
        database.add_race_result("2024 Season", "Test Race", "1", participant_data)

        mock_db.collection.assert_called_with("season")

    @patch("database.db")
    def test_delete_all_race_results(self, mock_db):
        mock_result = Mock()
        mock_result.reference = Mock()
        mock_db.collection.return_value.document.return_value.collection.return_value.document.return_value.collection.return_value.get.return_value = [
            mock_result
        ]
        mock_batch = Mock()
        mock_db.batch.return_value = mock_batch

        database.delete_all_race_results("2024 Season", "Test Race")

        mock_batch.delete.assert_called_with(mock_result.reference)
        mock_batch.commit.assert_called_once()

    @patch("database.db")
    def test_add_race_results_batch(self, mock_db):
        results_data = [
            {"finish_token": "1", "participant": {"first_name": "John"}},
            {"finish_token": "2", "participant": {"first_name": "Jane"}},
        ]
        mock_batch = Mock()
        mock_db.batch.return_value = mock_batch

        database.add_race_results_batch("2024 Season", "Test Race", results_data)

        self.assertEqual(mock_batch.set.call_count, 2)
        mock_batch.commit.assert_called_once()

    @patch("database.db")
    def test_process_participants_batch(self, mock_db):
        new_participants = [
            {"barcode": "A123456", "first_name": "John", "last_name": "Doe"}
        ]
        updated_participants = [
            ("A654321", {"first_name": "Jane", "last_name": "Smith"})
        ]
        mock_batch = Mock()
        mock_db.batch.return_value = mock_batch

        database.process_participants_batch(new_participants, updated_participants)

        self.assertEqual(mock_batch.set.call_count, 1)
        self.assertEqual(mock_batch.update.call_count, 1)
        self.assertEqual(mock_batch.commit.call_count, 2)

    @patch("database.db")
    def test_init_running_clubs_empty(self, mock_db):
        mock_db.collection.return_value.get.return_value = []
        mock_batch = Mock()
        mock_db.batch.return_value = mock_batch

        database.init_running_clubs()

        self.assertTrue(mock_batch.set.called)
        mock_batch.commit.assert_called_once()

    @patch("database.db")
    def test_init_running_clubs_existing(self, mock_db):
        mock_club = Mock()
        mock_db.collection.return_value.get.return_value = [mock_club]

        database.init_running_clubs()

        mock_db.batch.assert_not_called()

    @patch("database.db")
    def test_init_admin_emails_empty(self, mock_db):
        mock_db.collection.return_value.get.return_value = []

        database.init_admin_emails()

        mock_db.collection.return_value.document.assert_called_with(
            "weston.sam@gmail.com"
        )

    @patch("database.db")
    def test_init_admin_emails_existing(self, mock_db):
        mock_admin = Mock()
        mock_db.collection.return_value.get.return_value = [mock_admin]

        database.init_admin_emails()

        mock_db.collection.return_value.document.assert_not_called()


if __name__ == "__main__":
    unittest.main()
