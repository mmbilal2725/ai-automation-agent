"""
Basic test template for Python projects.

This template demonstrates common pytest patterns and can be customized
for your specific testing needs.
"""

import pytest
from unittest.mock import Mock, patch


# ============================================================================
# Basic Tests
# ============================================================================

def test_example():
    """Basic test example."""
    # Arrange
    expected = "Hello, World!"

    # Act
    result = "Hello, World!"

    # Assert
    assert result == expected


def test_with_fixture(sample_data):
    """Test using a fixture."""
    assert sample_data is not None
    assert "key" in sample_data


# ============================================================================
# Parametrized Tests
# ============================================================================

@pytest.mark.parametrize("input,expected", [
    (1, 2),
    (2, 4),
    (3, 6),
    (0, 0),
    (-1, -2),
], ids=["one", "two", "three", "zero", "negative"])
def test_double(input, expected):
    """Test doubling function with multiple inputs."""
    assert input * 2 == expected


@pytest.mark.parametrize("value", [
    pytest.param(1, id="small"),
    pytest.param(100, id="medium"),
    pytest.param(1000, marks=pytest.mark.slow, id="large"),
])
def test_process_value(value):
    """Test processing different value sizes."""
    result = value * 2
    assert result > 0


# ============================================================================
# Test Class
# ============================================================================

class TestExample:
    """Group related tests together."""

    @pytest.fixture
    def setup_data(self):
        """Setup data for this test class."""
        return {"initialized": True}

    def test_initialization(self, setup_data):
        """Test initialization."""
        assert setup_data["initialized"] is True

    def test_operation(self, setup_data):
        """Test an operation."""
        setup_data["operation"] = "complete"
        assert "operation" in setup_data


# ============================================================================
# Mocking Tests
# ============================================================================

def test_with_mock():
    """Test using a basic mock."""
    mock_obj = Mock()
    mock_obj.method.return_value = 42

    result = mock_obj.method()

    assert result == 42
    mock_obj.method.assert_called_once()


@patch('module.function')
def test_with_patch(mock_function):
    """Test using patch decorator."""
    mock_function.return_value = "mocked"

    # Your test code here
    # result = module.function()
    # assert result == "mocked"

    mock_function.assert_called()


def test_with_patch_context():
    """Test using patch as context manager."""
    with patch('module.function') as mock_function:
        mock_function.return_value = "mocked"

        # Your test code here
        # result = module.function()
        # assert result == "mocked"


# ============================================================================
# Exception Tests
# ============================================================================

def test_raises_exception():
    """Test that a function raises an exception."""
    with pytest.raises(ValueError):
        raise ValueError("Expected error")


def test_raises_with_message():
    """Test exception with specific message."""
    with pytest.raises(ValueError, match="Expected error"):
        raise ValueError("Expected error")


# ============================================================================
# Conditional Tests
# ============================================================================

@pytest.mark.skip(reason="Not implemented yet")
def test_future_feature():
    """Test for a feature not yet implemented."""
    pass


@pytest.mark.skipif(condition=True, reason="Skip under certain condition")
def test_conditional():
    """Test that runs conditionally."""
    pass


@pytest.mark.xfail(reason="Known bug")
def test_known_issue():
    """Test expected to fail due to known issue."""
    assert False, "This is expected to fail"


# ============================================================================
# Fixtures (usually in conftest.py)
# ============================================================================

@pytest.fixture
def sample_data():
    """Provide sample data for tests."""
    return {"key": "value", "number": 42}


@pytest.fixture
def resource_with_cleanup():
    """Fixture with setup and teardown."""
    # Setup
    resource = {"status": "initialized"}

    yield resource

    # Teardown
    resource["status"] = "cleaned up"
