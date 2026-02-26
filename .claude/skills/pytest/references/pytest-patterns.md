# Pytest Patterns and Best Practices

Comprehensive guide to pytest patterns for Python testing.

## Table of Contents

- [Fixtures](#fixtures)
- [Parametrization](#parametrization)
- [Mocking](#mocking)
- [Test Organization](#test-organization)
- [Markers](#markers)
- [Configuration](#configuration)

## Fixtures

### Basic Fixtures

```python
import pytest

@pytest.fixture
def sample_data():
    """Provides sample data for tests."""
    return {"key": "value", "number": 42}

def test_with_fixture(sample_data):
    assert sample_data["key"] == "value"
```

### Fixture Scopes

```python
@pytest.fixture(scope="function")  # Default - runs for each test
def function_fixture():
    return "fresh data"

@pytest.fixture(scope="class")  # Runs once per test class
def class_fixture():
    return "shared in class"

@pytest.fixture(scope="module")  # Runs once per module
def module_fixture():
    return "shared in module"

@pytest.fixture(scope="session")  # Runs once per test session
def session_fixture():
    return "shared across all tests"
```

### Setup and Teardown

```python
@pytest.fixture
def resource():
    # Setup
    resource = create_resource()
    print("Setup complete")

    yield resource  # Test runs here

    # Teardown
    resource.cleanup()
    print("Teardown complete")

def test_resource(resource):
    assert resource.is_ready()
```

### Fixture Chaining

```python
@pytest.fixture
def database():
    db = DatabaseConnection()
    db.connect()
    yield db
    db.disconnect()

@pytest.fixture
def populated_database(database):
    database.insert_test_data()
    return database

def test_query(populated_database):
    result = populated_database.query("SELECT * FROM users")
    assert len(result) > 0
```

### autouse Fixtures

```python
@pytest.fixture(autouse=True)
def reset_environment():
    """Automatically runs before each test."""
    os.environ.clear()
    yield
    # Cleanup after test
```

### Fixture Factories

```python
@pytest.fixture
def make_user():
    """Factory fixture that returns a function."""
    def _make_user(name="John", age=30):
        return User(name=name, age=age)
    return _make_user

def test_users(make_user):
    user1 = make_user(name="Alice")
    user2 = make_user(name="Bob", age=25)
    assert user1.name == "Alice"
    assert user2.age == 25
```

## Parametrization

### Basic Parametrize

```python
@pytest.mark.parametrize("input,expected", [
    (1, 2),
    (2, 4),
    (3, 6),
])
def test_double(input, expected):
    assert input * 2 == expected
```

### Multiple Parameters

```python
@pytest.mark.parametrize("x", [1, 2, 3])
@pytest.mark.parametrize("y", [10, 20])
def test_combinations(x, y):
    # Runs 6 times (3 * 2 combinations)
    assert x + y > 0
```

### Parametrize with IDs

```python
@pytest.mark.parametrize("input,expected", [
    (1, 2),
    (2, 4),
    (3, 6),
], ids=["one", "two", "three"])
def test_with_ids(input, expected):
    assert input * 2 == expected
```

### Parametrize Fixtures

```python
@pytest.fixture(params=["sqlite", "postgres", "mysql"])
def database_connection(request):
    db_type = request.param
    conn = connect_to_database(db_type)
    yield conn
    conn.close()

def test_database_operations(database_connection):
    # Runs once for each database type
    result = database_connection.execute("SELECT 1")
    assert result is not None
```

### Complex Parametrization

```python
test_cases = [
    pytest.param(1, 2, 3, id="simple"),
    pytest.param(10, 20, 30, id="tens"),
    pytest.param(100, 200, 300, marks=pytest.mark.slow, id="hundreds"),
]

@pytest.mark.parametrize("a,b,expected", test_cases)
def test_addition(a, b, expected):
    assert a + b == expected
```

## Mocking

### Basic Mock

```python
from unittest.mock import Mock, MagicMock, patch

def test_with_mock():
    mock_obj = Mock()
    mock_obj.method.return_value = 42

    result = mock_obj.method()
    assert result == 42
    mock_obj.method.assert_called_once()
```

### Patching Functions

```python
@patch('mymodule.external_api_call')
def test_api_call(mock_api):
    mock_api.return_value = {"status": "success"}

    result = my_function_that_calls_api()
    assert result["status"] == "success"
    mock_api.assert_called_once()
```

### Patching with Context Manager

```python
def test_with_patch():
    with patch('mymodule.get_data') as mock_get_data:
        mock_get_data.return_value = [1, 2, 3]

        result = process_data()
        assert len(result) == 3
```

### Mock Side Effects

```python
def test_side_effects():
    mock = Mock()
    mock.side_effect = [1, 2, 3]

    assert mock() == 1
    assert mock() == 2
    assert mock() == 3
```

### Mock Exceptions

```python
def test_exception_handling():
    mock = Mock()
    mock.side_effect = ValueError("Invalid input")

    with pytest.raises(ValueError, match="Invalid input"):
        process_with_mock(mock)
```

### Patching Multiple Targets

```python
@patch('mymodule.function_a')
@patch('mymodule.function_b')
def test_multiple_patches(mock_b, mock_a):
    # Note: patches are applied bottom-to-top
    mock_a.return_value = "A"
    mock_b.return_value = "B"

    result = my_function()
    assert result == "AB"
```

### Spy Pattern (Partial Mock)

```python
def test_spy_pattern():
    real_obj = MyClass()
    with patch.object(real_obj, 'method_to_spy', wraps=real_obj.method_to_spy) as spy:
        real_obj.do_something()

        # Real method was called
        spy.assert_called_once()
```

## Test Organization

### Directory Structure

```
project/
├── src/
│   └── myapp/
│       ├── __init__.py
│       ├── core.py
│       └── utils.py
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── test_core.py
    └── test_utils.py
```

### Test Classes

```python
class TestUserManagement:
    """Group related tests together."""

    @pytest.fixture
    def user(self):
        return User(name="Test User")

    def test_create_user(self):
        user = User(name="New User")
        assert user.name == "New User"

    def test_update_user(self, user):
        user.update(name="Updated")
        assert user.name == "Updated"

    def test_delete_user(self, user):
        user.delete()
        assert user.is_deleted
```

### Shared Fixtures (conftest.py)

```python
# tests/conftest.py
import pytest

@pytest.fixture(scope="session")
def database():
    """Database fixture available to all tests."""
    db = setup_database()
    yield db
    db.teardown()

@pytest.fixture
def sample_user():
    """User fixture available to all tests."""
    return User(name="Sample", email="sample@test.com")
```

## Markers

### Built-in Markers

```python
@pytest.mark.skip(reason="Not implemented yet")
def test_future_feature():
    pass

@pytest.mark.skipif(sys.version_info < (3, 8), reason="Requires Python 3.8+")
def test_new_feature():
    pass

@pytest.mark.xfail(reason="Known bug")
def test_buggy_feature():
    pass

@pytest.mark.parametrize("input,expected", [(1, 2)])
def test_with_params(input, expected):
    pass
```

### Custom Markers

```python
# pytest.ini
[tool:pytest]
markers =
    slow: marks tests as slow
    integration: marks tests as integration tests
    unit: marks tests as unit tests

# test file
@pytest.mark.slow
def test_slow_operation():
    time.sleep(5)

@pytest.mark.integration
def test_database_integration():
    pass

# Run specific markers
# pytest -m slow
# pytest -m "not slow"
# pytest -m "integration and not slow"
```

### Combining Markers

```python
@pytest.mark.slow
@pytest.mark.integration
def test_slow_integration():
    pass
```

## Configuration

### pytest.ini

```ini
[tool:pytest]
# Test discovery
testpaths = tests
python_files = test_*.py *_test.py
python_classes = Test*
python_functions = test_*

# Output
addopts =
    -v
    --strict-markers
    --tb=short
    --disable-warnings

# Coverage
addopts =
    --cov=src
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=80

# Markers
markers =
    slow: slow running tests
    integration: integration tests
    unit: unit tests

# Async
asyncio_mode = auto

# Warnings
filterwarnings =
    error
    ignore::UserWarning
```

### pyproject.toml Configuration

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "-v",
    "--strict-markers",
    "--cov=src",
    "--cov-report=html",
]
markers = [
    "slow: marks tests as slow",
    "integration: marks tests as integration tests",
]
```

### Environment-Specific Configuration

```python
# conftest.py
import os
import pytest

def pytest_configure(config):
    """Set environment variables for testing."""
    os.environ["TESTING"] = "1"
    os.environ["DATABASE_URL"] = "sqlite:///./test.db"

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    # Setup
    original_env = os.environ.copy()

    yield

    # Restore
    os.environ.clear()
    os.environ.update(original_env)
```

## Advanced Patterns

### Monkey Patching

```python
def test_monkeypatch(monkeypatch):
    def mock_return():
        return 42

    monkeypatch.setattr('module.function', mock_return)
    result = module.function()
    assert result == 42
```

### Temporary Files

```python
def test_with_tmpdir(tmp_path):
    # tmp_path is a pathlib.Path object
    file = tmp_path / "test.txt"
    file.write_text("content")

    assert file.read_text() == "content"
```

### Capturing Output

```python
def test_output(capsys):
    print("Hello, World!")
    captured = capsys.readouterr()
    assert captured.out == "Hello, World!\n"
```

### Custom Assertions

```python
def assert_valid_user(user):
    __tracebackhide__ = True  # Hide this function from traceback
    assert user.name, "User must have a name"
    assert user.email, "User must have an email"
    assert "@" in user.email, "Email must be valid"

def test_user():
    user = User(name="Test", email="test@example.com")
    assert_valid_user(user)
```

## Best Practices

1. **One assertion per test (when possible)** - Makes failures clearer
2. **Use descriptive test names** - Test name should describe what it tests
3. **Arrange-Act-Assert pattern** - Structure tests clearly
4. **Don't test implementation details** - Test behavior, not internals
5. **Use fixtures for setup** - Keep tests DRY
6. **Isolate tests** - Each test should be independent
7. **Use parametrize for similar tests** - Reduce duplication
8. **Mark slow/integration tests** - Allow selective test runs
9. **Keep tests fast** - Fast tests = frequent runs
10. **Mock external dependencies** - Tests should be deterministic
