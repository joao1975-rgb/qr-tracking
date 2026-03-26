import unittest
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

class TestSecurityS5(unittest.TestCase):
    def test_s5_01_benchmark_pool_anonymity(self):
        response = client.get("/api/analytics/industry-benchmarks")
        if response.status_code == 200:
            data = response.json()
            if "pools" in data:
                for pool in data["pools"].values():
                    self.assertNotIn("client", pool, "Leak detected: client name in benchmark pool")
                    self.assertNotIn("campaign_code", pool, "Leak detected: campaign_code in benchmark pool")
                    self.assertNotIn("description", pool, "Leak detected: description in benchmark pool")

    def test_s5_02_vs_benchmark_no_competitor_details(self):
        # We will test if the /vs-benchmark endpoint leaks competitor data.
        response = client.get("/api/analytics/compare/vs-benchmark/TEST_01")
        if response.status_code == 200:
            data = response.json()
            self.assertEqual(data.get("success"), True)
            
            benchmark_data = data.get("benchmark", {})
            self.assertNotIn("client", benchmark_data, "Leak detected: client name in vs_benchmark")
            self.assertNotIn("campaign_code", benchmark_data, "Leak detected: campaign_code in vs_benchmark")

    def test_s5_03_available_comparisons_no_description(self):
        response = client.get("/api/analytics/compare/available/TEST_01")
        if response.status_code == 200:
            data = response.json()
            for item in data.get("available", []):
                self.assertNotIn("client", item, "Leak in available pool")

    def test_s5_04_ssot_benchmark_endpoint_pure(self):
        response = client.get("/api/admin/system/benchmarks")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        industries = data.get("industries", {})
        self.assertGreater(len(industries), 0, "No industries loaded in SSOT")
        for ind, vals in industries.items():
            self.assertNotIn("client", vals)
            self.assertNotIn("campaign_code", vals)

if __name__ == "__main__":
    unittest.main()
