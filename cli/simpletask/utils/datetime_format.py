"""Datetime formatting utilities for CLI display.

Converts UTC timestamps to local timezone for user-friendly display.
"""

from datetime import datetime


def format_datetime(dt: datetime | None, include_timezone: bool = True) -> str:
    """Format datetime for CLI display, converting UTC to local timezone.

    Args:
        dt: Datetime to format (assumed to be in UTC). None returns empty string.
        include_timezone: Whether to include timezone abbreviation in output.

    Returns:
        Formatted datetime string in local timezone.
        Format: "YYYY-MM-DD HH:MM:SS TZ" (e.g., "2026-01-20 10:30:45 EST")
        or "YYYY-MM-DD HH:MM:SS" if include_timezone=False.

    Examples:
        >>> dt_utc = datetime(2026, 1, 20, 15, 30, 45, tzinfo=UTC)
        >>> format_datetime(dt_utc)  # doctest: +SKIP
        '2026-01-20 10:30:45 EST'  # In EST timezone (UTC-5)
        >>> format_datetime(dt_utc, include_timezone=False)  # doctest: +SKIP
        '2026-01-20 10:30:45'
        >>> format_datetime(None)
        ''
    """
    if dt is None:
        return ""

    # Convert to local timezone
    local_dt = dt.astimezone()

    # Format the datetime
    if include_timezone:
        # Get timezone abbreviation (e.g., EST, PST, UTC)
        tz_abbrev = local_dt.strftime("%Z")
        return local_dt.strftime(f"%Y-%m-%d %H:%M:%S {tz_abbrev}")
    else:
        return local_dt.strftime("%Y-%m-%d %H:%M:%S")


# Export public API
__all__ = ["format_datetime"]
