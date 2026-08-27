import copy
from fastapi.testclient import TestClient


def test_simulation_run_wildfire_scenario(client: TestClient):
    """Test 1: Simulation works with valid wildfire inputs and returns simulated schema."""
    payload = {
        "frp": 120.5,
        "brightness": 385.0,
        "persistence": 3,
        "industrial_proximity": 5.0,
        "wind_speed": 28.0,
        "wind_direction": 45.0,
        "ndvi": 0.12,
        "nbr": -0.30,
        "swir_anomaly": 4.2,
    }

    response = client.post("/api/v1/simulation/run", json=payload)
    assert response.status_code == 200
    data = response.json()

    # Verify explicitly marked as simulated
    assert data["is_simulated"] is True
    assert data["simulation_mode"] == "SIMULATED"
    assert data["status"] == "COMPLETED"
    assert "simulation_timestamp" in data

    # Verify output classifications and metrics
    assert data["classification"] == "WILDFIRE"
    assert 0.0 <= data["confidence"] <= 1.0
    assert 0.0 <= data["risk_score"] <= 10.0
    assert data["risk_level"] in ["LOW", "MODERATE", "HIGH", "CRITICAL"]

    # Verify evidence items
    assert isinstance(data["evidence"], list)
    assert len(data["evidence"]) >= 1
    for item in data["evidence"]:
        assert "factor" in item
        assert "value" in item
        assert "impact" in item
        assert "weight" in item

    # Verify smoke estimate
    smoke = data["smoke_estimate"]
    assert "plume_height_m" in smoke
    assert smoke["dispersion_direction"] == payload["wind_direction"]
    assert "pm25_threat_level" in smoke
    assert "affected_radius_km" in smoke

    # Verify impact estimate
    impact = data["impact_estimate"]
    assert "estimated_burned_ha_24h" in impact
    assert "containment_difficulty" in impact
    assert "threatened_infrastructure_radius_km" in impact


def test_simulation_run_flare_scenario(client: TestClient):
    """Test simulation rule evaluating to industrial flare when close to industrial facility."""
    payload = {
        "frp": 35.0,
        "brightness": 330.0,
        "persistence": 1,
        "industrial_proximity": 0.2,  # very close to industrial facility
        "wind_speed": 8.0,
        "wind_direction": 180.0,
        "ndvi": 0.45,
        "nbr": 0.10,
        "swir_anomaly": 1.2,
    }

    response = client.post("/api/v1/simulation/run", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["is_simulated"] is True
    assert data["classification"] == "INDUSTRIAL_FLARE"


def test_simulation_run_invalid_inputs_rejected(client: TestClient):
    """Test 2: Invalid inputs are rejected with 422 Unprocessable Entity."""
    base_valid = {
        "frp": 50.0,
        "brightness": 320.0,
        "persistence": 1,
        "industrial_proximity": 2.0,
        "wind_speed": 10.0,
        "wind_direction": 90.0,
        "ndvi": 0.2,
        "nbr": 0.0,
        "swir_anomaly": 1.5,
    }

    # Case A: NDVI > 1.0
    bad_ndvi = copy.deepcopy(base_valid)
    bad_ndvi["ndvi"] = 2.5
    assert client.post("/api/v1/simulation/run", json=bad_ndvi).status_code == 422

    # Case B: NDVI < -1.0
    bad_ndvi_low = copy.deepcopy(base_valid)
    bad_ndvi_low["ndvi"] = -1.5
    assert client.post("/api/v1/simulation/run", json=bad_ndvi_low).status_code == 422

    # Case C: NBR > 1.0
    bad_nbr = copy.deepcopy(base_valid)
    bad_nbr["nbr"] = 1.8
    assert client.post("/api/v1/simulation/run", json=bad_nbr).status_code == 422

    # Case D: Negative FRP
    bad_frp = copy.deepcopy(base_valid)
    bad_frp["frp"] = -25.0
    assert client.post("/api/v1/simulation/run", json=bad_frp).status_code == 422

    # Case E: Brightness out of physical range (< 200K)
    bad_brightness = copy.deepcopy(base_valid)
    bad_brightness["brightness"] = 100.0
    assert client.post("/api/v1/simulation/run", json=bad_brightness).status_code == 422

    # Case F: Wind direction > 360 degrees
    bad_wind_dir = copy.deepcopy(base_valid)
    bad_wind_dir["wind_direction"] = 450.0
    assert client.post("/api/v1/simulation/run", json=bad_wind_dir).status_code == 422

    # Case G: Missing required field
    missing_field = copy.deepcopy(base_valid)
    del missing_field["swir_anomaly"]
    assert client.post("/api/v1/simulation/run", json=missing_field).status_code == 422


def test_simulation_does_not_modify_existing_data(client: TestClient):
    """Test 3: Proving simulation execution NEVER modifies existing targets, observations, or threats."""
    # 1. Capture snapshot of existing data before running simulations
    targets_before = client.get("/api/v1/targets").json()
    threats_before = client.get("/api/v1/threats").json()
    hotspots_before = client.get("/api/v1/hotspots").json()
    target_01_obs_before = client.get("/api/v1/targets/tgt-001/observations").json()
    target_01_risk_before = client.get("/api/v1/targets/tgt-001/risk").json()

    # 2. Run simulation calculations multiple times with different extreme values
    sim_inputs = [
        {
            "frp": 300.0,
            "brightness": 450.0,
            "persistence": 8,
            "industrial_proximity": 0.1,
            "wind_speed": 65.0,
            "wind_direction": 120.0,
            "ndvi": -0.5,
            "nbr": -0.8,
            "swir_anomaly": 9.5,
        },
        {
            "frp": 10.0,
            "brightness": 295.0,
            "persistence": 1,
            "industrial_proximity": 20.0,
            "wind_speed": 2.0,
            "wind_direction": 0.0,
            "ndvi": 0.8,
            "nbr": 0.5,
            "swir_anomaly": 0.1,
        },
    ]

    for sim_in in sim_inputs:
        resp = client.post("/api/v1/simulation/run", json=sim_in)
        assert resp.status_code == 200

    # 3. Capture snapshot of data after simulation runs
    targets_after = client.get("/api/v1/targets").json()
    threats_after = client.get("/api/v1/threats").json()
    hotspots_after = client.get("/api/v1/hotspots").json()
    target_01_obs_after = client.get("/api/v1/targets/tgt-001/observations").json()
    target_01_risk_after = client.get("/api/v1/targets/tgt-001/risk").json()

    # 4. Strict assertions: data before and after must be exactly identical
    assert targets_before == targets_after
    assert threats_before == threats_after
    assert hotspots_before == hotspots_after
    assert target_01_obs_before == target_01_obs_after
    assert target_01_risk_before == target_01_risk_after
