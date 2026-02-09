"""Unit tests for MCP constraint and context tools."""

import subprocess

import pytest
from simpletask.mcp.models import (
    SimpleTaskConstraintResponse,
    SimpleTaskContextResponse,
    SimpleTaskWriteResponse,
)
from simpletask.mcp.server import constraint, context, new


@pytest.fixture
def temp_project(tmp_path, monkeypatch):
    """Create temporary git project for testing."""
    subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, check=True)
    monkeypatch.chdir(tmp_path)
    return tmp_path


@pytest.fixture
def task_project(temp_project):
    """Create project with existing task file."""
    new(branch="test", title="Test", prompt="Test")
    # Checkout the test branch so MCP tools can auto-detect it
    subprocess.run(["git", "checkout", "-b", "test"], cwd=temp_project, check=True)
    return temp_project


class TestConstraintAdd:
    """Tests for constraint add action."""

    def test_add_constraint(self, task_project):
        """Test adding a constraint."""
        result = constraint(action="add", value="Use Pydantic models")
        assert isinstance(result, SimpleTaskWriteResponse)
        assert result.success is True
        assert result.action == "constraint_added"
        assert "constraint" in result.message.lower()

    def test_add_multiple_constraints(self, task_project):
        """Test adding multiple constraints."""
        constraint(action="add", value="Constraint 1")
        constraint(action="add", value="Constraint 2")

        result = constraint(action="list")
        assert isinstance(result, SimpleTaskConstraintResponse)
        assert result.constraints == ["Constraint 1", "Constraint 2"]

    def test_add_constraint_missing_value(self, task_project):
        """Test that missing value raises ValueError."""
        with pytest.raises(ValueError, match="'value' is required"):
            constraint(action="add")


class TestConstraintRemove:
    """Tests for constraint remove action."""

    def test_remove_constraint_by_index(self, task_project):
        """Test removing constraint by index."""
        constraint(action="add", value="Constraint 1")
        constraint(action="add", value="Constraint 2")
        constraint(action="add", value="Constraint 3")

        result = constraint(action="remove", index=1)
        assert isinstance(result, SimpleTaskWriteResponse)
        assert result.success is True
        assert result.action == "constraint_removed"
        assert "constraint 1" in result.message.lower()

    def test_remove_constraint_all(self, task_project):
        """Test removing all constraints."""
        constraint(action="add", value="Constraint 1")
        constraint(action="add", value="Constraint 2")

        result = constraint(action="remove", all=True)
        assert isinstance(result, SimpleTaskWriteResponse)
        assert result.success is True
        assert result.action == "constraint_removed"
        assert "all constraints" in result.message.lower()

    def test_remove_constraint_invalid_index(self, task_project):
        """Test that invalid index raises ValueError."""
        constraint(action="add", value="Constraint 1")

        with pytest.raises(ValueError, match="Invalid constraint index"):
            constraint(action="remove", index=5)

    def test_remove_constraint_missing_params(self, task_project):
        """Test that missing index and all raises ValueError."""
        constraint(action="add", value="Constraint 1")

        with pytest.raises(ValueError, match="Either 'index' or 'all=True' is required"):
            constraint(action="remove")


class TestConstraintList:
    """Tests for constraint list action."""

    def test_list_constraints_empty(self, task_project):
        """Test listing constraints when none exist."""
        result = constraint(action="list")
        assert isinstance(result, SimpleTaskConstraintResponse)
        assert result.action == "constraint_list"
        assert result.constraints is None

    def test_list_constraints_with_data(self, task_project):
        """Test listing constraints with existing data."""
        constraint(action="add", value="Constraint 1")
        constraint(action="add", value="Constraint 2")
        constraint(action="add", value="Constraint 3")

        result = constraint(action="list")
        assert isinstance(result, SimpleTaskConstraintResponse)
        assert result.constraints == ["Constraint 1", "Constraint 2", "Constraint 3"]


class TestContextSet:
    """Tests for context set action."""

    def test_set_context(self, task_project):
        """Test setting a context key-value pair."""
        result = context(action="set", key="framework", value="django")
        assert isinstance(result, SimpleTaskWriteResponse)
        assert result.success is True
        assert result.action == "context_set"
        assert "framework" in result.message

    def test_set_multiple_context_keys(self, task_project):
        """Test setting multiple context keys."""
        context(action="set", key="framework", value="django")
        context(action="set", key="database", value="postgresql")

        result = context(action="show")
        assert isinstance(result, SimpleTaskContextResponse)
        assert result.context == {"framework": "django", "database": "postgresql"}

    def test_set_context_update_existing(self, task_project):
        """Test updating existing context key."""
        context(action="set", key="framework", value="flask")
        result = context(action="set", key="framework", value="django")

        assert isinstance(result, SimpleTaskWriteResponse)
        assert result.success is True

        # Verify update
        result = context(action="show")
        assert result.context == {"framework": "django"}

    def test_set_context_missing_key(self, task_project):
        """Test that missing key raises ValueError."""
        with pytest.raises(ValueError, match="'key' is required"):
            context(action="set", value="value")

    def test_set_context_missing_value(self, task_project):
        """Test that missing value raises ValueError."""
        with pytest.raises(ValueError, match="'value' is required"):
            context(action="set", key="key")


class TestContextRemove:
    """Tests for context remove action."""

    def test_remove_context_by_key(self, task_project):
        """Test removing context entry by key."""
        context(action="set", key="framework", value="django")
        context(action="set", key="database", value="postgresql")

        result = context(action="remove", key="framework")
        assert isinstance(result, SimpleTaskWriteResponse)
        assert result.success is True
        assert result.action == "context_removed"
        assert "framework" in result.message

    def test_remove_context_all(self, task_project):
        """Test removing all context entries."""
        context(action="set", key="framework", value="django")
        context(action="set", key="database", value="postgresql")

        result = context(action="remove", all=True)
        assert isinstance(result, SimpleTaskWriteResponse)
        assert result.success is True
        assert result.action == "context_removed"
        assert "all context" in result.message.lower()

    def test_remove_context_invalid_key(self, task_project):
        """Test that invalid key raises ValueError."""
        context(action="set", key="framework", value="django")

        with pytest.raises(ValueError, match="Context key 'invalid' not found"):
            context(action="remove", key="invalid")

    def test_remove_context_missing_params(self, task_project):
        """Test that missing key and all raises ValueError."""
        context(action="set", key="framework", value="django")

        with pytest.raises(ValueError, match="Either 'key' or 'all=True' is required"):
            context(action="remove")


class TestContextShow:
    """Tests for context show action."""

    def test_show_context_empty(self, task_project):
        """Test showing context when none exist."""
        result = context(action="show")
        assert isinstance(result, SimpleTaskContextResponse)
        assert result.action == "context_show"
        assert result.context is None

    def test_show_context_with_data(self, task_project):
        """Test showing context with existing data."""
        context(action="set", key="framework", value="django")
        context(action="set", key="database", value="postgresql")
        context(action="set", key="cache", value="redis")

        result = context(action="show")
        assert isinstance(result, SimpleTaskContextResponse)
        assert result.context == {
            "framework": "django",
            "database": "postgresql",
            "cache": "redis",
        }
