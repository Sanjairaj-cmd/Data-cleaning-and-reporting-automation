import os
import sys
import json
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from database import init_db

class TestAutoCleanProAPI(unittest.TestCase):

    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()
        init_db()

    def test_index_route(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'AutoCleanPro', response.data)

    def test_upload_sample(self):
        response = self.client.post('/api/upload', data={'sample_name': 'sample_customer_churn.csv'})
        if response.status_code != 200:
            print("ERROR RESPONSE DATA:", response.data.decode('utf-8'))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('session_id', data)
        self.assertIn('raw_analysis', data)
        self.assertIn('summary_statistics', data)
        self.assertIn('preview_data', data)
        self.assertGreater(data['total_rows'], 0)

        # Test Clean route
        session_id = data['session_id']
        clean_response = self.client.post('/api/clean', json={
            'session_id': session_id,
            'mode': 'auto'
        })
        self.assertEqual(clean_response.status_code, 200)
        clean_data = json.loads(clean_response.data)
        self.assertIn('download_urls', clean_data)
        self.assertGreaterEqual(clean_data['cleaned_analysis']['summary']['quality_score'], data['raw_analysis']['summary']['quality_score'])

        # Test Download Cleaned CSV
        csv_response = self.client.get(f"/download/cleaned/{session_id}?file_format=csv")
        self.assertEqual(csv_response.status_code, 200)

        # Test Download PDF
        pdf_response = self.client.get(f"/download/pdf/{session_id}")
        self.assertEqual(pdf_response.status_code, 200)

        # Test History API
        history_response = self.client.get('/api/history')
        self.assertEqual(history_response.status_code, 200)
        hist_data = json.loads(history_response.data)
        self.assertGreater(len(hist_data['history']), 0)

if __name__ == '__main__':
    unittest.main()
