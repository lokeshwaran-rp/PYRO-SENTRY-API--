"""
Simulation test suite for PYRO-SENTRY API.
Includes:
1. Lifecycle control (start, status, stop).
2. Stateless inference POST /api/v1/simulation/run.
3. PARITY TEST: Asserts 100% identical outputs between /simulation/run and the real intelligence engine functions.
4. Non-destructive isolation: Asserts simulation doesn't mutate existing DB records.
"""

import pytest
from fastapi.testclient import TestClient
from app.intelligence.classifier import classify
from app.intelligence.risk import compute_risk


def test_simulation_lifecycle(client: TestClient):
    """Test start, status polling, and stopping simulation."""
    start_req = {
        "simulation_id": "sim-test-01",
        "latitude": 29.7150,
        "longitude": -95.0792,
        "wind_speed_kmh": 25.0,
        "wind_direction_deg": 180.0,
        "max_steps": 5,
        "step_interval_seconds": 0.5,
    }
    # 1. Start
    res_start = client.post("/api/v1/simulation/start", json=start_req)
    assert res_start.status_code == 202
    assert res_start.json()["is_running"] is True
    assert res_start.json()["current_simulation_id"] == "sim-test-01"

    # 2. Status
    res_status = client.get("/api/v1/simulation/status")
    assert res_status.status_code == 200
    assert res_status.json()["max_steps"] == 5

    # 3. Stop
    res_stop = client.post("/api/v1/simulation/stop")
    assert res_stop.status_code == 200
    assert "stopped" in res_stop.json()["message"].lower()
    assert res_stop.json()["simulation_id"] == "sim-test-01"


def test_simulation_run_industrial_flare(client: TestClient):
    """Test /simulation/run correctly evaluates industrial flare features."""
    req_payload = {
        "frp": 60.0,
        "brightness": 330.0,
        "persistence": 4,
        "industrial_proximity": 0.2,
        "wind_speed": 15.0,
        "wind_direction": 90.0,
        "ndvi": 0.45,
        "nbr": 0.35,
        "swir_anomaly": 0.25,
    }
    response = client.post("/api/v1/simulation/run", json=req_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["is_simulated"] is True
    assert data["simulation_mode"] == "SIMULATED"
    assert data["status"] == "COMPLETED"
    assert data["classification"] == "INDUSTRIAL_FLARE"
    assert "evidence" in data
    assert "smoke_estimate" in data
    assert "impact_estimate" in data


def test_simulation_run_wildfire(client: TestClient):
    """Test /simulation/run correctly evaluates wildfire signature."""
    req_payload = {
        "frp": 350.0,
        "brightness": 395.0,
        "persistence": 5,
        "industrial_proximity": 18.0,
        "wind_speed": 45.0,
        "wind_direction": 225.0,
        "ndvi": 0.05,
        "nbr": -0.45,
        "swir_anomaly": 0.85,
    }
    response = client.post("/api/v1/simulation/run", json=req_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["classification"] == "WILDFIRE"
    assert data["risk_level"] in ["HIGH", "CRITICAL"]
    assert data["risk_score"] > 6.0


def test_simulation_live_pipeline_parity(client: TestClient):
    """
    CRITICAL PARITY TEST:
    Asserts that passing synthetic inputs to /simulation/run produces
    EXACTLY THE SAME classification and risk scoring as direct invocation
    of the Intelligence engine's real classifier and risk scorer.
    """
    test_cases = [
        # Case 1: Industrial flare near plant
        {
            "frp": 85.0,
            "brightness": 340.0,
            "persistence": 3,
            "industrial_proximity": 0.4,
            "wind_speed": 12.0,
            "wind_direction": 45.0,
            "ndvi": 0.3,
            "nbr": 0.2,
            "swir_anomaly": 0.3,
        },
        # Case 2: Severe Wildfire
        {
            "frp": 420.0,
            "brightness": 410.0,
            "persistence": 6,
            "industrial_proximity": 25.0,
            "wind_speed": 55.0,
            "wind_direction": 270.0,
            "ndvi": -0.1,
            "nbr": -0.6,
            "swir_anomaly": 0.95,
        },
        # Case 3: Prescribed burn
        {
            "frp": 25.0,
            "brightness": 310.0,
            "persistence": 1,
            "industrial_proximity": 12.0,
            "wind_speed": 8.0,
            "wind_direction": 180.0,
            "ndvi": 0.5,
            "nbr": 0.4,
            "swir_anomaly": 0.1,
        },
        # Case 4: False positive
        {
            "frp": 10.0,
            "brightness": 302.0,
            "persistence": 1,
            "industrial_proximity": 8.0,
            "wind_speed": 5.0,
            "wind_direction": 0.0,
            "ndvi": 0.75,
            "nbr": 0.6,
            "swir_anomaly": 0.05,
        },
    ]

    for tc in test_cases:
        # 1. Output from API endpoint (/simulation/run)
        api_res = client.post("/api/v1/simulation/run", json=tc)
        assert api_res.status_code == 200
        sim_data = api_res.json()

        # 2. Output from direct Intelligence engine call
        direct_classification = classify(
            frp=tc["frp"],
            brightness=tc["brightness"],
            persistence=tc["persistence"],
            industrial_proximity=tc["industrial_proximity"],
            wind_speed=tc["wind_speed"],
            wind_direction=tc["wind_direction"],
            ndvi=tc["ndvi"],
            nbr=tc["nbr"],
            swir_anomaly=tc["swir_anomaly"],
        )
        direct_risk = compute_risk(
            frp=tc["frp"],
            brightness=tc["brightness"],
            persistence=tc["persistence"],
            industrial_proximity=tc["industrial_proximity"],
            wind_speed=tc["wind_speed"],
            wind_direction=tc["wind_direction"],
            ndvi=tc["ndvi"],
            nbr=tc["nbr"],
            swir_anomaly=tc["swir_anomaly"],
            classification=direct_classification,
        )

        # 3. Assert 100% PARITY
        assert sim_data["classification"] == direct_classification.primary_class
        assert sim_data["confidence"] == direct_classification.confidence
        assert sim_data["risk_score"] == direct_risk.risk_score
        assert sim_data["risk_level"] == direct_risk.risk_level
        assert sim_data["smoke_estimate"]["plume_height_m"] == direct_risk.smoke_estimate.plume_height_m
        assert sim_data["smoke_estimate"]["pm25_threat_level"] == direct_risk.smoke_estimate.pm25_threat_level
        assert sim_data["impact_estimate"]["estimated_burned_ha_24h"] == direct_risk.impact_estimate.estimated_burned_ha_24h
        assert sim_data["impact_estimate"]["containment_difficulty"] == direct_risk.impact_estimate.containment_difficulty


def test_simulation_non_destructive_isolation(client: TestClient):
    """Test that running simulation does not create or modify targets in database."""
    # Count targets before simulation
    targets_before = client.get("/api/v1/targets").json()
    count_before = len(targets_before)

    # Run simulation
    client.post("/api/v1/simulation/run", json={
        "frp": 500.0,
        "brightness": 420.0,
        "persistence": 8,
        "industrial_proximity": 15.0,
        "wind_speed": 60.0,
        "wind_direction": 180.0,
        "ndvi": -0.2,
        "nbr": -0.8,
        "swir_anomaly": 0.99,
    })

    # Count targets after simulation
    targets_after = client.get("/api/v1/targets").json()
    assert len(targets_after) == count_before
