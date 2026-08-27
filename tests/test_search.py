"""
Global search API test suite for PYRO-SENTRY.
"""

import pytest
from fastapi.testclient import TestClient


def test_global_search_matching_query(client: TestClient):
    """Test searching with keyword matching targets, threats, or assets."""
    response = client.get("/api/v1/search?q=Refinery")
    assert response.status_code == 200
    data = response.json()
    assert data["query"] == "Refinery"
    assert data["total_results"] >= 1
    assert "results" in data
    assert len(data["results"]["targets"]) >= 1 or len(data["results"]["assets"]) >= 1


def test_global_search_empty_results(client: TestClient):
    """Test searching with no matching results."""
    response = client.get("/api/v1/search?q=xyznonexistentterm999")
    assert response.status_code == 200
    data = response.json()
    assert data["total_results"] == 0
    assert len(data["results"]["targets"]) == 0
