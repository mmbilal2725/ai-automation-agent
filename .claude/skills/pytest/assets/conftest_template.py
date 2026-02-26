"""
Shared test fixtures and configuration.

This conftest.py file provides common fixtures used across all tests.
Customize based on your project's needs.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Uncomment and adjust imports based on your project structure
# from myapp.main import app
# from myapp.database import Base, get_db
# from myapp.config import Settings


# ============================================================================
# Configuration Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def test_settings():
    """Test-specific application settings."""
    return {
        "database_url": "sqlite:///./test.db",
        "testing": True,
        "secret_key": "test-secret-key"
    }


# ============================================================================
# Database Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def engine(test_settings):
    """Create test database engine."""
    # Uncomment and adjust for your database
    # engine = create_engine(
    #     test_settings["database_url"],
    #     connect_args={"check_same_thread": False}  # SQLite only
    # )
    # Base.metadata.create_all(bind=engine)
    # yield engine
    # Base.metadata.drop_all(bind=engine)
    pass


@pytest.fixture(scope="function")
def db_session(engine):
    """Create a fresh database session for each test."""
    # Uncomment and adjust for your database
    # TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    # Base.metadata.create_all(bind=engine)
    # session = TestingSessionLocal()
    # try:
    #     yield session
    # finally:
    #     session.close()
    #     Base.metadata.drop_all(bind=engine)
    pass


@pytest.fixture(autouse=True)
def override_get_db(db_session):
    """Override the get_db dependency for all tests."""
    # Uncomment and adjust for your app
    # def _override():
    #     try:
    #         yield db_session
    #     finally:
    #         db_session.close()
    # app.dependency_overrides[get_db] = _override
    # yield
    # app.dependency_overrides.clear()
    pass


# ============================================================================
# FastAPI Client Fixtures
# ============================================================================

@pytest.fixture(scope="module")
def client():
    """TestClient for FastAPI application."""
    # Uncomment and adjust import
    # with TestClient(app) as c:
    #     yield c
    pass


@pytest.fixture
def authenticated_client(client, db_session):
    """Client with authenticated user."""
    # Uncomment and customize authentication logic
    # from myapp.dependencies import get_current_user
    #
    # def override_get_current_user():
    #     return {"id": 1, "username": "testuser", "email": "test@example.com"}
    #
    # app.dependency_overrides[get_current_user] = override_get_current_user
    # yield client
    # app.dependency_overrides.clear()
    pass


@pytest.fixture
def admin_client(client, db_session):
    """Client with admin user authentication."""
    # Uncomment and customize
    # from myapp.dependencies import get_current_user
    #
    # def override_get_current_user():
    #     return {
    #         "id": 1,
    #         "username": "admin",
    #         "email": "admin@example.com",
    #         "is_admin": True
    #     }
    #
    # app.dependency_overrides[get_current_user] = override_get_current_user
    # yield client
    # app.dependency_overrides.clear()
    pass


# ============================================================================
# Test Data Factories
# ============================================================================

@pytest.fixture
def make_user(db_session):
    """Factory fixture for creating test users."""
    # Uncomment and adjust for your User model
    # from myapp.models import User
    # from myapp.auth import get_password_hash
    #
    # def _make_user(**kwargs):
    #     defaults = {
    #         "email": "user@example.com",
    #         "username": "testuser",
    #         "hashed_password": get_password_hash("password"),
    #         "is_active": True
    #     }
    #     defaults.update(kwargs)
    #     user = User(**defaults)
    #     db_session.add(user)
    #     db_session.commit()
    #     db_session.refresh(user)
    #     return user
    #
    # return _make_user
    pass


@pytest.fixture
def sample_user(make_user):
    """A pre-created sample user for tests."""
    # Uncomment to use
    # return make_user(email="sample@example.com", username="sampleuser")
    pass


# ============================================================================
# Async Fixtures
# ============================================================================

@pytest.fixture
async def async_client():
    """AsyncClient for async endpoint testing."""
    # Uncomment for async tests
    # from httpx import AsyncClient
    # from myapp.main import app
    #
    # async with AsyncClient(app=app, base_url="http://test") as ac:
    #     yield ac
    pass


# ============================================================================
# Environment Setup
# ============================================================================

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up test environment variables."""
    import os
    original_env = os.environ.copy()

    # Set test environment variables
    os.environ["TESTING"] = "1"
    os.environ["DATABASE_URL"] = "sqlite:///./test.db"

    yield

    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


# ============================================================================
# Pytest Hooks
# ============================================================================

def pytest_configure(config):
    """Configure pytest."""
    # Add custom markers
    config.addinivalue_line("markers", "slow: marks tests as slow")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "unit: marks tests as unit tests")
