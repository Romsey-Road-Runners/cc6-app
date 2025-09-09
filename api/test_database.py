import unittest
from unittest.mock import Mock, patch

from database import (
    add_admin_email,
    add_club,
    add_race,
    add_race_results,
    add_season,
    barcode_exists,
    club_exists,
    create_participant,
    delete_race_result,
    get_admin_emails,
    get_all_clubs,
    get_all_races,
    get_all_seasons,
    get_all_seasons_with_ids,
    get_participant,
    get_participants,
    get_race_results,
    get_races_by_season,
    is_admin_email,
    remove_admin_email,
    season_exists,
    soft_delete_participant,
    update_participant,
    update_race_result_position,
    validate_barcode,
)


class TestDatabase(unittest.TestCase):

    def test_validate_barcode_valid(self):
        self.assertTrue(validate_barcode("A123456"))
        self.assertTrue(validate_barcode("A1234567"))
        self.assertTrue(validate_barcode("a123456"))

    def test_validate_barcode_invalid(self):
        self.assertFalse(validate_barcode("B123456"))
        self.assertFalse(validate_barcode("A12345"))
        self.assertFalse(validate_barcode("A12345678"))

    @patch("database.db")
    def test_get_all_clubs(self, mock_db):
        mock_club = Mock()
        mock_club.to_dict.return_value = {"name": "Test Club", "short_names": ["TC"]}
        mock_club.id = "club_id"
        mock_db.collection.return_value.order_by.return_value.get.return_value = [
            mock_club
        ]

        result = get_all_clubs()

        mock_db.collection.assert_called_with("running_clubs")
        mock_db.collection.return_value.order_by.assert_called_with("name")
        self.assertEqual(
            result, [{"id": "club_id", "name": "Test Club", "short_names": ["TC"]}]
        )

    @patch("database.db")
    def test_club_exists_true(self, mock_db):
        mock_db.collection.return_value.where.return_value.get.return_value = [Mock()]

        result = club_exists("Test Club")
        self.assertTrue(result)

    @patch("database.db")
    def test_club_exists_false(self, mock_db):
        mock_db.collection.return_value.where.return_value.get.return_value = []

        result = club_exists("Test Club")
        self.assertFalse(result)

    @patch("database.db")
    def test_barcode_exists_true(self, mock_db):
        mock_doc = Mock()
        mock_doc.id = "different_id"
        mock_db.collection.return_value.where.return_value.get.return_value = [mock_doc]

        result = barcode_exists("A123456", "test_id")
        self.assertTrue(result)

    @patch("database.db")
    def test_barcode_exists_false(self, mock_db):
        mock_db.collection.return_value.where.return_value.get.return_value = []

        result = barcode_exists("A123456")
        self.assertFalse(result)

    @patch("database.db")
    def test_create_participant(self, mock_db):
        data = {"first_name": "John", "last_name": "Doe"}
        create_participant(data)

        mock_db.collection.assert_called_with("participants")
        mock_db.collection.return_value.add.assert_called_once()

    @patch("database.db")
    def test_update_participant(self, mock_db):
        data = {"first_name": "Jane"}
        update_participant("test_id", data)

        mock_db.collection.return_value.document.assert_called_with("test_id")
        mock_db.collection.return_value.document.return_value.update.assert_called_with(
            data
        )

    @patch("database.db")
    def test_get_participants(self, mock_db):
        mock_participant = Mock()
        mock_participant.to_dict.return_value = {"first_name": "John", "deleted": False}
        mock_participant.id = "test_id"
        mock_db.collection.return_value.order_by.return_value.get.return_value = [
            mock_participant
        ]

        result = get_participants()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], "test_id")

    @patch("database.db")
    def test_get_participant(self, mock_db):
        mock_doc = Mock()
        mock_db.collection.return_value.document.return_value.get.return_value = (
            mock_doc
        )

        result = get_participant("test_id")

        mock_db.collection.assert_called_with("participants")
        mock_db.collection.return_value.document.assert_called_with("test_id")
        self.assertEqual(result, mock_doc)

    @patch("database.db")
    def test_add_club(self, mock_db):
        club_name = "New Club"
        add_club(club_name)

        mock_db.collection.assert_called_with("running_clubs")
        mock_db.collection.return_value.add.assert_called_with({"name": club_name})

    @patch("database.db")
    def test_soft_delete_participant(self, mock_db):
        soft_delete_participant("test_id")

        mock_db.collection.return_value.document.assert_called_with("test_id")
        mock_db.collection.return_value.document.return_value.update.assert_called_with(
            {"deleted": True}
        )

    @patch("database.db")
    def test_get_admin_emails(self, mock_db):
        mock_admin = Mock()
        mock_admin.to_dict.return_value = {"email": "admin@test.com"}
        mock_db.collection.return_value.get.return_value = [mock_admin]

        result = get_admin_emails()
        self.assertEqual(result, ["admin@test.com"])

    @patch("database.get_admin_emails")
    def test_is_admin_email_true(self, mock_get_admin_emails):
        mock_get_admin_emails.return_value = ["admin@test.com"]

        result = is_admin_email("admin@test.com")
        self.assertTrue(result)

    @patch("database.get_admin_emails")
    def test_is_admin_email_false(self, mock_get_admin_emails):
        mock_get_admin_emails.return_value = ["admin@test.com"]

        result = is_admin_email("user@test.com")
        self.assertFalse(result)

    @patch("database.db")
    def test_add_admin_email(self, mock_db):
        add_admin_email("new@test.com")

        mock_db.collection.assert_called_with("admin_emails")
        mock_db.collection.return_value.add.assert_called_with(
            {"email": "new@test.com"}
        )

    @patch("database.db")
    def test_remove_admin_email_success(self, mock_db):
        mock_doc = Mock()
        mock_doc.id = "test_id"
        mock_db.collection.return_value.where.return_value.get.return_value = [mock_doc]

        result = remove_admin_email("admin@test.com")

        self.assertTrue(result)
        mock_db.collection.return_value.document.assert_called_with("test_id")
        mock_db.collection.return_value.document.return_value.delete.assert_called_once()

    @patch("database.db")
    def test_remove_admin_email_not_found(self, mock_db):
        mock_db.collection.return_value.where.return_value.get.return_value = []

        result = remove_admin_email("nonexistent@test.com")

        self.assertFalse(result)

    @patch("database.db")
    def test_get_all_seasons(self, mock_db):
        mock_season = Mock()
        mock_season.to_dict.return_value = {"name": "2024 Season"}
        mock_db.collection.return_value.order_by.return_value.get.return_value = [
            mock_season
        ]

        result = get_all_seasons()

        mock_db.collection.assert_called_with("seasons")
        mock_db.collection.return_value.order_by.assert_called_with("name")
        self.assertEqual(result, ["2024 Season"])

    @patch("database.db")
    def test_season_exists_true(self, mock_db):
        mock_db.collection.return_value.where.return_value.get.return_value = [Mock()]

        result = season_exists("2024 Season")
        self.assertTrue(result)

    @patch("database.db")
    def test_season_exists_false(self, mock_db):
        mock_db.collection.return_value.where.return_value.get.return_value = []

        result = season_exists("2024 Season")
        self.assertFalse(result)

    @patch("database.db")
    def test_add_season(self, mock_db):
        season_name = "2024 Season"
        age_category_size = 5
        add_season(season_name, age_category_size)

        mock_db.collection.assert_called_with("seasons")
        mock_db.collection.return_value.add.assert_called_with(
            {"name": season_name, "age_category_size": age_category_size}
        )

    @patch("database.db")
    def test_get_all_races(self, mock_db):
        mock_race = Mock()
        mock_race.to_dict.return_value = {
            "name": "Test Race",
            "date": "2024-01-01",
            "season": "2024 Season",
        }
        mock_race.id = "race_id"
        mock_db.collection.return_value.order_by.return_value.get.return_value = [
            mock_race
        ]

        result = get_all_races()

        mock_db.collection.assert_called_with("races")
        mock_db.collection.return_value.order_by.assert_called_with("date")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], "race_id")
        self.assertEqual(result[0]["name"], "Test Race")

    @patch("database.db")
    def test_add_race(self, mock_db):
        add_race("Test Race", "2024-01-01", "2024 Season")

        mock_db.collection.assert_called_with("races")
        mock_db.collection.return_value.add.assert_called_with(
            {"name": "Test Race", "date": "2024-01-01", "season": "2024 Season"}
        )

    @patch("database.db")
    def test_add_race_results(self, mock_db):
        mock_batch = Mock()
        mock_db.batch.return_value = mock_batch

        results = [
            {"race_name": "Test Race", "barcode": "A123456", "position": "P0001"},
            {"race_name": "Test Race", "barcode": "A123457", "position": "P0002"},
        ]

        add_race_results(results)

        mock_db.batch.assert_called_once()
        self.assertEqual(mock_batch.set.call_count, 2)
        mock_batch.commit.assert_called_once()

    @patch("database.db")
    def test_get_race_results(self, mock_db):
        # Mock race results
        mock_result = Mock()
        mock_result.to_dict.return_value = {
            "race_name": "Test Race",
            "barcode": "A123456",
            "position": "P0001",
        }
        mock_result.id = "result_id"

        # Mock race data
        mock_race = Mock()
        mock_race.to_dict.return_value = {"name": "Test Race", "date": "2024-01-01"}

        # Mock participants
        mock_participant = Mock()
        mock_participant.to_dict.return_value = {
            "barcode": "A123456",
            "first_name": "John",
            "last_name": "Doe",
            "club": "Test Club",
            "date_of_birth": "1990-01-01",
            "gender": "Male",
            "deleted": False,
        }

        # Setup mock calls
        def mock_collection_side_effect(collection_name):
            mock_collection = Mock()
            if collection_name == "race_results":
                mock_collection.where.return_value.get.return_value = [mock_result]
            elif collection_name == "races":
                mock_collection.where.return_value.get.return_value = [mock_race]
            elif collection_name == "participants":
                mock_collection.get.return_value = [mock_participant]
            return mock_collection

        mock_db.collection.side_effect = mock_collection_side_effect

        result = get_race_results("Test Race")

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["barcode"], "A123456")
        self.assertEqual(result[0]["participant_name"], "John Doe")
        self.assertEqual(result[0]["club"], "Test Club")
        self.assertEqual(result[0]["gender"], "Male")
        self.assertEqual(result[0]["age_category"], "Senior")

    @patch("database.db")
    def test_get_all_seasons_with_ids(self, mock_db):
        mock_season = Mock()
        mock_season.to_dict.return_value = {"name": "2024 Season"}
        mock_season.id = "season_id"
        mock_db.collection.return_value.order_by.return_value.get.return_value = [
            mock_season
        ]

        result = get_all_seasons_with_ids()

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], "season_id")
        self.assertEqual(result[0]["name"], "2024 Season")

    @patch("database.db")
    def test_get_races_by_season(self, mock_db):
        # Mock season document
        mock_season_doc = Mock()
        mock_season_doc.exists = True
        mock_season_doc.to_dict.return_value = {"name": "2024 Season"}

        # Mock race
        mock_race = Mock()
        mock_race.to_dict.return_value = {
            "name": "Test Race",
            "date": "2024-01-01",
            "season": "2024 Season",
        }
        mock_race.id = "race_id"

        def mock_collection_side_effect(collection_name):
            mock_collection = Mock()
            if collection_name == "seasons":
                mock_collection.document.return_value.get.return_value = mock_season_doc
            elif collection_name == "races":
                mock_collection.where.return_value.get.return_value = [mock_race]
            return mock_collection

        mock_db.collection.side_effect = mock_collection_side_effect

        result = get_races_by_season("season_id")

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], "race_id")
        self.assertEqual(result[0]["name"], "Test Race")

    @patch("database.db")
    def test_get_races_by_season_not_found(self, mock_db):
        mock_season_doc = Mock()
        mock_season_doc.exists = False

        mock_db.collection.return_value.document.return_value.get.return_value = (
            mock_season_doc
        )

        result = get_races_by_season("nonexistent")
        self.assertEqual(result, [])

    @patch("database.db")
    def test_delete_race_result(self, mock_db):
        delete_race_result("result_id")

        mock_db.collection.assert_called_with("race_results")
        mock_db.collection.return_value.document.assert_called_with("result_id")
        mock_db.collection.return_value.document.return_value.delete.assert_called_once()

    @patch("database.db")
    def test_update_race_result_position(self, mock_db):
        update_race_result_position("result_id", "P0005")

        mock_db.collection.assert_called_with("race_results")
        mock_db.collection.return_value.document.assert_called_with("result_id")
        mock_db.collection.return_value.document.return_value.update.assert_called_with(
            {"position": "P0005"}
        )


if __name__ == "__main__":
    unittest.main()
