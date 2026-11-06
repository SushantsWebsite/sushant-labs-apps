"""Pure logic for Focus Timer. No tkinter here so it can be unit-tested."""

WORK, SHORT, LONG = "work", "short", "long"
DURATIONS = {WORK: 25 * 60, SHORT: 5 * 60, LONG: 15 * 60}
LABELS = {WORK: "Focus", SHORT: "Short break", LONG: "Long break"}
SESSIONS_BEFORE_LONG = 4


def format_time(seconds: int) -> str:
    """Format seconds as MM:SS (never negative)."""
    seconds = max(0, int(seconds))
    minutes, secs = divmod(seconds, 60)
    return f"{minutes:02d}:{secs:02d}"


def next_phase(current: str, sessions_done: int) -> str:
    """Return the phase that follows `current`.

    `sessions_done` is the number of completed focus sessions, including the one
    that just ended when `current` is WORK.
    """
    if current == WORK:
        if sessions_done > 0 and sessions_done % SESSIONS_BEFORE_LONG == 0:
            return LONG
        return SHORT
    return WORK
