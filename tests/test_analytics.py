"""
Analytics API test suite for PYRO-SENTRY.
Tests DB aggregations, trends, and breakdowns on /api/v1/analytics.
"""

import pytest
from fastapi.testclient import TestClient


def test_analytics_summary(client: TestClient):
    """Test retrieving high-level analytics summary."""
    response = client.get("/api/v1/analytics/summary")
    assert response.status_code == 200
    data = response.json()
    assert "total_hotspots_detected_24h" in data
    assert "active_targets_count" in data
    assert "average_confidence_pct" in data
    assert "critical_threats_count" in data
    assert "total_estimated_burned_ha" in data
    assert "highest_frp_mw" in data
    assert "last_updated" in data


def test_frp_trends(client: TestClient):
    """Test retrieving FRP time-series trends."""
    response = client.get("/api/v1/analytics/frp-trends")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert "timestamp" in data[0]
    assert "total_frp_mw" in data[0]
    assert "hotspots_count" in data[0]


def test_classification_distribution(client: TestClient):
    """Test retrieving classification breakdown dictionary."""
    response = client.get("/api/v1/analytics/classification-distribution")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert len(data) >= 1


def test_hourly_activity(client: TestClient):
    """Test retrieving 24-hour diurnal activity breakdown."""
    response = client.get("/api/v1/analytics/hourly-activity")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert "hour_utc" in data[0]
    assert "detections" in data[0]
