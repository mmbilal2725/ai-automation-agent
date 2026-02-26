# Testing with SQLModel

## Test Database Setup

```python
import pytest
from sqlmodel import SQLModel, create_engine, Session
from fastapi.testclient import TestClient

# Test engine using SQLite in-memory
@pytest.fixture(name="engine")
def engine_fixture():
    """Create test database engine"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        echo=False
    )
    SQLModel.metadata.create_all(engine)
    return engine

@pytest.fixture(name="session")
def session_fixture(engine):
    """Create test session"""
    with Session(engine) as session:
        yield session
```

## FastAPI TestClient with Database

```python
from typing import Generator
from fastapi import FastAPI
from fastapi.testclient import TestClient

@pytest.fixture(name="client")
def client_fixture(session: Session) -> Generator[TestClient, None, None]:
    """Create test client with overridden database session"""

    def get_session_override():
        return session

    # Override dependency
    app.dependency_overrides[get_session] = get_session_override

    with TestClient(app) as client:
        yield client

    # Clear overrides
    app.dependency_overrides.clear()
```

## Testing CRUD Operations

```python
def test_create_user(session: Session):
    """Test creating a user"""
    user = User(
        username="testuser",
        email="test@example.com",
        is_active=True
    )
    session.add(user)
    session.commit()
    session.refresh(user)

    assert user.id is not None
    assert user.username == "testuser"
    assert user.email == "test@example.com"

def test_get_user(session: Session):
    """Test retrieving a user"""
    # Create user
    user = User(username="testuser", email="test@example.com")
    session.add(user)
    session.commit()
    session.refresh(user)

    # Retrieve user
    retrieved = session.get(User, user.id)
    assert retrieved is not None
    assert retrieved.username == "testuser"

def test_update_user(session: Session):
    """Test updating a user"""
    user = User(username="testuser", email="test@example.com")
    session.add(user)
    session.commit()

    # Update
    user.email = "newemail@example.com"
    session.add(user)
    session.commit()
    session.refresh(user)

    assert user.email == "newemail@example.com"

def test_delete_user(session: Session):
    """Test deleting a user"""
    user = User(username="testuser", email="test@example.com")
    session.add(user)
    session.commit()
    user_id = user.id

    # Delete
    session.delete(user)
    session.commit()

    # Verify deletion
    deleted_user = session.get(User, user_id)
    assert deleted_user is None
```

## Testing API Endpoints

```python
def test_create_user_endpoint(client: TestClient):
    """Test POST /users endpoint"""
    response = client.post(
        "/users",
        json={
            "username": "testuser",
            "email": "test@example.com"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "testuser"
    assert "id" in data

def test_get_user_endpoint(client: TestClient, session: Session):
    """Test GET /users/{id} endpoint"""
    # Create user
    user = User(username="testuser", email="test@example.com")
    session.add(user)
    session.commit()
    session.refresh(user)

    # Get user
    response = client.get(f"/users/{user.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"

def test_get_nonexistent_user(client: TestClient):
    """Test GET /users/{id} with invalid ID"""
    response = client.get("/users/9999")
    assert response.status_code == 404

def test_list_users_endpoint(client: TestClient, session: Session):
    """Test GET /users endpoint"""
    # Create multiple users
    users = [
        User(username=f"user{i}", email=f"user{i}@example.com")
        for i in range(5)
    ]
    session.add_all(users)
    session.commit()

    # List users
    response = client.get("/users")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 5

def test_update_user_endpoint(client: TestClient, session: Session):
    """Test PUT /users/{id} endpoint"""
    user = User(username="testuser", email="test@example.com")
    session.add(user)
    session.commit()
    session.refresh(user)

    # Update user
    response = client.put(
        f"/users/{user.id}",
        json={"email": "newemail@example.com"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "newemail@example.com"

def test_delete_user_endpoint(client: TestClient, session: Session):
    """Test DELETE /users/{id} endpoint"""
    user = User(username="testuser", email="test@example.com")
    session.add(user)
    session.commit()
    user_id = user.id

    # Delete user
    response = client.delete(f"/users/{user_id}")
    assert response.status_code == 204

    # Verify deletion
    deleted = session.get(User, user_id)
    assert deleted is None
```

## Fixtures for Test Data

```python
@pytest.fixture
def sample_user(session: Session) -> User:
    """Create a sample user for testing"""
    user = User(
        username="testuser",
        email="test@example.com",
        is_active=True
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

@pytest.fixture
def sample_users(session: Session) -> List[User]:
    """Create multiple sample users"""
    users = [
        User(username=f"user{i}", email=f"user{i}@example.com")
        for i in range(10)
    ]
    session.add_all(users)
    session.commit()
    for user in users:
        session.refresh(user)
    return users

# Use fixtures in tests
def test_with_fixture(sample_user: User):
    """Test using fixture"""
    assert sample_user.username == "testuser"
    assert sample_user.id is not None
```

