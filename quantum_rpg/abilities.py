"""Class abilities used in combat."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .conditions import check
from .util import loc

if TYPE_CHECKING:
    from .engine import Game


def player_class_id(game: "Game") -> str:
    if getattr(game, "player_class", ""):
        return str(game.player_class)
    for flag in game.state.flags:
        if str(flag).startswith("class_"):
            return str(flag)[6:]
    return ""


def available(game: "Game") -> list[tuple[str, dict]]:
    cid = player_class_id(game)
    out: list[tuple[str, dict]] = []
    for aid, spec in (game.world.abilities or {}).items():
        if not isinstance(spec, dict):
            continue
        need = spec.get("class") or spec.get("classes")
        if need:
            needs = need if isinstance(need, list) else [need]
            if cid not in [str(x) for x in needs]:
                continue
        if spec.get("when") and not check(game, spec["when"]):
            continue
        out.append((str(aid), spec))
    return out


def resolve_choice(game: "Game", choice: str) -> str:
    """Map a combat command to an ability id, or ''."""
    raw = (choice or "").strip()
    if not raw:
        return ""
    rows = available(game)
    low = raw.lower()
    if low.isdigit():
        n = int(low)
        if 5 <= n <= 4 + len(rows):
            return rows[n - 5][0]
        return ""
    parts = low.split(None, 1)
    head = parts[0]
    rest = parts[1] if len(parts) > 1 else ""
    if head in ("ability", "умение", "cast", "skill"):
        q = rest
    else:
        q = low
    if not q:
        return ""
    for aid, spec in rows:
        name = loc(spec.get("name") or aid, game.lang).lower()
        if q == aid.lower() or q == name:
            return aid
    return ""
