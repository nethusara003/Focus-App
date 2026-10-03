"""Focus timer (pomodoro-style countdown) for Daily Focus.

Standard library only. The countdown logic lives in pure functions so it
can be unit tested without waiting in real time.
"""

import time
from typing import Callable, Optional


def format_duration(total_seconds: int) -> str:
    """Format a number of seconds as MM:SS (or H:MM:SS for long durations)."""
    total_seconds = max(0, int(total_seconds))
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    return f"{minutes:02d}:{seconds:02d}"


def run_timer(
    duration_seconds: int,
    label: str = "Focus",
    tick: Optional[Callable[[int], None]] = None,
    sleep: Callable[[float], None] = time.sleep,
) -> bool:
    """Run a countdown timer.

    Args:
        duration_seconds: How long the timer should run.
        label: Text shown next to the remaining time.
        tick: Called with the seconds remaining on each tick (including 0
            at the end). Defaults to a live-updating terminal line.
        sleep: Sleep function, injectable for tests.

    Returns:
        True if the timer completed, False if it was cancelled with Ctrl+C.

    Raises:
        ValueError: If duration_seconds is not positive.
    """
    if int(duration_seconds) <= 0:
        raise ValueError("Timer duration must be positive.")

    remaining = int(duration_seconds)

    if tick is None:
        def tick(left: int) -> None:
            print(f"\r{label} {format_duration(left)} remaining", end="", flush=True)

    try:
        while remaining > 0:
            tick(remaining)
            sleep(1)
            remaining -= 1
        tick(0)
        return True
    except KeyboardInterrupt:
        return False