## Testing Relationships

```python
def test_user_posts_relationship(session: Session):
    """Test one-to-many relationship"""
    # Create user
    user = User(username="testuser", email="test@example.com")
    session.add(user)
    session.commit()
    session.refresh(user)

    # Create posts
    posts = [
        Post(title=f"Post {i}", content=f"Content {i}", user_id=user.id)
        for i in range(3)
    ]
    session.add_all(posts)
    session.commit()

    # Test relationship
    assert len(user.posts) == 3
    assert all(post.user_id == user.id for post in user.posts)

def test_many_to_many_relationship(session: Session):
    """Test many-to-many relationship"""
    # Create students and courses
    student = Student(name="John")
    courses = [
        Course(title="Math"),
        Course(title="Science")
    ]

    session.add(student)
    session.add_all(courses)
    session.commit()

    # Link student to courses
    student.courses.extend(courses)
    session.commit()

    # Test relationship
    assert len(student.courses) == 2
    assert courses[0].students[0].name == "John"
```

## Testing Validation

```python
def test_email_validation(client: TestClient):
    """Test email validation"""
    response = client.post(
        "/users",
        json={
            "username": "testuser",
            "email": "invalid-email"  # Invalid email
        }
    )
    assert response.status_code == 422  # Validation error

def test_unique_constraint(client: TestClient, session: Session):
    """Test unique constraint violation"""
    # Create first user
    user1 = User(username="testuser", email="test@example.com")
    session.add(user1)
    session.commit()

    # Try to create duplicate
    response = client.post(
        "/users",
        json={
            "username": "testuser",  # Duplicate username
            "email": "other@example.com"
        }
    )
    assert response.status_code == 400
```

## Testing Transactions

```python
def test_transaction_rollback(session: Session):
    """Test transaction rollback on error"""
    user = User(username="testuser", email="test@example.com")
    session.add(user)

    try:
        # Simulate error
        session.commit()
        raise ValueError("Simulated error")
    except ValueError:
        session.rollback()

    # User should not be in database
    users = session.exec(select(User)).all()
    assert len(users) == 0

def test_transaction_commit(session: Session):
    """Test successful transaction"""
    user = User(username="testuser", email="test@example.com")
    session.add(user)
    session.commit()

    # User should be in database
    users = session.exec(select(User)).all()
    assert len(users) == 1
```

## Parametrized Tests

```python
@pytest.mark.parametrize("username,email,expected", [
    ("user1", "user1@example.com", True),
    ("user2", "user2@example.com", True),
    ("user3", "invalid-email", False),
])
def test_create_user_variations(
    client: TestClient,
    username: str,
    email: str,
    expected: bool
):
    """Test user creation with various inputs"""
    response = client.post(
        "/users",
        json={"username": username, "email": email}
    )

    if expected:
        assert response.status_code == 201
    else:
        assert response.status_code == 422
```

## Database Isolation

```python
@pytest.fixture(scope="function", autouse=True)
def reset_database(engine):
    """Reset database before each test"""
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
```

## Testing with PostgreSQL Test Database

```python
import pytest
from sqlmodel import create_engine

@pytest.fixture(scope="session")
def postgres_engine():
    """Create PostgreSQL test database"""
    # Create test database
    engine = create_engine(
        "postgresql://user:password@localhost:5432/test_db"
    )

    # Create tables
    SQLModel.metadata.create_all(engine)

    yield engine

    # Drop all tables after tests
    SQLModel.metadata.drop_all(engine)
    engine.dispose()

@pytest.fixture
def postgres_session(postgres_engine):
    """Create session for PostgreSQL tests"""
    with Session(postgres_engine) as session:
        yield session
        # Rollback after each test
        session.rollback()
```

## Coverage Configuration

```ini
# pytest.ini
[pytest]
testpaths = tests
python_files = test_*.py
python_functions = test_*
addopts =
    --cov=app
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=80
```

```bash
# Run tests with coverage
pytest --cov=app --cov-report=html

# View coverage report
open htmlcov/index.html
```

## Mocking External Dependencies

```python
from unittest.mock import Mock, patch

def test_with_mocked_external_api(session: Session):
    """Test with mocked external API call"""
    with patch('app.services.external_api.call') as mock_api:
        mock_api.return_value = {"status": "success"}

        user = User(username="testuser", email="test@example.com")
        session.add(user)
        session.commit()

        # Verify mock was called
        mock_api.assert_called_once()
```
