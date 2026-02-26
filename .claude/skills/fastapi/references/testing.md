# Testing FastAPI Applications

## Overview

FastAPI makes testing straightforward with its built-in `TestClient` based on HTTPX and pytest integration. Tests use standard Python `assert` statements and run synchronously even when testing async code.

## Setup

### Installation

```bash
pip install httpx pytest
```

### Project Structure

```
app/
├── main.py
├── routers/
│   └── users.py
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── test_main.py
    └── test_users.py
```

## Basic Testing

### Simple Test

```python
# app/main.py
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def read_main():
    return {"msg": "Hello World"}

# app/tests/test_main.py
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"msg": "Hello World"}
```

**Key points:**
- Use `def test_*`, not `async def`
- Use normal function calls, not `await`
- `TestClient` handles async automatically

### Running Tests

```bash
pytest
pytest -v  # verbose
pytest tests/test_main.py  # specific file
pytest tests/test_main.py::test_read_main  # specific test
pytest -k "user"  # tests matching pattern
```

## TestClient Features

### Making Requests

```python
from fastapi.testclient import TestClient

client = TestClient(app)

# GET request
response = client.get("/items/", params={"skip": 0, "limit": 10})

# POST with JSON
response = client.post("/items/", json={"name": "Foo", "price": 42.0})

# POST with form data
response = client.post("/login/", data={"username": "user", "password": "pass"})

# File upload
files = {"file": ("test.txt", open("test.txt", "rb"), "text/plain")}
response = client.post("/files/", files=files)

# Custom headers
headers = {"X-Token": "fake-token"}
response = client.get("/items/", headers=headers)

# Cookies
cookies = {"session_id": "abc123"}
response = client.get("/items/", cookies=cookies)
```

### Response Assertions

```python
def test_create_item():
    response = client.post("/items/", json={"name": "Foo", "price": 42.0})

    # Status code
    assert response.status_code == 200

    # JSON response
    assert response.json() == {"name": "Foo", "price": 42.0}

    # Headers
    assert "content-type" in response.headers
    assert response.headers["content-type"] == "application/json"

    # Cookies
    assert "session_id" in response.cookies

    # Response text
    assert "Foo" in response.text
```

## Testing with Dependencies

### Dependency Override

```python
# app/main.py
from typing import Annotated
from fastapi import Depends, FastAPI

app = FastAPI()

async def get_db():
    db = DatabaseConnection()
    try:
        yield db
    finally:
        db.close()

@app.get("/items/")
async def read_items(db: Annotated[DatabaseConnection, Depends(get_db)]):
    return db.get_items()

# app/tests/test_main.py
async def override_get_db():
    return MockDatabase()

app.dependency_overrides[get_db] = override_get_db

def test_read_items():
    response = client.get("/items/")
    assert response.status_code == 200
```

**Benefits:**
- Replace real database with mock
- Test without external dependencies
- Faster test execution

### Current User Override

```python
# Override authentication
from app.dependencies import get_current_user
from app.models import User

async def override_get_current_user():
    return User(username="testuser", email="test@example.com")

app.dependency_overrides[get_current_user] = override_get_current_user

def test_read_user_me():
    response = client.get("/users/me")
    assert response.status_code == 200
    assert response.json()["username"] == "testuser"
```

## Testing with Database

### In-Memory Database

```python
# app/tests/conftest.py
import pytest
from sqlmodel import Session, SQLModel, create_engine
from fastapi.testclient import TestClient

from app.main import app
from app.database.session import get_session

@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session

@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()

# app/tests/test_users.py
def test_create_user(client: TestClient):
    response = client.post(
        "/users/",
        json={"email": "test@example.com", "password": "secret"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "id" in data
```

### Database Fixtures with Data

```python
# app/tests/conftest.py
@pytest.fixture(name="session_with_data")
def session_with_data_fixture():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        # Add test data
        hero1 = Hero(name="Deadpond", secret_name="Dive Wilson")
        hero2 = Hero(name="Spider-Boy", secret_name="Pedro Parqueador")
        session.add(hero1)
        session.add(hero2)
        session.commit()

        yield session

def test_read_heroes(client: TestClient, session_with_data: Session):
    app.dependency_overrides[get_session] = lambda: session_with_data
    response = client.get("/heroes/")
    assert len(response.json()) == 2
```

## Testing Authentication

