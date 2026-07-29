"""Utility functions for date calculation and week identifier computation."""

import os
from datetime import datetime, timezone


def get_week_identifier(dt: datetime | None = None) -> str:
    """Compute ISO week identifier string (e.g., '2026-W30') for a given datetime.

    Args:
        dt: Datetime object. Defaults to reference now if None.

    Returns:
        str: Formatted ISO week string (e.g., '2026-W30').
    """
    if dt is None:
        dt = get_reference_now()

    year, week, _ = dt.isocalendar()
    return f"{year}-W{week:02d}"


def get_reference_now() -> datetime:
    """Get reference current datetime for dataset filtering and scoring.

    DESIGN CHOICE EXPLANATION:
    The Phase 4 dataset activity items are all dated within a fixed target week
    (2026-W30, July 20-27, 2026 per backend/data/README.md). If the server were to use
    the real wall-clock date during live evaluation or demo runs, filtering activity items
    for 'this week' would yield zero items. To ensure the fixed dataset remains fully
    demoable and interactive at runtime, DIGEST_REFERENCE_DATE environment variable is checked
    first, defaulting to the dataset's target reference timestamp (2026-07-27T23:59:59Z).

    Returns:
        datetime: Timezone-aware reference UTC datetime.
    """
    env_ref = os.getenv("DIGEST_REFERENCE_DATE")
    if env_ref:
        try:
            parsed = datetime.fromisoformat(env_ref.replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed
        except Exception:
            pass

    # Default to dataset target week endpoint (July 26, 2026 23:59:59Z -> 2026-W30)
    return datetime(2026, 7, 26, 23, 59, 59, tzinfo=timezone.utc)
