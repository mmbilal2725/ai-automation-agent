# FastAPI Testing Patterns

Comprehensive patterns for testing FastAPI applications with pytest.

## Table of Contents

- [Basic Setup](#basic-setup)
- [TestClient Usage](#testclient-usage)
- [Async Testing](#async-testing)
- [Database Testing](#database-testing)
- [Dependency Overrides](#dependency-overrides)
- [Authentication Testing](#authentication-testing)
- [File Upload Testing](#file-upload-testing)
- [WebSocket Testing](#websocket-testing)

## Basic Setup

### conftest.py Structure

```python
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from myapp.main import app
from myapp.database import Base, get_db

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="module")
def client():
    """Create test client for the entire test module."""
    with TestClient(app) as c:
        yield c

@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(autouse=True)
def override_get_db(db_session):
    """Override the get_db dependency for all tests."""
    def _override():
        try:
            yield db_session
        finally:
            db_session.close()
    app.dependency_overrides[get_db] = _override
    yield
    app.dependency_overrides.clear()
```

## TestClient Usage

### Basic Request Testing

```python
def test_read_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}

def test_create_item(client):
    response = client.post(
        "/items/",
        json={"name": "Test Item", "price": 10.5}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Item"
    assert "id" in data

def test_validation_error(client):
    response = client.post(
        "/items/",
        json={"name": "Test"}  # Missing required 'price' field
    )
    assert response.status_code == 422
    assert "detail" in response.json()
```

### Query Parameters and Headers

```python
def test_with_query_params(client):
    response = client.get("/items/?skip=0&limit=10")
    assert response.status_code == 200
    assert len(response.json()) <= 10

def test_with_headers(client):
    response = client.get(
        "/protected",
        headers={"Authorization": "Bearer fake-token"}
    )
    assert response.status_code == 200
```

## Async Testing

### AsyncClient Setup

```python
import pytest
from httpx import AsyncClient
from myapp.main import app

@pytest.mark.asyncio
async def test_async_endpoint():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/async-route")
    assert response.status_code == 200

@pytest.fixture
async def async_client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.mark.asyncio
async def test_with_fixture(async_client):
    response = await async_client.post(
        "/async-items/",
        json={"name": "Async Item"}
    )
    assert response.status_code == 201
```

### pytest.ini Configuration for Async

```ini
[tool:pytest]
asyncio_mode = auto
```

## Database Testing

### Transaction Isolation

```python
@pytest.fixture
def db_session():
    """Database session with automatic rollback."""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()
```

### Factory Pattern for Test Data

```python
# factories.py
from myapp.models import User, Item

def create_user(db, **kwargs):
    defaults = {
        "email": "test@example.com",
        "username": "testuser",
        "hashed_password": "hashed"
    }
    defaults.update(kwargs)
    user = User(**defaults)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def create_item(db, user_id, **kwargs):
    defaults = {
        "name": "Test Item",
        "price": 10.0,
        "owner_id": user_id
    }
    defaults.update(kwargs)
    item = Item(**defaults)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item

# test_items.py
def test_get_user_items(client, db_session):
    user = create_user(db_session, email="user@test.com")
    create_item(db_session, user.id, name="Item 1")
    create_item(db_session, user.id, name="Item 2")

    response = client.get(f"/users/{user.id}/items")
    assert response.status_code == 200
    assert len(response.json()) == 2
```

## Dependency Overrides

### Simple Dependency Override

```python
from myapp.dependencies import get_current_user

def test_protected_route(client):
    def override_get_current_user():
        return {"id": 1, "username": "testuser"}

    app.dependency_overrides[get_current_user] = override_get_current_user

    response = client.get("/protected")
    assert response.status_code == 200

    app.dependency_overrides.clear()
```

### Fixture-Based Override

```python
@pytest.fixture
def authenticated_client(client):
    """Client with authentication dependency overridden."""
    def override_get_current_user():
        return {"id": 1, "username": "testuser", "is_admin": False}

    app.dependency_overrides[get_current_user] = override_get_current_user
    yield client
    app.dependency_overrides.clear()

@pytest.fixture
def admin_client(client):
    """Client with admin authentication."""
    def override_get_current_user():
        return {"id": 1, "username": "admin", "is_admin": True}

    app.dependency_overrides[get_current_user] = override_get_current_user
    yield client
    app.dependency_overrides.clear()

def test_user_access(authenticated_client):
    response = authenticated_client.get("/user-only")
    assert response.status_code == 200

def test_admin_access(admin_client):
    response = admin_client.get("/admin-only")
    assert response.status_code == 200
```

## Authentication Testing

### JWT Token Testing

```python
def test_login_success(client, db_session):
    # Create user
    create_user(db_session, email="user@test.com", password="secret")

    # Login
    response = client.post(
        "/token",
        data={"username": "user@test.com", "password": "secret"}
    )
    assert response.status_code == 200
    token_data = response.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"

    # Use token
    headers = {"Authorization": f"Bearer {token_data['access_token']}"}
    response = client.get("/users/me", headers=headers)
    assert response.status_code == 200
    assert response.json()["email"] == "user@test.com"

def test_login_invalid_credentials(client):
    response = client.post(
        "/token",
        data={"username": "wrong@test.com", "password": "wrong"}
    )
    assert response.status_code == 401

@pytest.fixture
def auth_headers(client, db_session):
    """Generate authentication headers for tests."""
    user = create_user(db_session)
    response = client.post(
        "/token",
        data={"username": user.email, "password": "password"}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_with_auth(client, auth_headers):
    response = client.get("/protected", headers=auth_headers)
    assert response.status_code == 200
```

## File Upload Testing

### Single File Upload

```python
def test_upload_file(client):
    files = {"file": ("test.txt", b"file content", "text/plain")}
    response = client.post("/upload", files=files)
    assert response.status_code == 200
    assert response.json()["filename"] == "test.txt"

def test_upload_image(client):
    # Read actual image file
    with open("test_image.png", "rb") as f:
        files = {"file": ("image.png", f, "image/png")}
        response = client.post("/upload-image", files=files)
    assert response.status_code == 200
```

### Multiple Files Upload

```python
def test_upload_multiple_files(client):
    files = [
        ("files", ("file1.txt", b"content1", "text/plain")),
        ("files", ("file2.txt", b"content2", "text/plain"))
    ]
    response = client.post("/upload-multiple", files=files)
    assert response.status_code == 200
    assert len(response.json()["filenames"]) == 2
```

## WebSocket Testing

### Basic WebSocket Testing

```python
def test_websocket(client):
    with client.websocket_connect("/ws") as websocket:
        data = websocket.receive_json()
        assert data["message"] == "Connected"

        websocket.send_json({"msg": "Hello"})
        data = websocket.receive_json()
        assert data["echo"] == "Hello"

def test_websocket_authentication(client):
    with client.websocket_connect("/ws?token=valid-token") as websocket:
        data = websocket.receive_json()
        assert "user" in data
```

## Best Practices

1. **Use fixtures for common setup** - Database sessions, authenticated clients, test data
2. **Clear dependency overrides** - Always clear after tests to avoid side effects
3. **Test both success and failure cases** - Happy path and validation errors
4. **Use parametrize for similar tests** - Reduce code duplication
5. **Test database transactions** - Ensure proper rollback/commit behavior
6. **Mock external services** - Don't hit real APIs in tests
7. **Use factory functions** - For creating test data consistently
8. **Test async endpoints properly** - Use AsyncClient for async routes
9. **Verify response schemas** - Not just status codes
10. **Test authentication flows end-to-end** - Login, token usage, expiration
