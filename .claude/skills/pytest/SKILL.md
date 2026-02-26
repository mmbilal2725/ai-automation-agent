---
name: pytest
description: Comprehensive pytest testing skill for Python projects with specialized FastAPI support. Use when: (1) User wants to generate test files for existing code, (2) User asks about pytest patterns, best practices, fixtures, or test organization, (3) User is working with FastAPI testing (TestClient, async tests, dependency overrides, authentication), (4) User needs help writing tests, configuring pytest, or organizing test suites. Includes test generation script, FastAPI-specific patterns, fixture templates, and comprehensive pytest reference documentation.
---

# Pytest Testing Skill

Generate tests, apply best practices, and master pytest patterns for Python and FastAPI projects.

## Quick Start

### Generate Test Files

Generate pytest test files automatically from Python source code:

```bash
python scripts/generate_tests.py <source_file.py>
```

Options:
- `-o <dir>` - Specify output directory (default: auto-detects tests/ folder)
- `-f` - Force overwrite existing test file

Example:
```bash
# Generate tests for a module
python scripts/generate_tests.py app/main.py

# Generate in specific directory
python scripts/generate_tests.py app/users.py -o tests/unit/

# Overwrite existing test file
python scripts/generate_tests.py app/models.py -f
```

The script analyzes your code and generates:
- Test functions for all public functions
- Test classes for all classes with their methods
- Async test stubs for async functions
- FastAPI-specific fixtures if FastAPI imports detected
- Proper imports and boilerplate

### Use Template Files

Template files are available in `assets/` for quick setup:

**conftest.py template:**
```bash
# Copy and customize
cp assets/conftest_template.py tests/conftest.py
```

**Basic test template:**
```bash
cp assets/test_template_basic.py tests/test_example.py
```

**FastAPI test template:**
```bash
cp assets/test_template_fastapi.py tests/test_api.py
```

**pytest.ini configuration:**
```bash
cp assets/pytest.ini pytest.ini
```

## Testing Workflows

### Workflow 1: Generate Tests for Existing Code

When user has existing Python code and wants tests:

1. Run the test generator on the source file
2. Review generated test file
3. Customize test assertions and test data
4. Add fixtures to conftest.py as needed
5. Run tests to verify

### Workflow 2: Write FastAPI Tests

When user needs to test FastAPI endpoints:

1. Read `references/fastapi-patterns.md` for comprehensive FastAPI testing patterns
2. Focus on relevant sections:
   - TestClient usage for sync endpoints
   - AsyncClient for async endpoints
   - Dependency overrides for auth/database
   - Database testing with fixtures
3. Use template from `assets/test_template_fastapi.py` as starting point
4. Implement tests following the patterns

**Key FastAPI patterns to reference:**

```python
# TestClient for sync endpoints
def test_endpoint(client):
    response = client.get("/api/resource")
    assert response.status_code == 200

# AsyncClient for async endpoints
@pytest.mark.asyncio
async def test_async_endpoint(async_client):
    response = await async_client.get("/api/async-resource")
    assert response.status_code == 200

# Dependency override for authentication
def test_protected(client):
    def override_get_current_user():
        return {"id": 1, "username": "test"}
    app.dependency_overrides[get_current_user] = override_get_current_user
    response = client.get("/protected")
    app.dependency_overrides.clear()
```

### Workflow 3: Setup Test Infrastructure

When user needs to set up testing infrastructure:

1. Copy `assets/conftest_template.py` to `tests/conftest.py`
2. Copy `assets/pytest.ini` to project root
3. Customize conftest.py:
   - Update imports to match project structure
   - Uncomment and configure database fixtures
   - Uncomment and configure FastAPI client fixtures
   - Add project-specific fixtures
4. Configure pytest.ini:
   - Set testpaths
   - Add custom markers
   - Configure coverage if needed
   - Enable asyncio_mode if needed

### Workflow 4: Learn Pytest Patterns

When user asks about specific pytest features:

**For FastAPI-specific patterns:**
Read `references/fastapi-patterns.md` sections:
- Basic Setup - conftest.py structure
- TestClient Usage - request testing
- Async Testing - AsyncClient patterns
- Database Testing - transaction isolation
- Dependency Overrides - auth and mocking
- Authentication Testing - JWT patterns
- File Upload Testing
- WebSocket Testing

