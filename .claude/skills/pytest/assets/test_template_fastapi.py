"""
FastAPI test template.

This template demonstrates common FastAPI testing patterns using pytest.
Customize based on your application's structure.
"""

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

# Uncomment and adjust imports
# from myapp.main import app
# from myapp.models import User, Item
# from myapp.schemas import UserCreate, ItemCreate


# ============================================================================
# Basic Endpoint Tests
# ============================================================================

def test_read_root(client):
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}


def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


# ============================================================================
# CRUD Operation Tests
# ============================================================================

def test_create_item(client, db_session):
    """Test creating a new item."""
    response = client.post(
        "/items/",
        json={"name": "Test Item", "description": "Test Description", "price": 10.5}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Item"
    assert "id" in data


def test_read_item(client, db_session):
    """Test reading an item."""
    # Create item first
    create_response = client.post(
        "/items/",
        json={"name": "Test Item", "price": 10.5}
    )
    item_id = create_response.json()["id"]

    # Read the item
    response = client.get(f"/items/{item_id}")
    assert response.status_code == 200
    assert response.json()["id"] == item_id


def test_read_item_not_found(client):
    """Test reading non-existent item."""
    response = client.get("/items/99999")
    assert response.status_code == 404


def test_update_item(client, db_session):
    """Test updating an item."""
    # Create item
    create_response = client.post(
        "/items/",
        json={"name": "Original", "price": 10.0}
    )
    item_id = create_response.json()["id"]

    # Update item
    response = client.put(
        f"/items/{item_id}",
        json={"name": "Updated", "price": 20.0}
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Updated"


def test_delete_item(client, db_session):
    """Test deleting an item."""
    # Create item
    create_response = client.post(
        "/items/",
        json={"name": "To Delete", "price": 10.0}
    )
    item_id = create_response.json()["id"]

    # Delete item
    response = client.delete(f"/items/{item_id}")
    assert response.status_code == 204

    # Verify deletion
    get_response = client.get(f"/items/{item_id}")
    assert get_response.status_code == 404


def test_list_items(client, db_session):
    """Test listing items with pagination."""
    # Create multiple items
    for i in range(5):
        client.post("/items/", json={"name": f"Item {i}", "price": 10.0})

    # List items
    response = client.get("/items/?skip=0&limit=3")
    assert response.status_code == 200
    items = response.json()
    assert len(items) <= 3


# ============================================================================
# Validation Tests
# ============================================================================

def test_create_item_validation_error(client):
    """Test validation error when creating item."""
    response = client.post(
        "/items/",
        json={"name": "Test"}  # Missing required 'price' field
    )
    assert response.status_code == 422
    assert "detail" in response.json()


def test_invalid_item_id(client):
    """Test invalid item ID format."""
    response = client.get("/items/invalid")
    assert response.status_code == 422


# ============================================================================
# Authentication Tests
# ============================================================================

def test_login_success(client, db_session, make_user):
    """Test successful login."""
    # Create user
    user = make_user(email="test@example.com", password="password123")

    # Login
    response = client.post(
        "/token",
        data={"username": "test@example.com", "password": "password123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_invalid_credentials(client):
    """Test login with invalid credentials."""
    response = client.post(
        "/token",
        data={"username": "wrong@example.com", "password": "wrong"}
    )
    assert response.status_code == 401


def test_protected_endpoint_without_auth(client):
    """Test accessing protected endpoint without authentication."""
    response = client.get("/users/me")
    assert response.status_code == 401


def test_protected_endpoint_with_auth(authenticated_client):
    """Test accessing protected endpoint with authentication."""
    response = authenticated_client.get("/users/me")
    assert response.status_code == 200
    assert "email" in response.json()


# ============================================================================
# Query Parameter Tests
# ============================================================================

def test_search_with_query_params(client):
    """Test endpoint with query parameters."""
    response = client.get("/search?q=test&limit=10")
    assert response.status_code == 200


@pytest.mark.parametrize("query,expected_count", [
    ("test", 5),
    ("example", 3),
    ("", 0),
])
def test_search_variations(client, query, expected_count):
    """Test search with different query parameters."""
    response = client.get(f"/search?q={query}")
    assert response.status_code == 200
    # assert len(response.json()) == expected_count


# ============================================================================
# Header Tests
# ============================================================================

def test_custom_header(client):
    """Test endpoint requiring custom header."""
    response = client.get(
        "/api/data",
        headers={"X-API-Key": "test-key"}
    )
    assert response.status_code == 200


# ============================================================================
# File Upload Tests
# ============================================================================

def test_upload_file(client):
    """Test file upload."""
    files = {"file": ("test.txt", b"file content", "text/plain")}
    response = client.post("/upload", files=files)
    assert response.status_code == 200
    assert "filename" in response.json()


def test_upload_invalid_file_type(client):
    """Test uploading invalid file type."""
    files = {"file": ("test.exe", b"content", "application/x-msdownload")}
    response = client.post("/upload", files=files)
    assert response.status_code == 400


# ============================================================================
# Async Endpoint Tests
# ============================================================================

@pytest.mark.asyncio
async def test_async_endpoint(async_client):
    """Test async endpoint."""
    response = await async_client.get("/async-data")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_async_create(async_client):
    """Test async create operation."""
    response = await async_client.post(
        "/async-items/",
        json={"name": "Async Item", "price": 15.0}
    )
    assert response.status_code == 201


# ============================================================================
# WebSocket Tests
# ============================================================================

def test_websocket(client):
    """Test WebSocket connection."""
    with client.websocket_connect("/ws") as websocket:
        data = websocket.receive_json()
        assert "message" in data

        websocket.send_json({"msg": "Hello"})
        response = websocket.receive_json()
        assert response is not None


# ============================================================================
# Error Handling Tests
# ============================================================================

def test_internal_server_error_handling(client):
    """Test that server errors are handled gracefully."""
    # Trigger an error condition
    response = client.get("/trigger-error")
    assert response.status_code == 500
    assert "detail" in response.json()


def test_not_found_error(client):
    """Test 404 error handling."""
    response = client.get("/nonexistent-endpoint")
    assert response.status_code == 404


# ============================================================================
# Database Integration Tests
# ============================================================================

@pytest.mark.integration
def test_database_transaction(client, db_session):
    """Test database transaction handling."""
    # Create item
    response = client.post(
        "/items/",
        json={"name": "Transaction Test", "price": 25.0}
    )
    assert response.status_code == 201

    # Verify in database
    item_id = response.json()["id"]
    # item = db_session.query(Item).filter(Item.id == item_id).first()
    # assert item is not None
    # assert item.name == "Transaction Test"


# ============================================================================
# Performance Tests
# ============================================================================

@pytest.mark.slow
def test_bulk_operations(client):
    """Test performance of bulk operations."""
    items = [{"name": f"Item {i}", "price": 10.0} for i in range(100)]

    for item in items:
        response = client.post("/items/", json=item)
        assert response.status_code == 201
