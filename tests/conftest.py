import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    """Provides a TestClient instance for REST API tests."""
    with TestClient(app) as c:
        yield c
