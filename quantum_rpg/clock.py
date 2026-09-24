"""Day clock. Foundation for 1.4 — phases only, not a full calendar."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .i18n import t

if TYPE_CHECKING:
    from .engine import Game

PHASES = ("night", "morning", "day", "evening")


def _cfg(game: "Game") -> dict:
    raw = game.world.game.get("time") or {}
    return raw if isinstance(raw, dict) else {}


def day_length(game: "Game") -> int:
    return max(4, int(_cfg(game).get("day_length") or 24))


def clock(game: "Game") -> tuple[int, str]:
    """Return (hour 0..length-1, phase).

    On a 24-hour day: night 21–5, morning 6–11, day 12–17, evening 18–20.
    Other day lengths are scaled onto those bands.
    """
    length = day_length(game)
    start = int(_cfg(game).get("start_hour") or 8)
    hour = (start + int(game.state.time)) % length
    scaled = int(hour * 24 / length) if length != 24 else hour
    if scaled >= 21 or scaled < 6:
        phase = "night"
    elif scaled < 12:
        phase = "morning"
    elif scaled < 18:
        phase = "day"
    else:
        phase = "evening"
    return hour, phase


def phase_name(game: "Game") -> str:
    return t(game.lang, "phase_" + clock(game)[1])


def advance(game: "Game", hours: int | None = None) -> tuple[int, str]:
    n = hours
    if n is None:
        n = int(_cfg(game).get("rest_hours") or 8)
    game.state.time += max(1, int(n))
    return clock(game)
