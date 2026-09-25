"""Mutable play state. Definitions stay in World; this is the saveable blob."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any


STAT_KEYS = ("str", "dex", "int", "con", "cha", "per")


@dataclass
class StatusEffect:
    id: str
    name: Any
    turns: int
    attack: int = 0
    ac: int = 0
    defense: int = 0
    dot: int = 0
    str_mod: int = 0
    dex_mod: int = 0
    data: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "StatusEffect":
        known = {f.name for f in cls.__dataclass_fields__.values()}
        return cls(**{k: v for k, v in d.items() if k in known})


@dataclass
class Player:
    name: str = "Hero"
    stats: dict = field(default_factory=lambda: {k: 10 for k in STAT_KEYS})
    hp: int = 20
    max_hp: int = 20
    mp: int = 0
    max_mp: int = 0
    gold: int = 0
    xp: int = 0
    level: int = 1
    inventory: list = field(default_factory=list)
    equipment: dict = field(default_factory=dict)  # slot -> item_id
    skills: dict = field(default_factory=dict)  # skill -> bonus
    status: list = field(default_factory=list)
    abilities: list = field(default_factory=list)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["status"] = [
            s.to_dict() if isinstance(s, StatusEffect) else s for s in self.status
        ]
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "Player":
        st = []
        for s in d.get("status") or []:
            st.append(s if isinstance(s, StatusEffect) else StatusEffect.from_dict(s))
        stats = {k: 10 for k in STAT_KEYS}
        stats.update(d.get("stats") or {})
        return cls(
            name=d.get("name") or "Hero",
            stats=stats,
            hp=int(d.get("hp", 20)),
            max_hp=int(d.get("max_hp", 20)),
            mp=int(d.get("mp", 0)),
            max_mp=int(d.get("max_mp", 0)),
            gold=int(d.get("gold", 0)),
            xp=int(d.get("xp", 0)),
            level=int(d.get("level", 1)),
            inventory=list(d.get("inventory") or []),
            equipment=dict(d.get("equipment") or {}),
            skills=dict(d.get("skills") or {}),
            status=st,
            abilities=[str(x) for x in (d.get("abilities") or [])],
        )


@dataclass
class GameState:
    location: str = ""
    flags: set = field(default_factory=set)
    counters: dict = field(default_factory=dict)
    visited: set = field(default_factory=set)
    revealed_exits: dict = field(default_factory=dict)  # loc -> [dir]
    unlocked: set = field(default_factory=set)  # "loc:dir"
    quests: dict = field(default_factory=dict)  # id -> status
    time: int = 0
    location_items: dict = field(default_factory=dict)
    hidden_found: dict = field(default_factory=dict)  # loc -> [item_id]
    location_npcs: dict = field(default_factory=dict)
    defeated: set = field(default_factory=set)
    opened: set = field(default_factory=set)  # container ids "loc:cid"
    shop_stock: dict = field(default_factory=dict)
    journal: list = field(default_factory=list)
    language: str = "ru"
    rng_seed: int = 1
    rng_calls: int = 0
    player: Player = field(default_factory=Player)
    ended: str = ""  # "", "win", "lose"
    once: set = field(default_factory=set)  # fired once-events
    followers: dict = field(default_factory=dict)  # npc id -> {hp, max_hp, attack}
    reputation: dict = field(default_factory=dict)
    hunger: int = 0
    muted: bool = False
    music_volume: int = -1
    sfx_volume: int = -1
    quest_steps: dict = field(default_factory=dict)
    quest_deadlines: dict = field(default_factory=dict)
    heard_rumors: set = field(default_factory=set)
    meters: dict = field(default_factory=dict)
    meter_marks: set = field(default_factory=set)
    map_notes: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "location": self.location,
            "flags": sorted(self.flags),
            "counters": self.counters,
            "visited": sorted(self.visited),
            "revealed_exits": self.revealed_exits,
            "unlocked": sorted(self.unlocked),
            "quests": self.quests,
            "time": self.time,
            "location_items": self.location_items,
            "hidden_found": self.hidden_found,
            "location_npcs": self.location_npcs,
            "defeated": sorted(self.defeated),
            "opened": sorted(self.opened),
            "shop_stock": self.shop_stock,
            "journal": self.journal,
            "language": self.language,
            "rng_seed": self.rng_seed,
            "rng_calls": self.rng_calls,
            "player": self.player.to_dict(),
            "ended": self.ended,
            "once": sorted(self.once),
            "followers": self.followers,
            "reputation": self.reputation,
            "hunger": self.hunger,
            "muted": self.muted,
            "music_volume": self.music_volume,
            "sfx_volume": self.sfx_volume,
            "quest_steps": self.quest_steps,
            "quest_deadlines": self.quest_deadlines,
            "heard_rumors": sorted(self.heard_rumors),
            "meters": self.meters,
            "meter_marks": sorted(self.meter_marks),
            "map_notes": self.map_notes,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "GameState":
        return cls(
            location=d.get("location") or "",
            flags=set(d.get("flags") or []),
            counters=dict(d.get("counters") or {}),
            visited=set(d.get("visited") or []),
            revealed_exits=dict(d.get("revealed_exits") or {}),
            unlocked=set(d.get("unlocked") or []),
            quests=dict(d.get("quests") or {}),
            time=int(d.get("time") or 0),
            location_items=dict(d.get("location_items") or {}),
            hidden_found=dict(d.get("hidden_found") or {}),
            location_npcs=dict(d.get("location_npcs") or {}),
            defeated=set(d.get("defeated") or []),
            opened=set(d.get("opened") or []),
            shop_stock=dict(d.get("shop_stock") or {}),
            journal=list(d.get("journal") or []),
            language=d.get("language") or "ru",
            rng_seed=int(d.get("rng_seed") or 1),
            rng_calls=int(d.get("rng_calls") or 0),
            player=Player.from_dict(d.get("player") or {}),
            ended=d.get("ended") or "",
            once=set(d.get("once") or []),
            followers=dict(d.get("followers") or {}),
            reputation={str(k): int(v) for k, v in (d.get("reputation") or {}).items()},
            hunger=int(d.get("hunger") or 0),
            muted=bool(d.get("muted") or False),
            music_volume=int(d["music_volume"]) if d.get("music_volume") is not None else -1,
            sfx_volume=int(d["sfx_volume"]) if d.get("sfx_volume") is not None else -1,
            quest_steps={str(k): int(v) for k, v in (d.get("quest_steps") or {}).items()},
            quest_deadlines={
                str(k): {"at": int((v or {}).get("at") or 0), "step": int((v or {}).get("step") or 0)}
                for k, v in (d.get("quest_deadlines") or {}).items()
                if isinstance(v, dict)
            },
            heard_rumors=set(d.get("heard_rumors") or []),
            meters={str(k): int(v) for k, v in (d.get("meters") or {}).items()},
            meter_marks=set(d.get("meter_marks") or []),
            map_notes={str(k): str(v) for k, v in (d.get("map_notes") or {}).items()},
        )
