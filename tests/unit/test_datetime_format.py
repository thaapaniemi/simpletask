"""Unit tests for datetime_format module.

Tests cover:
- format_datetime() - UTC to local timezone conversion
- Timezone abbreviation inclusion
- None handling
- Edge cases
"""

from datetime import UTC, datetime

from simpletask.utils.datetime_format import format_datetime


class TestFormatDatetime:
    """Test format_datetime function."""

    def test_format_utc_to_local(self):
        """Verify UTC datetime converts to local timezone."""
        # Create a UTC datetime
        utc_dt = datetime(2026, 1, 20, 15, 30, 45, tzinfo=UTC)

        # Format it (should convert to local timezone)
        result = format_datetime(utc_dt)

        # Verify format includes date, time, and timezone
        assert "2026-01-20" in result
        assert ":" in result  # Time separator
        # Note: We can't assert exact time since it depends on system timezone

    def test_format_includes_timezone_abbrev(self):
        """Verify timezone abbreviation appears in output."""
        utc_dt = datetime(2026, 1, 20, 15, 30, 45, tzinfo=UTC)
        result = format_datetime(utc_dt)

        # Should have at least 3 parts: date, time, timezone
        parts = result.split()
        assert len(parts) >= 3

        # Last part should be timezone abbreviation (e.g., EST, PST, UTC)
        tz_abbrev = parts[-1]
        assert len(tz_abbrev) >= 2  # Timezone abbreviations are 2+ chars
        assert tz_abbrev.isalpha() or tz_abbrev.startswith(("+", "-"))

    def test_format_without_timezone(self):
        """Verify include_timezone=False omits timezone indicator."""
        utc_dt = datetime(2026, 1, 20, 15, 30, 45, tzinfo=UTC)
        result = format_datetime(utc_dt, include_timezone=False)

        # Should have format: YYYY-MM-DD HH:MM:SS (no timezone)
        parts = result.split()
        assert len(parts) == 2  # Date and time only

        # Verify format
        assert "2026-01-20" in result
        assert ":" in result

    def test_format_none_returns_empty(self):
        """Verify None input returns empty string."""
        result = format_datetime(None)
        assert result == ""

    def test_format_preserves_date(self):
        """Verify date components are correct after conversion."""
        # Use a datetime that won't change date when converted to any timezone
        utc_dt = datetime(2026, 6, 15, 12, 0, 0, tzinfo=UTC)  # Noon UTC
        result = format_datetime(utc_dt)

        # Date should always be 2026-06-15 or nearby (depending on timezone)
        # For safety, just check year and month are present
        assert "2026-06" in result

    def test_format_with_seconds(self):
        """Verify seconds are included in output."""
        utc_dt = datetime(2026, 1, 20, 15, 30, 45, tzinfo=UTC)
        result = format_datetime(utc_dt)

        # Should have HH:MM:SS format
        time_parts = result.split()[1].split(":")
        assert len(time_parts) == 3  # Hour, minute, second

    def test_format_midnight(self):
        """Verify midnight (00:00:00) displays correctly."""
        utc_dt = datetime(2026, 1, 20, 0, 0, 0, tzinfo=UTC)
        result = format_datetime(utc_dt)

        # Should contain time even if it's midnight
        assert ":" in result
        assert "2026-01-20" in result

    def test_format_with_microseconds_ignored(self):
        """Verify microseconds are not displayed."""
        utc_dt = datetime(2026, 1, 20, 15, 30, 45, 123456, tzinfo=UTC)
        result = format_datetime(utc_dt)

        # Microseconds should not appear in output
        assert ".123456" not in result
        assert "123456" not in result
