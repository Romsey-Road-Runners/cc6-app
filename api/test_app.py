import unittest
from unittest.mock import Mock, patch
import os

# Mock Google Cloud before importing app
with patch('google.cloud.firestore.Client'):
    from app import app, validate_barcode, get_club_id_by_name


class TestApp(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()

    def test_validate_barcode_valid(self):
        self.assertTrue(validate_barcode('A123456'))
        self.assertTrue(validate_barcode('A1234567'))
        self.assertTrue(validate_barcode('a123456'))

    def test_validate_barcode_invalid(self):
        self.assertFalse(validate_barcode('B123456'))
        self.assertFalse(validate_barcode('A12345'))
        self.assertFalse(validate_barcode('A12345678'))
        self.assertFalse(validate_barcode('123456'))

    def test_index_route(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    @patch('app.db')
    def test_get_clubs_api(self, mock_db):
        mock_club = Mock()
        mock_club.to_dict.return_value = {'name': 'Test Club'}
        mock_db.collection.return_value.get.return_value = [mock_club]
        
        response = self.client.get('/api/clubs')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, ['Test Club'])

    @patch('app.db')
    def test_get_club_id_by_name(self, mock_db):
        mock_doc = Mock()
        mock_doc.id = 'test_id'
        mock_db.collection.return_value.where.return_value.get.return_value = [mock_doc]
        
        result = get_club_id_by_name('Test Club')
        self.assertEqual(result, 'test_id')

    def test_participants_requires_login(self):
        response = self.client.get('/participants')
        self.assertEqual(response.status_code, 302)

    def test_clubs_requires_login(self):
        response = self.client.get('/clubs')
        self.assertEqual(response.status_code, 302)

    def test_register_missing_fields(self):
        response = self.client.post('/register', data={})
        self.assertEqual(response.status_code, 302)


if __name__ == '__main__':
    unittest.main()