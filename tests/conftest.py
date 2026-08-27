"""
Test configuration and fixtures for PYRO-SENTRY API test suite.

Sets up:
1. In-memory async SQLite database with all tables created and populated with test seeds.
2. Dependency override for get_db so all endpoints use the isolated test database.
3. Test authentication tokens for ADMIN, OPERATOR, ANALYST, and VIEWER roles.
4. TestClient configured with authorization headers.
5. In-memory Redis mocking for pub/sub testing.
"""

import pytest
import pytest_asyncio
import uuid
from typing import AsyncGenerator, Generator
from datetime import datetime, timezone, timedelta

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db.base import Base
from app.db.session import get_db
from app.db.models import User, UserRole
from app.db.seed import seed_database
from app.auth.security import hash_password, create_access_token
from app.realtime.publisher import EventPublisher, publisher
from app.realtime.connection_manager import ConnectionManager

# In-memory SQLite async engine for tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


from contextlib import asynccontextmanager

@asynccontextmanager
async def _test_lifespan(app):
    yield

app.router.lifespan_context = _test_lifespan

# Precompute password hashes once for speed across tests
_ADMIN_HASH = hash_password("AdminPass123!")
_OPERATOR_HASH = hash_password("OperatorPass123!")
_ANALYST_HASH = hash_password("AnalystPass123!")
_VIEWER_HASH = hash_password("ViewerPass123!")

_tables_created = False


@pytest_asyncio.fixture(autouse=True)
async def init_test_db():
    """Create tables once, clean and reseed for every test."""
    global _tables_created
    if not _tables_created:
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        _tables_created = True

    async with TestingSessionLocal() as session:
        for table in reversed(Base.metadata.sorted_tables):
            await session.execute(table.delete())
        await session.commit()

        # Seed test users for each role
        users = [
            User(
                id="user-admin-01",
                email="admin@pyrosentry.io",
                username="admin_user",
                hashed_password=_ADMIN_HASH,
                role=UserRole.ADMIN,
                is_active=True,
            ),
            User(
                id="user-operator-01",
                email="operator@pyrosentry.io",
                username="operator_user",
                hashed_password=_OPERATOR_HASH,
                role=UserRole.OPERATOR,
                is_active=True,
            ),
            User(
                id="user-analyst-01",
                email="analyst@pyrosentry.io",
                username="analyst_user",
                hashed_password=_ANALYST_HASH,
                role=UserRole.ANALYST,
                is_active=True,
            ),
            User(
                id="user-viewer-01",
                email="viewer@pyrosentry.io",
                username="viewer_user",
                hashed_password=_VIEWER_HASH,
                role=UserRole.VIEWER,
                is_active=True,
            ),
        ]
        session.add_all(users)
        await session.commit()

        # Seed domain data
        await seed_database(session)

    yield


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency override providing a test DB session."""
    async with TestingSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture
def db_session_factory():
    """Returns the testing session maker for direct DB access in tests."""
    return TestingSessionLocal


@pytest.fixture
def admin_token() -> str:
    """JWT token for ADMIN role."""
    return create_access_token({"sub": "user-admin-01", "role": "ADMIN", "email": "admin@pyrosentry.io"})


@pytest.fixture
def operator_token() -> str:
    """JWT token for OPERATOR role."""
    return create_access_token({"sub": "user-operator-01", "role": "OPERATOR", "email": "operator@pyrosentry.io"})


@pytest.fixture
def analyst_token() -> str:
    """JWT token for ANALYST role."""
    return create_access_token({"sub": "user-analyst-01", "role": "ANALYST", "email": "analyst@pyrosentry.io"})


@pytest.fixture
def viewer_token() -> str:
    """JWT token for VIEWER role."""
    return create_access_token({"sub": "user-viewer-01", "role": "VIEWER", "email": "viewer@pyrosentry.io"})


@pytest.fixture
def client(operator_token: str) -> Generator[TestClient, None, None]:
    """Default authenticated TestClient (OPERATOR role)."""
    with TestClient(app) as c:
        c.headers.update({"Authorization": f"Bearer {operator_token}"})
        yield c


@pytest.fixture
def unauth_client() -> Generator[TestClient, None, None]:
    """Unauthenticated TestClient (no Bearer token)."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
def admin_client(admin_token: str) -> Generator[TestClient, None, None]:
    """Authenticated TestClient (ADMIN role)."""
    with TestClient(app) as c:
        c.headers.update({"Authorization": f"Bearer {admin_token}"})
        yield c


@pytest.fixture
def analyst_client(analyst_token: str) -> Generator[TestClient, None, None]:
    """Authenticated TestClient (ANALYST role)."""
    with TestClient(app) as c:
        c.headers.update({"Authorization": f"Bearer {analyst_token}"})
        yield c


@pytest.fixture
def viewer_client(viewer_token: str) -> Generator[TestClient, None, None]:
    """Authenticated TestClient (VIEWER role)."""
    with TestClient(app) as c:
        c.headers.update({"Authorization": f"Bearer {viewer_token}"})
        yield c
