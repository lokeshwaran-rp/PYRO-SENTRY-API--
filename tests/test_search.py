from fastapi.testclient import TestClient


def test_global_search_matching(client: TestClient):
    """Test global search with query matching targets and threats."""
    response = client.get("/api/v1/search?q=Angeles")
    assert response.status_code == 200
    data = response.json()
    assert data["query"] == "Angeles"
    assert data["total_results"] >= 1
    assert "results" in data
    assert "targets" in data["results"]


def test_global_search_assets(client: TestClient):
    """Test global search matching infrastructure asset."""
    response = client.get("/api/v1/search?q=Transmission")
    assert response.status_code == 200
    data = response.json()
    assert data["total_results"] >= 1
    assert len(data["results"]["assets"]) >= 1


def test_search_missing_param_validation(client: TestClient):
    """Test 422 validation error when query parameter 'q' is missing."""
    response = client.get("/api/v1/search")
    assert response.status_code == 422
