"""Unit tests for OutputFormat enum, resolve_format(), and json_error().

Tests cover:
- OutputFormat enum has correct string values
- resolve_format() auto-downgrades RICH to PLAIN when stdout is not a terminal
- resolve_format() leaves PLAIN and JSON unchanged regardless of terminal state
- resolve_format() keeps RICH when stdout is a real terminal
- json_error() prints valid JSON to stdout with success=False and a message field
"""

import json
from unittest.mock import patch

import pytest
from simpletask.utils.output import OutputFormat, json_error, resolve_format


class TestOutputFormatEnum:
    """Tests for OutputFormat enum values."""

    def test_rich_value(self):
        """RICH has string value 'rich'."""
        assert OutputFormat.RICH == "rich"
        assert OutputFormat.RICH.value == "rich"

    def test_plain_value(self):
        """PLAIN has string value 'plain'."""
        assert OutputFormat.PLAIN == "plain"
        assert OutputFormat.PLAIN.value == "plain"

    def test_json_value(self):
        """JSON has string value 'json'."""
        assert OutputFormat.JSON == "json"
        assert OutputFormat.JSON.value == "json"

    def test_enum_is_str_subclass(self):
        """OutputFormat is a str enum (usable as a plain string)."""
        assert isinstance(OutputFormat.JSON, str)

    def test_all_three_values_distinct(self):
        """All three enum members are distinct."""
        values = {OutputFormat.RICH, OutputFormat.PLAIN, OutputFormat.JSON}
        assert len(values) == 3


class TestResolveFormat:
    """Tests for resolve_format() auto-downgrade logic."""

    def test_rich_downgrades_to_plain_when_not_terminal(self):
        """RICH is downgraded to PLAIN when console is not a terminal."""
        with patch("simpletask.utils.output.console") as mock_console:
            mock_console.is_terminal = False
            result = resolve_format(OutputFormat.RICH)
        assert result == OutputFormat.PLAIN

    def test_rich_unchanged_when_terminal(self):
        """RICH stays RICH when console is a real terminal."""
        with patch("simpletask.utils.output.console") as mock_console:
            mock_console.is_terminal = True
            result = resolve_format(OutputFormat.RICH)
        assert result == OutputFormat.RICH

    def test_plain_unchanged_when_not_terminal(self):
        """PLAIN is unaffected by terminal state (not a terminal)."""
        with patch("simpletask.utils.output.console") as mock_console:
            mock_console.is_terminal = False
            result = resolve_format(OutputFormat.PLAIN)
        assert result == OutputFormat.PLAIN

    def test_plain_unchanged_when_terminal(self):
        """PLAIN is unaffected by terminal state (is a terminal)."""
        with patch("simpletask.utils.output.console") as mock_console:
            mock_console.is_terminal = True
            result = resolve_format(OutputFormat.PLAIN)
        assert result == OutputFormat.PLAIN

    def test_json_unchanged_when_not_terminal(self):
        """JSON is never downgraded regardless of terminal state."""
        with patch("simpletask.utils.output.console") as mock_console:
            mock_console.is_terminal = False
            result = resolve_format(OutputFormat.JSON)
        assert result == OutputFormat.JSON

    def test_json_unchanged_when_terminal(self):
        """JSON stays JSON even when stdout is a terminal."""
        with patch("simpletask.utils.output.console") as mock_console:
            mock_console.is_terminal = True
            result = resolve_format(OutputFormat.JSON)
        assert result == OutputFormat.JSON


class TestJsonError:
    """Tests for json_error() output."""

    def test_outputs_valid_json(self, capsys):
        """json_error() prints parseable JSON to stderr."""
        json_error("Something went wrong")
        captured = capsys.readouterr()
        parsed = json.loads(captured.err)
        assert isinstance(parsed, dict)

    def test_success_is_false(self, capsys):
        """json_error() always sets success=False."""
        json_error("error message")
        captured = capsys.readouterr()
        parsed = json.loads(captured.err)
        assert parsed["success"] is False

    def test_message_field_present(self, capsys):
        """json_error() includes the provided message."""
        json_error("Task not found")
        captured = capsys.readouterr()
        parsed = json.loads(captured.err)
        assert parsed["message"] == "Task not found"

    def test_no_ansi_codes_in_output(self, capsys):
        """json_error() output contains no ANSI escape sequences."""
        json_error("error")
        captured = capsys.readouterr()
        assert "\033[" not in captured.err
        assert "\x1b[" not in captured.err

    def test_nothing_written_to_stdout(self, capsys):
        """json_error() writes only to stderr, not stdout."""
        json_error("some error")
        captured = capsys.readouterr()
        assert captured.out == ""
        parsed = json.loads(captured.err)
        assert parsed["success"] is False

    @pytest.mark.parametrize(
        "msg",
        [
            "simple error",
            "Error with 'quotes' and \"double quotes\"",
            "Unicode: café, résumé",
            "Newline\\nin message",
        ],
    )
    def test_various_messages_produce_valid_json(self, capsys, msg):
        """json_error() handles various message strings without breaking JSON."""
        json_error(msg)
        captured = capsys.readouterr()
        parsed = json.loads(captured.err)
        assert parsed["success"] is False
        assert "message" in parsed
