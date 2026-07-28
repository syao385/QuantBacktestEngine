import unittest
from fastapi.testclient import TestClient
from quant_engine.server.app import app

class TestAPIServer(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)

    def test_healthcheck(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")
        self.assertIn("version", data)

    def test_save_and_list_strategies_api(self):
        spec = {
            "name": "API_Test_Strategy",
            "version": "1.0.0",
            "indicators": {"ema_fast": {"type": "EMA", "period": 5}}
        }
        res_save = self.client.post("/api/strategies", json={
            "name": "API_Test_Strategy",
            "version": "1.0.0",
            "spec": spec,
            "description": "API Test"
        })
        self.assertEqual(res_save.status_code, 200)

        res_list = self.client.get("/api/strategies")
        self.assertEqual(res_list.status_code, 200)
        data = res_list.json()
        self.assertIn("strategies", data)

if __name__ == "__main__":
    unittest.main()
