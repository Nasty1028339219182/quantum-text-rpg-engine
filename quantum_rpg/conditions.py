"""Evaluate YAML `when:` blocks."""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

from .util import as_list, modifier, roll
from .clock import clock

if TYPE_CHECKING:
    from .engine import Game


def check(game: "Game", cond: Any) -> bool:
    if not cond:
        return True
    if isinstance(cond, list):
        return all(check(game, c) for c in cond)
    if isinstance(cond, str):
        return cond in game.state.flags
    if not isinstance(cond, dict):
        return bool(cond)

    if "all" in cond:
        if not all(check(game, c) for c in as_list(cond["all"])):
            return False
    if "any" in cond:
        if not any(check(game, c) for c in as_list(cond["any"])):
            return False
    if "not" in cond:
        if check(game, cond["not"]):
            return False

    p = game.state.player
    st = game.state

    def _flag(v):
        return str(v) in st.flags

    def _has_item(v):
        return game.has_item(str(v))

    def _quest(v):
        if isinstance(v, dict):
            qid = v.get("id")
            status = v.get("status", "active")
            return st.quests.get(qid) == status
        return st.quests.get(str(v)) == "active"

    def _stat_gte(v):
        if not isinstance(v, dict):
            return False
        return all(int(p.stats.get(k, 0)) >= int(n) for k, n in v.items())

    def _stat_lte(v):
        if not isinstance(v, dict):
            return False
        return all(int(p.stats.get(k, 0)) <= int(n) for k, n in v.items())

    def _counter_gte(v):
        if not isinstance(v, dict):
            return False
        return all(int(st.counters.get(k, 0)) >= int(n) for k, n in v.items())

    def _skill_check(v):
        if not isinstance(v, dict):
            return False
        skill = v.get("skill") or v.get("stat") or "dex"
        dc = int(v.get("dc", 10))
        bonus = int(p.skills.get(skill, 0))
        stat = p.stats.get(skill, p.stats.get(_skill_stat(skill), 10))
        total = roll("1d20", game.rng) + modifier(int(stat)) + bonus
        ok = total >= dc
        game.last_skill_roll = (total, dc, ok)
        return ok

    checkers = {
        "flag": _flag,
        "not_flag": lambda v: not _flag(v),
        "has_item": _has_item,
        "not_item": lambda v: not _has_item(v),
        "has_any_item": lambda v: any(game.has_item(str(i)) for i in as_list(v)),
        "in_location": lambda v: st.location == str(v),
        "visited": lambda v: str(v) in st.visited,
        "gold_gte": lambda v: p.gold >= int(v),
        "gold_lte": lambda v: p.gold <= int(v),
        "hp_gte": lambda v: p.hp >= int(v),
        "hp_lte": lambda v: p.hp <= int(v),
        "hp_pct_lte": lambda v: (p.hp / max(1, p.max_hp) * 100) <= float(v),
        "stat_gte": _stat_gte,
        "stat_lte": _stat_lte,
        "quest": _quest,
        "defeated": lambda v: str(v) in st.defeated,
        "npc_here": lambda v: str(v) in (st.location_npcs.get(st.location) or []),
        "npc_alive": lambda v: str(v) not in st.defeated,
        "counter_gte": _counter_gte,
        "time_gte": lambda v: st.time >= int(v),
        "phase": lambda v: clock(game)[1] == str(v),
        "hour_gte": lambda v: clock(game)[0] >= int(v),
        "equipped": lambda v: str(v) in (p.equipment or {}).values(),
        "once": lambda v: str(v) not in st.once,
        "skill_check": _skill_check,
        "lang": lambda v: st.language == str(v),
    }

    skip = {"all", "any", "not"}
    for key, val in cond.items():
        if key in skip:
            continue
        fn = checkers.get(key)
        if fn is None:
            continue
        if not fn(val):
            return False
    return True


def _skill_stat(skill: str) -> str:
    mapping = {
        "perception": "per",
        "stealth": "dex",
        "athletics": "str",
        "lockpick": "dex",
        "lore": "int",
        "persuasion": "cha",
        "insight": "int",
        "survival": "per",
        "str": "str",
        "dex": "dex",
        "int": "int",
        "con": "con",
        "cha": "cha",
        "per": "per",
    }
    return mapping.get(skill, "dex")


def skill_bonus(game: "Game", skill: str) -> int:
    p = game.state.player
    stat_key = _skill_stat(skill)
    stat = int(p.stats.get(skill, p.stats.get(stat_key, 10)))
    return modifier(stat) + int(p.skills.get(skill, 0))
