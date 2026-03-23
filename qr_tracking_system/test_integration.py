import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app import app
from fastapi.testclient import TestClient

def run_tests():
    print("Starting Integration Tests for v2.8 Implementation")
    client = TestClient(app)
    
    print("\\n[Test 1] Create Campaign with new v2.8 fields (POST /api/campaigns)")
    payload = {
        "campaign_code": "TEST_INTEGRATION_01",
        "client": "TEST_CORPORATION",
        "destination": "https://example.com/tracking",
        "description": "Integration test campaign",
        "active": True,
        "product_name": "Test Product v2.8",
        "start_date": "2026-03-21",
        "end_date": "2026-04-21",
        "campaign_status": "active",
        "campaign_phase": "launch",
        "industry": "electronica_tecnologia",
        "industry_sub": "software",
        "geo_country": "CL",
        "is_benchmark_eligible": True,
        "campaign_type": "branding",
        "budget_currency": "USD"
    }
    
    response = client.post("/api/campaigns", json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    assert response.status_code == 200, "Failed to create campaign"

    # print("\\n[Test 2] Update Campaign with new v2.8 fields (PUT /api/campaigns/{campaign_code})")
    # update_payload = {
    #     "budget_currency": "EUR",
    #     "campaign_objective": "awareness"
    # }
    # resp_update = client.put("/api/campaigns/TEST_INTEGRATION_01", json=update_payload)
    # print(f"Status: {resp_update.status_code}")
    # print(f"Response: {resp_update.text}")
    # assert resp_update.status_code == 200, "Failed to update campaign"
    
    print("\\n[Test 3] Retrieve Industry Benchmarks (GET /api/analytics/industry-benchmarks)")
    resp_bench = client.get("/api/analytics/industry-benchmarks")
    print(f"Status: {resp_bench.status_code}")
    print(f"Response: {resp_bench.text[:200]}...") # truncate if too long
    assert resp_bench.status_code == 200, "Failed to retrieve benchmarks"
    
    print("\\n[Test 4] Compare vs Benchmark (GET /api/analytics/compare/vs-benchmark/TEST_INTEGRATION_01)")
    resp_comp = client.get("/api/analytics/compare/vs-benchmark/TEST_INTEGRATION_01")
    print(f"Status: {resp_comp.status_code}")
    print(f"Response: {resp_comp.text}")
    assert resp_comp.status_code == 200, "Failed to compare vs benchmark"
    
    print("\\n[Test 5] Get Available for Comparison (GET /api/analytics/compare/available/TEST_INTEGRATION_01)")
    resp_avail = client.get("/api/analytics/compare/available/TEST_INTEGRATION_01")
    print(f"Status: {resp_avail.status_code}")
    print(f"Response: {resp_avail.text[:200]}...")
    assert resp_avail.status_code == 200, "Failed to get available comparisons"

    print("\\nCleanup: Deleting test campaign")
    import psycopg2
    from database import get_db_connection
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM campaigns WHERE campaign_code = 'TEST_INTEGRATION_01'")
        conn.commit()
    print("Cleanup successful.")

    print("\\n*** ALL TESTS PASSED SUCCESSFULLY ***")

if __name__ == "__main__":
    run_tests()
