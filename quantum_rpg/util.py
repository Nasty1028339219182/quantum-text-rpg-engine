"""Helpers: localization, dice, wrapping, alias matching."""

from __future__ import annotations

import re
import textwrap
from typing import Any, Iterable, Mapping, Optional

DICE_RE = re.compile(r"^(\d*)d(\d+)([+-]\d+)?$", re.I)


def loc(value: Any, lang: str = "ru") -> str:
    """Resolve a bilingual field `{ru: ..., en: ...}` or a plain string."""
    if value is None:
        return ""
    if isinstance(value, Mapping):
        for key in (lang, "en", "ru"):
            if key in value and value[key] not in (None, ""):
                return str(value[key])
        for v in value.values():
            if v not in (None, ""):
                return str(v)
        return ""
    return str(value)


def wrap(text: str, width: int = 72) -> str:
    if not text:
        return ""
    lines: list[str] = []
    for para in str(text).split("\n"):
        if not para.strip():
            lines.append("")
        else:
            lines.extend(textwrap.wrap(para, width=width) or [""])
    return "\n".join(lines)


def modifier(stat: int) -> int:
    return (int(stat) - 10) // 2


def roll(expr: Any, rng) -> int:
    """Roll `1d8+2`, `d20`, `2d6-1`, or a plain integer."""
    if expr is None:
        return 0
    if isinstance(expr, bool):
        return int(expr)
    if isinstance(expr, (int, float)):
        return int(expr)
    s = str(expr).strip().replace(" ", "")
    if not s:
        return 0
    m = DICE_RE.match(s)
    if not m:
        try:
            return int(s)
        except ValueError:
            return 0
    n = int(m.group(1) or 1)
    sides = int(m.group(2))
    bonus = int(m.group(3) or 0)
    total = bonus
    for _ in range(max(1, n)):
        total += rng.randint(1, max(1, sides))
    return total


def norm(s: str) -> str:
    return (s or "").strip().lower()


def as_list(value: Any) -> list:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def weighted_choice(entries: list, rng):
    if not entries:
        return None
    weights = []
    for e in entries:
        if isinstance(e, dict):
            weights.append(max(1, int(e.get("weight") or 1)))
        else:
            weights.append(1)
    total = sum(weights) or 1
    r = rng.randint(1, total)
    acc = 0
    picked = entries[-1]
    for e, w in zip(entries, weights):
        acc += w
        if r <= acc:
            picked = e
            break
    return picked


def as_effects(value: Any) -> list[dict]:
    """Normalize effects to a list of dicts."""
    if not value:
        return []
    if isinstance(value, list):
        out: list[dict] = []
        for item in value:
            if isinstance(item, dict):
                out.append(item)
            elif isinstance(item, str):
                out.append({"message": item})
        return out
    if isinstance(value, dict):
        return [value]
    if isinstance(value, str):
        return [{"message": value}]
    return []


def match_alias(query: str, aliases: Iterable[str]) -> bool:
    q = norm(query)
    if not q:
        return False
    for a in aliases:
        if norm(str(a)) == q:
            return True
    return False


def entity_names(data: Mapping[str, Any], lang: str) -> list[str]:
    names = [data.get("id", "")]
    names.append(loc(data.get("name"), lang))
    names.extend(as_list(data.get("aliases")))
    return [n for n in names if n]


def match_entity(query: str, entities: Mapping[str, Mapping[str, Any]], lang: str) -> Optional[str]:
    """Match a typed name/alias/id against a dict of entities. Returns id or None."""
    q = norm(query)
    if not q:
        return None
    if q in entities:
        return q
    # exact name / alias
    for eid, data in entities.items():
        names = [norm(x) for x in entity_names(data, lang)]
        if q in names:
            return eid
    # startswith / contains
    hits = []
    for eid, data in entities.items():
        names = [norm(x) for x in entity_names(data, lang)]
        if any(n.startswith(q) or q.startswith(n) for n in names if n):
            hits.append(eid)
            continue
        if any(q in n or n in q for n in names if n and len(q) >= 3):
            hits.append(eid)
    if len(hits) == 1:
        return hits[0]
    return None


def deep_copy(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: deep_copy(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [deep_copy(v) for v in obj]
    return obj