**For general pytest patterns:**
Read `references/pytest-patterns.md` sections:
- Fixtures - scopes, setup/teardown, factories
- Parametrization - testing multiple inputs
- Mocking - unittest.mock patterns
- Test Organization - structure and classes
- Markers - custom markers and filtering
- Configuration - pytest.ini and pyproject.toml

## Reference Documentation

### FastAPI Patterns

Read `references/fastapi-patterns.md` for:
- Complete FastAPI testing setup with TestClient
- Database testing with SQLAlchemy
- Dependency injection and override patterns
- Authentication and authorization testing
- Async endpoint testing
- File upload and WebSocket testing
- Best practices for FastAPI projects

### Pytest Patterns

Read `references/pytest-patterns.md` for:
- Fixture patterns (scopes, factories, chaining)
- Parametrization techniques
- Mocking and patching strategies
- Test organization and structure
- Custom markers and filtering
- Configuration options
- Advanced patterns (monkeypatching, capsys, etc.)

## Common Tasks

### Generate Tests for a Module

```bash
python scripts/generate_tests.py app/services/user_service.py
```

### Setup New Test Suite

```bash
# Create tests directory
mkdir -p tests

# Copy templates
cp assets/conftest_template.py tests/conftest.py
cp assets/pytest.ini pytest.ini

# Customize conftest.py and pytest.ini
# Then write your first test or generate from source
```

### Test FastAPI Endpoints

```python
# In your test file
def test_create_user(client, db_session):
    response = client.post(
        "/users/",
        json={"email": "test@example.com", "password": "secret"}
    )
    assert response.status_code == 201
    assert "id" in response.json()
```

### Test with Authentication

```python
@pytest.fixture
def authenticated_client(client):
    def override_get_current_user():
        return {"id": 1, "username": "testuser"}
    app.dependency_overrides[get_current_user] = override_get_current_user
    yield client
    app.dependency_overrides.clear()

def test_protected_route(authenticated_client):
    response = authenticated_client.get("/protected")
    assert response.status_code == 200
```

### Run Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_users.py

# Run specific test function
pytest tests/test_users.py::test_create_user

# Run tests with marker
pytest -m unit
pytest -m "not slow"

# Run with coverage
pytest --cov=app --cov-report=html

# Run in parallel (requires pytest-xdist)
pytest -n auto
```

## Best Practices

1. **Generate, then customize** - Use the generator for boilerplate, customize assertions and test data
2. **Use fixtures liberally** - Keep tests DRY with shared setup in conftest.py
3. **Test both success and failure** - Happy path and error cases
4. **Clear dependency overrides** - Always clear after tests to avoid side effects
5. **Isolate tests** - Each test should be independent
6. **Use parametrize** - Test multiple inputs without code duplication
7. **Mark tests appropriately** - Use markers for slow, integration, unit tests
8. **Keep tests fast** - Fast tests = frequent runs = better development
9. **Mock external dependencies** - Don't hit real APIs or services
10. **Follow AAA pattern** - Arrange, Act, Assert for clarity

## Troubleshooting

**Generated tests have TODO comments:**
- Review and customize assertions based on expected behavior
- Provide actual test data for function parameters
- Adjust imports if module structure differs

**FastAPI tests failing:**
- Ensure dependency overrides are cleared after tests
- Check database fixtures are properly configured
- Verify app is imported correctly in conftest.py
- For async tests, ensure `asyncio_mode = auto` in pytest.ini

**Import errors:**
- Adjust import paths in generated tests to match project structure
- Ensure tests directory has `__init__.py`
- Check PYTHONPATH includes project root

**Fixture not found:**
- Ensure fixture is defined in conftest.py
- Check fixture scope matches usage
- Verify conftest.py is in tests directory or parent

## When to Use This Skill

Use this skill when you need to:
- Generate test files from existing code
- Set up pytest infrastructure for a project
- Learn pytest patterns and best practices
- Test FastAPI applications (endpoints, auth, database)
- Configure pytest with markers, coverage, async support
- Organize and structure test suites
- Write fixtures for common test scenarios
- Mock dependencies and external services
