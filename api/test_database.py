import unittest
from unittest.mock import Mock, patch
from database import (
    validate_barcode,
    get_all_clubs,
    club_exists,
    barcode_exists,
    create_participant,
    update_participant,
    get_participants,
    get_participant,
    get_clubs_ordered,
    add_club,
    soft_delete_participant,
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
        mock_club.to_dict.return_value = {"name": "Test Club"}
        mock_db.collection.return_value.get.return_value = [mock_club]

        result = get_all_clubs()
        self.assertEqual(result, ["Test Club"])

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
    def test_get_clubs_ordered(self, mock_db):
        mock_clubs = [Mock(), Mock()]
        mock_db.collection.return_value.order_by.return_value.get.return_value = (
            mock_clubs
        )

        result = get_clubs_ordered()

        mock_db.collection.assert_called_with("running_clubs")
        mock_db.collection.return_value.order_by.assert_called_with("name")
        self.assertEqual(result, mock_clubs)

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


if __name__ == "__main__":
    unittest.main()
