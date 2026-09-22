"""Loot tables and weighted random picks."""

from __future__ import annotations

from typing import Any, Optional

from .util import as_list, weighted_choice


def resolve_loot(world, spec: Any) -> list[dict]:
    """Flatten a loot field into `{item, chance}` rows.

    Spec may be: item id, table id, `{item, chance}`, `{table}`, or a list of those.
    """
    tables = getattr(world, "loot_tables", None) or {}
    if isinstance(world, dict):
        tables = world.get("loot_tables") or {}
    out: list[dict] = []
    _walk(spec, tables, out, depth=0)
    return out


def _walk(spec: Any, tables: dict, out: list, depth: int) -> None:
    if spec in (None, "", [], {}):
        return
    if depth > 8:
        return
    if isinstance(spec, str):
        if spec in tables:
            table = tables[spec]
            if isinstance(table, dict) and "drops" in table:
                table = table["drops"]
            _walk(table, tables, out, depth + 1)
        else:
            out.append({"item": spec, "chance": 100})
        return
    if isinstance(spec, list):
        for x in spec:
            _walk(x, tables, out, depth + 1)
        return
    if isinstance(spec, dict):
        if spec.get("table"):
            _walk(spec["table"], tables, out, depth + 1)
            return
        if spec.get("drops"):
            _walk(spec["drops"], tables, out, depth + 1)
            return
        if spec.get("item") or spec.get("id"):
            iid = spec.get("item") or spec.get("id")
            if iid:
                out.append({"item": iid, "chance": int(spec.get("chance") or 100)})
            return
        for v in spec.values():
            if isinstance(v, (list, dict)):
                _walk(v, tables, out, depth + 1)


def pick_encounter(table: dict, rng) -> Optional[dict]:
    if not table:
        return None
    entries = table.get("table") or table.get("encounters") or []
    if not entries:
        return None
    pick = weighted_choice(entries, rng)
    if pick is None:
        return None
    if isinstance(pick, str):
        return {"encounter": pick}
    return pick
