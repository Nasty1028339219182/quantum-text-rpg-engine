"""Day clock: phases, shop hours, night encounters."""

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


def shop_is_open(game: "Game", npc: dict) -> bool:
    """Shops close on `time.shop_closed` phases. No `time:` block → always open."""
    cfg = _cfg(game)
    if not cfg:
        return True
    if npc.get("shop_always") or npc.get("shop_hours") == "always":
        return True
    phase = clock(game)[1]
    hours = npc.get("shop_hours")
    if isinstance(hours, list):
        return phase in [str(x) for x in hours]
    closed = cfg.get("shop_closed")
    if closed is None:
        closed = ["night"]
    return phase not in [str(x) for x in (closed or [])]


def encounter_chance(game: "Game", table: dict) -> int:
    chance = int(table.get("chance") or 0)
    phase = clock(game)[1]
    if f"chance_{phase}" in table:
        chance = int(table[f"chance_{phase}"])
    else:
        cfg = _cfg(game)
        if phase == "night":
            chance += int(cfg.get("night_encounter_bonus") or 0)
        elif phase == "evening":
            chance += int(cfg.get("evening_encounter_bonus") or 0)
    return max(0, min(100, chance))
