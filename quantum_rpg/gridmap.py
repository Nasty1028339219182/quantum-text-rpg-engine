"""Schematic room grid. Boxes of text, not a picture."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .util import loc

if TYPE_CHECKING:
    from .engine import Game


def floor_table(game: "Game") -> dict:
    raw = game.world.game.get("map")
    if isinstance(raw, list):
        return {"grid": raw}
    if not isinstance(raw, dict):
        return {}
    if isinstance(raw.get("floors"), dict):
        return raw["floors"]
    table = raw.get("regions") if isinstance(raw.get("regions"), dict) else raw
    out = {}
    for key, spec in table.items():
        if isinstance(spec, list) or (isinstance(spec, dict) and isinstance(spec.get("grid"), list)):
            out[str(key)] = spec
    return out


def floor_rows(spec) -> list:
    if isinstance(spec, list):
        return spec
    if isinstance(spec, dict):
        return spec.get("grid") or []
    return []


def floor_of(game: "Game", loc_id: str) -> str:
    for fid, spec in floor_table(game).items():
        for row in floor_rows(spec):
            if not isinstance(row, list):
                continue
            if loc_id in [str(cell or "").strip() for cell in row]:
                return fid
    return game.region_of(loc_id)


def floor_name(game: "Game", fid: str) -> str:
    spec = floor_table(game).get(fid)
    if isinstance(spec, dict) and spec.get("name"):
        return loc(spec.get("name"), game.lang)
    named = game.region_name(fid)
    return named if named and named != fid else str(fid)


def floor_match(game: "Game", query: str) -> str:
    q = (query or "").strip().lower()
    if not q:
        return ""
    for fid in floor_table(game):
        name = floor_name(game, fid).lower()
        if q == fid.lower() or q == name or (len(q) >= 3 and name.startswith(q)):
            return fid
    return ""


def floor_seen(game: "Game", fid: str) -> bool:
    if fid == floor_of(game, game.state.location):
        return True
    for row in floor_rows(floor_table(game).get(fid)):
        if not isinstance(row, list):
            continue
        for cell in row:
            if str(cell or "").strip() in game.state.visited:
                return True
    return False


def reveal_mode(game: "Game") -> str:
    raw = game.world.game.get("map")
    if not isinstance(raw, dict):
        return "rooms"
    return str(raw.get("reveal") or "rooms")


def rows_for(game: "Game", floor: str = "") -> list:
    table = floor_table(game)
    fid = floor or floor_of(game, game.state.location)
    if fid in table:
        return floor_rows(table[fid])
    raw = game.world.game.get("map")
    if isinstance(raw, dict) and isinstance(raw.get("grid"), list):
        return raw["grid"]
    return []


def view(game: "Game", floor: str = "") -> list[list[dict]]:
    rows = rows_for(game, floor)
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
    mode = reveal_mode(game)
    out = []
    for row in rows:
        if not isinstance(row, list):
            continue
        line = []
        for cell in row:
            cid = str(cell or "").strip()
            if not cid:
                line.append({"id": "", "label": "", "command": "", "here": False, "east": "", "south": ""})
                continue
            room = game.world.locations.get(cid) or {}
            token = loc(room.get("map_mark"), game.lang) or game.loc_name(cid)
            token = str(token).replace(" ", "")[:2] or "?"
            known = mode == "all" or cid == here or cid in visited
            neighbor = dest_dir.get(cid, "")
            locked = bool(neighbor) and game.is_locked(neighbor, exits.get(neighbor))
            if not known and mode == "fog" and not neighbor:
                label = ""
            elif cid == here:
                label = f"[{token}{_tag(game, cid)}]"
            elif known:
                label = token + _tag(game, cid)
            else:
                label = "?"
            if cid in game.state.map_notes and (known or cid == here):
                label += "*"
            command = neighbor if neighbor and not locked and cid != here else ""
            line.append({"id": cid, "label": label, "command": command, "here": cid == here, "east": "", "south": ""})
        out.append(line)
    for y, line in enumerate(out):
        for x, cell in enumerate(line):
            right = line[x + 1] if x + 1 < len(line) else None
            below = out[y + 1][x] if y + 1 < len(out) and x < len(out[y + 1]) else None
            if right is not None:
                cell["east"] = _link(game, cell.get("id") or "", right.get("id") or "")
            if below is not None:
                cell["south"] = _link(game, cell.get("id") or "", below.get("id") or "")
    return out


def render(grid: list[list[dict]]) -> str:
    if not grid:
        return ""
    width = 4
    cols = max(len(row) for row in grid)
    for row in grid:
        for cell in row:
            width = max(width, len(str(cell.get("label") or "")))

    def box(text: str) -> str:
        return str(text or "").center(width)[:width].ljust(width)

    def hspan(kind: str) -> str:
        if kind == "open":
            glyph = " "
        elif kind == "one":
            glyph = ">"
        elif kind == "locked":
            glyph = "×"
        elif kind == "none":
            glyph = "═"
        else:
            glyph = "─"
        left = (width - 1) // 2
        return "─" * left + glyph + "─" * (width - left - 1)

    def vbar(kind: str) -> str:
        return {"open": " ", "one": ">", "locked": "×", "none": "║"}.get(kind, "│")

    lines = []
    top = "┌" + "┬".join("─" * width for _ in range(cols)) + "┐"
    lines.append(top)
    for y, row in enumerate(grid):
        padded = list(row) + [{"label": "", "east": "", "south": ""}] * (cols - len(row))
        body = "│"
        for x, cell in enumerate(padded):
            body += box(cell.get("label") or "")
            body += vbar(cell.get("east") or "") if x < cols - 1 else "│"
        lines.append(body)
        if y == len(grid) - 1:
            lines.append("└" + "┴".join("─" * width for _ in range(cols)) + "┘")
        else:
            mid = "├"
            for x in range(cols):
                mid += hspan(padded[x].get("south") or "")
                mid += "┼" if x < cols - 1 else "┤"
            lines.append(mid)
    return "\n".join(lines)


def _tag(game: "Game", cid: str) -> str:
    room = game.world.locations.get(cid) or {}
    mark = str(room.get("map_tag") or "")[:1]
    if mark:
        return mark
    for npc in (room.get("npcs") or []):
        data = game.world.npcs.get(str(npc)) or {}
        if data.get("shop"):
            return "$"
    if room.get("rest") is True:
        return "+"
    exits = room.get("exits") or {}
    if any(str(d) in ("up", "down") for d in exits):
        return "^"
    return ""


def _link(game: "Game", a: str, b: str) -> str:
    if not a or not b:
        return ""
    ways = []
    for src, dst in ((a, b), (b, a)):
        room = game.world.locations.get(src) or {}
        for direction, dest in (room.get("exits") or {}).items():
            if game.exit_target(dest) != dst:
                continue
            hidden = dest.get("hidden") if isinstance(dest, dict) else False
            if hidden and direction not in set(game.state.revealed_exits.get(src) or []):
                continue
            locked = False
            if isinstance(dest, dict):
                key = f"{src}:{direction}"
                flagged = dest.get("lock_flag") and dest.get("lock_flag") not in game.state.flags
                if key not in game.state.unlocked and (dest.get("locked") or flagged):
                    locked = True
            ways.append(locked)
    if not ways:
        return "none"
    if len(ways) == 1:
        return "locked" if ways[0] else "one"
    if all(ways):
        return "locked"
    return "open"