### Login Flow

```python
def test_login():
    response = client.post(
        "/token",
        data={"username": "johndoe", "password": "secret"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_incorrect_password():
    response = client.post(
        "/token",
        data={"username": "johndoe", "password": "wrong"}
    )
    assert response.status_code == 401

def test_read_users_me():
    # Login first
    login_response = client.post(
        "/token",
        data={"username": "johndoe", "password": "secret"}
    )
    token = login_response.json()["access_token"]

    # Use token
    response = client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["username"] == "johndoe"
```

### Reusable Token Fixture

```python
# app/tests/conftest.py
@pytest.fixture
def auth_token(client: TestClient):
    response = client.post(
        "/token",
        data={"username": "testuser", "password": "testpass"}
    )
    return response.json()["access_token"]

@pytest.fixture
def auth_headers(auth_token: str):
    return {"Authorization": f"Bearer {auth_token}"}

# app/tests/test_items.py
def test_create_item(client: TestClient, auth_headers: dict):
    response = client.post(
        "/items/",
        json={"name": "Foo", "price": 42.0},
        headers=auth_headers
    )
    assert response.status_code == 200
```

## Testing Error Cases

```python
def test_read_item_not_found():
    response = client.get("/items/999")
    assert response.status_code == 404
    assert response.json() == {"detail": "Item not found"}

def test_create_item_invalid_data():
    response = client.post(
        "/items/",
        json={"name": "Foo"}  # Missing required 'price'
    )
    assert response.status_code == 422
    assert "detail" in response.json()

def test_unauthorized_access():
    response = client.get("/admin/users/")
    assert response.status_code == 401
```

## Parametrized Tests

```python
import pytest

@pytest.mark.parametrize("item_id,expected_status", [
    (1, 200),
    (2, 200),
    (999, 404),
])
def test_read_item(item_id: int, expected_status: int):
    response = client.get(f"/items/{item_id}")
    assert response.status_code == expected_status

@pytest.mark.parametrize("username,password,expected_status", [
    ("johndoe", "secret", 200),
    ("johndoe", "wrong", 401),
    ("nonexistent", "secret", 401),
])
def test_login_variations(username: str, password: str, expected_status: int):
    response = client.post(
        "/token",
        data={"username": username, "password": password}
    )
    assert response.status_code == expected_status
```

## Coverage

### Installation

```bash
pip install pytest-cov
```

### Run with Coverage

```bash
pytest --cov=app --cov-report=html
pytest --cov=app --cov-report=term-missing
```

### Coverage Configuration

```ini
# .coveragerc or pyproject.toml
[tool.coverage.run]
source = ["app"]
omit = ["app/tests/*", "app/__init__.py"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
]
```

## Async Tests

For testing background tasks or WebSockets:

```bash
pip install pytest-asyncio
```

```python
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_async_endpoint():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/async-endpoint")
    assert response.status_code == 200
```

## Testing Best Practices

1. **Use fixtures** for setup and teardown
2. **Override dependencies** to avoid external services
3. **Test edge cases** and error conditions
4. **Use in-memory database** for faster tests
5. **Parametrize tests** for multiple scenarios
6. **Measure coverage** to ensure comprehensive testing
7. **Mock external APIs** with libraries like `responses` or `httpx-mock`
8. **Test authentication** separately from business logic
9. **Keep tests independent** - each test should run in isolation
10. **Name tests clearly** - describe what is being tested

## Example Test Suite Structure

```python
# app/tests/test_users.py
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

def test_create_user(client: TestClient):
    """Test creating a new user"""
    response = client.post(
        "/users/",
        json={"email": "test@example.com", "password": "secret"}
    )
    assert response.status_code == 200

def test_create_user_duplicate_email(client: TestClient, session: Session):
    """Test creating user with duplicate email fails"""
    # Create first user
    client.post("/users/", json={"email": "test@example.com", "password": "secret"})

    # Try to create duplicate
    response = client.post(
        "/users/",
        json={"email": "test@example.com", "password": "secret2"}
    )
    assert response.status_code == 400

def test_read_users(client: TestClient):
    """Test reading list of users"""
    response = client.get("/users/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_read_user_me(client: TestClient, auth_headers: dict):
    """Test reading current user info"""
    response = client.get("/users/me", headers=auth_headers)
    assert response.status_code == 200
    assert "email" in response.json()
```
