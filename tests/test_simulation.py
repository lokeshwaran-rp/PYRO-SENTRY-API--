import time
from fastapi.testclient import TestClient


def test_simulation_lifecycle(client: TestClient):
    """Test starting, checking status, and stopping a simulation."""
    # 1. Check initial status
    status_resp = client.get("/api/v1/simulation/status")
    assert status_resp.status_code == 200
    
    # 2. Start simulation with short step interval
    start_payload = {
        "simulation_id": "test-sim-01",
        "latitude": 34.0522,
        "longitude": -118.2437,
        "wind_speed_kmh": 20.0,
        "wind_direction_deg": 90.0,
        "max_steps": 5,
        "step_interval_seconds": 0.2,
    }
    start_resp = client.post("/api/v1/simulation/start", json=start_payload)
    assert start_resp.status_code == 202
    start_data = start_resp.json()
    assert start_data["is_running"] is True
    assert start_data["current_simulation_id"] == "test-sim-01"

    # Give simulation a brief moment to run a step
    time.sleep(0.5)

    # 3. Check status during or right after run
    status_after = client.get("/api/v1/simulation/status")
    assert status_after.status_code == 200
    status_data = status_after.json()
    assert status_data["max_steps"] == 5

    # 4. Stop simulation
    stop_resp = client.post("/api/v1/simulation/stop")
    assert stop_resp.status_code == 200
    stop_data = stop_resp.json()
    assert "Simulation stopped successfully" in stop_data["message"]
