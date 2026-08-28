import unittest
import os
import json
from app import app
from database import init_db, create_agreement, get_agreement

class SahayakTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()
        init_db()

    def test_home_page_languages(self):
        # English
        resp_en = self.client.get('/?lang=en')
        self.assertEqual(resp_en.status_code, 200)
        self.assertIn(b'Create Wage Agreement', resp_en.data)

        # Hindi
        resp_hi = self.client.get('/?lang=hi')
        self.assertEqual(resp_hi.status_code, 200)
        self.assertIn('मजदूरी अनुबंध बनाएं'.encode('utf-8'), resp_hi.data)

        # Telugu
        resp_te = self.client.get('/?lang=te')
        self.assertEqual(resp_te.status_code, 200)
        self.assertIn('వేతన ఒప్పంద పత్రం'.encode('utf-8'), resp_te.data)
        self.assertIn('యజమాని'.encode('utf-8'), resp_te.data)
        self.assertIn('కార్మికుడు'.encode('utf-8'), resp_te.data)

    def test_create_and_view_agreement(self):
        payload = {
            "owner_name": "Rajesh Sharma",
            "owner_phone": "+91 9876543210",
            "worker_name": "Ram Prasad",
            "worker_phone": "+91 9123456780",
            "work_description": "Complete electrical wiring for 4-bedroom house and installation of switchboards",
            "wage_amount": "14500",
            "wage_unit": "per job",
            "payment_schedule": "installments",
            "late_penalty": "Rs. 250 per day late penalty",
            "start_date": "2026-09-01",
            "duration": "10 Days",
            "work_location": "House No 55, Civil Lines, Kanpur"
        }
        
        # Submit form
        response = self.client.post('/create', data=payload, follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        redirect_url = response.headers['Location']
        agreement_id = redirect_url.split('/')[-1].split('?')[0]
        self.assertTrue(len(agreement_id) > 20)

        # Check DB
        record = get_agreement(agreement_id)
        self.assertIsNotNone(record)
        self.assertEqual(record['owner_name'], "Rajesh Sharma")
        self.assertEqual(record['worker_name'], "Ram Prasad")
        self.assertEqual(record['wage_amount'], 14500.0)

        # View agreement page in Telugu
        view_resp_te = self.client.get(f'/agreement/{agreement_id}?lang=te')
        self.assertEqual(view_resp_te.status_code, 200)
        self.assertIn('ఒప్పందం విజయవంతంగా నమోదైంది'.encode('utf-8'), view_resp_te.data)
        self.assertIn(b'Rajesh Sharma', view_resp_te.data)
        self.assertIn(b'Ram Prasad', view_resp_te.data)

        # Verify page in Telugu
        verify_resp_te = self.client.get(f'/verify/{agreement_id}?lang=te')
        self.assertEqual(verify_resp_te.status_code, 200)
        self.assertIn('అధికారికంగా ధృవీకరించబడిన వేతన ఒప్పందం'.encode('utf-8'), verify_resp_te.data)
        self.assertIn(b'Ram Prasad', verify_resp_te.data)
        self.assertIn(b'Kanpur', verify_resp_te.data)

        # PDF download
        pdf_resp = self.client.get(f'/pdf/{agreement_id}?lang=te')
        self.assertEqual(pdf_resp.status_code, 200)
        self.assertEqual(pdf_resp.content_type, 'application/pdf')
        self.assertTrue(pdf_resp.data.startswith(b'%PDF'))
        self.assertGreater(len(pdf_resp.data), 2000)

        # API JSON check
        api_resp = self.client.get(f'/api/agreement/{agreement_id}')
        self.assertEqual(api_resp.status_code, 200)
        data = json.loads(api_resp.data)
        self.assertEqual(data['id'], agreement_id)
        self.assertEqual(data['wage_amount'], 14500.0)

    def test_nonexistent_agreement_404(self):
        resp = self.client.get('/verify/non-existent-uuid-12345?lang=te')
        self.assertEqual(resp.status_code, 404)
        self.assertIn('ఒప్పందం కనుగొనబడలేదు'.encode('utf-8'), resp.data)

if __name__ == '__main__':
    unittest.main()
