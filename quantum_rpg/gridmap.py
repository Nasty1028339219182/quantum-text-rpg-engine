"""Schematic room grid. Boxes of text, not a picture."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .util import loc

if TYPE_CHECKING:
    from .engine import Game


def rows_for(game: "Game") -> list:
    raw = game.world.game.get("map")
    if isinstance(raw, list):
        return raw
    if not isinstance(raw, dict):
        return []
    rid = game.region_of(game.state.location)
    table = raw.get("regions") if isinstance(raw.get("regions"), dict) else raw
    if rid and isinstance(table.get(rid), list):
        return table[rid]
    if isinstance(raw.get("grid"), list):
        return raw["grid"]
    return []


def reveal_all(game: "Game") -> bool:
    raw = game.world.game.get("map")
    if not isinstance(raw, dict):
        return False
    return str(raw.get("reveal") or "") == "all"


def view(game: "Game") -> list[list[dict]]:
    rows = rows_for(game)
    if not rows:
        return []
    exits = game.visible_exits()
    dest_dir = {}
    for direction, dest in exits.items():
        target = game.exit_target(dest)
        if target:
            dest_dir[str(target)] = direction
    here = game.state.location
    visited = set(game.state.visited)
    show_all = reveal_all(game)
    out = []
    for row in rows:
        if not isinstance(row, list):
            continue
        line = []
        for cell in row:
            cid = str(cell or "").strip()
            if not cid:
                line.append({"id": "", "label": "", "command": "", "here": False})
                continue
            room = game.world.locations.get(cid) or {}
            token = loc(room.get("map_mark"), game.lang) or game.loc_name(cid)
            token = str(token).replace(" ", "")[:2] or "?"
            known = show_all or cid == here or cid in visited
            neighbor = dest_dir.get(cid, "")
            locked = bool(neighbor) and game.is_locked(neighbor, exits.get(neighbor))
            if cid == here:
                label = f"[{token}]"
            elif known:
                label = token
            elif neighbor:
                label = "?"
            else:
                label = ""
            command = ""
            if neighbor and not locked and cid != here:
                command = neighbor
            line.append({"id": cid, "label": label, "command": command, "here": cid == here})
        out.append(line)
    return out


def render(grid: list[list[dict]]) -> str:
    if not grid:
        return ""
    width = 4
    for row in grid:
        for cell in row:
            width = max(width, len(str(cell.get("label") or "")))
    def box(text: str) -> str:
        return str(text or "").center(width)[:width].ljust(width)

    span = "─" * width
    top = "┌" + "┬".join(span for _ in grid[0]) + "┐"
    mid = "├" + "┼".join(span for _ in grid[0]) + "┤"
    bot = "└" + "┴".join(span for _ in grid[0]) + "┘"
    lines = [top]
    for i, row in enumerate(grid):
        lines.append("│" + "│".join(box(cell.get("label") or "") for cell in row) + "│")
        lines.append(bot if i == len(grid) - 1 else mid)
    return "\n".join(lines)
