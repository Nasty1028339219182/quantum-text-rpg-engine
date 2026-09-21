"""Load a game folder of YAML files and optional hooks.py."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import yaml

from .util import as_list, deep_copy

KNOWN_FILES = (
    "game",
    "locations",
    "items",
    "npcs",
    "dialogues",
    "quests",
    "encounters",
    "recipes",
    "events",
    "skills",
)


@dataclass
class World:
    path: Path
    game: dict = field(default_factory=dict)
    locations: dict = field(default_factory=dict)
    items: dict = field(default_factory=dict)
    npcs: dict = field(default_factory=dict)
    dialogues: dict = field(default_factory=dict)
    quests: dict = field(default_factory=dict)
    encounters: dict = field(default_factory=dict)
    recipes: dict = field(default_factory=dict)
    events: list = field(default_factory=list)
    skills: dict = field(default_factory=dict)
    warnings: list = field(default_factory=list)
    errors: list = field(default_factory=list)

    @property
    def title(self) -> Any:
        return self.game.get("title") or self.path.name

    @property
    def start_location(self) -> str:
        start = self.game.get("start") or {}
        if isinstance(start, str):
            return start
        return start.get("location") or self.game.get("start_location") or ""


def _read_yaml(path: Path) -> Any:
    text = path.read_text(encoding="utf-8")
    data = yaml.safe_load(text)
    return data


def _index(data: Any, kind: str) -> dict:
    if not data:
        return {}
    if isinstance(data, dict):
        # allow {items: {...}} wrapping
        if kind in data and isinstance(data[kind], dict) and len(data) == 1:
            data = data[kind]
        out = {}
        for k, v in data.items():
            if v is None:
                v = {}
            if not isinstance(v, dict):
                continue
            item = dict(v)
            item.setdefault("id", k)
            out[k] = item
        return out
    if isinstance(data, list):
        out = {}
        for v in data:
            if not isinstance(v, dict) or "id" not in v:
                continue
            out[v["id"]] = v
        return out
    return {}


def load_world(game_dir: str | Path) -> World:
    path = Path(game_dir).resolve()
    if not path.exists():
        raise FileNotFoundError(f"Game folder not found: {path}")
    if path.is_file():
        path = path.parent

    world = World(path=path)
    files = {p.stem: p for p in path.glob("*.yaml")}
    files.update({p.stem: p for p in path.glob("*.yml")})

    raw: dict[str, Any] = {}
    for name in KNOWN_FILES:
        fp = files.get(name)
        if fp is None:
            raw[name] = None
            continue
        try:
            raw[name] = _read_yaml(fp)
        except yaml.YAMLError as exc:
            world.errors.append(f"[{fp.name}] YAML error: {exc}")
            raw[name] = None

    game = raw.get("game") or {}
    if not isinstance(game, dict):
        world.errors.append("[game.yaml] must be a mapping")
        game = {}
    world.game = game
    world.locations = _index(raw.get("locations"), "locations")
    world.items = _index(raw.get("items"), "items")
    world.npcs = _index(raw.get("npcs"), "npcs")
    world.dialogues = _index(raw.get("dialogues"), "dialogues")
    world.quests = _index(raw.get("quests"), "quests")
    world.encounters = _index(raw.get("encounters"), "encounters")
    world.recipes = _index(raw.get("recipes"), "recipes")
    world.skills = _index(raw.get("skills"), "skills")
    events = raw.get("events")
    if isinstance(events, dict):
        world.events = []
        for k, v in events.items():
            if isinstance(v, dict):
                item = dict(v)
                item.setdefault("id", k)
                world.events.append(item)
    elif isinstance(events, list):
        world.events = [e for e in events if isinstance(e, dict)]
    else:
        world.events = []

    _attach_ids(world)
    _validate(world)
    return world


def _attach_ids(world: World) -> None:
    for loc_id, loc in world.locations.items():
        loc["id"] = loc_id
        items = []
        hidden = []
        for entry in as_list(loc.get("items")):
            if isinstance(entry, str):
                items.append(entry)
            elif isinstance(entry, dict) and "id" in entry:
                if entry.get("hidden"):
                    hidden.append(entry["id"])
                else:
                    items.append(entry["id"])
        loc["_item_ids"] = items
        extra_hidden = [x for x in as_list(loc.get("hidden_items")) if isinstance(x, str)]
        loc["_hidden_ids"] = hidden + extra_hidden
        npcs = []
        for entry in as_list(loc.get("npcs")):
            if isinstance(entry, str):
                npcs.append(entry)
            elif isinstance(entry, dict) and "id" in entry:
                npcs.append(entry["id"])
        loc["_npc_ids"] = npcs
    for nid, npc in world.npcs.items():
        npc["id"] = nid
        loc_id = npc.get("location")
        if loc_id and loc_id in world.locations:
            if nid not in world.locations[loc_id]["_npc_ids"]:
                world.locations[loc_id]["_npc_ids"].append(nid)


def _validate(world: World) -> None:
    if not world.locations:
        world.errors.append("No locations defined (locations.yaml).")
    start = world.start_location
    if start and start not in world.locations:
        world.errors.append(f"Start location '{start}' does not exist.")
    if not start and world.locations:
        world.warnings.append("No start location set; using the first location.")

    for loc_id, loc in world.locations.items():
        exits = loc.get("exits") or {}
        if not isinstance(exits, dict):
            world.errors.append(f"[{loc_id}] exits must be a mapping")
            continue
        for direction, dest in exits.items():
            target = dest if isinstance(dest, str) else (dest or {}).get("to")
            if not target:
                world.errors.append(f"[{loc_id}.exits.{direction}] missing 'to'")
            elif target not in world.locations:
                world.errors.append(
                    f"[{loc_id}.exits.{direction}] unknown location '{target}'"
                )
            hidden = dest.get("hidden") if isinstance(dest, dict) else False
            if hidden is True:
                pass
        for iid in loc.get("_item_ids", []) + loc.get("_hidden_ids", []):
            if iid not in world.items:
                world.warnings.append(f"[{loc_id}] unknown item '{iid}'")
        for nid in loc.get("_npc_ids", []):
            if nid not in world.npcs:
                world.warnings.append(f"[{loc_id}] unknown npc '{nid}'")

    for nid, npc in world.npcs.items():
        dlg = npc.get("dialogue")
        if dlg and dlg not in world.dialogues and dlg != nid:
            # dialogue may be inline or same id
            if dlg not in world.dialogues:
                world.warnings.append(f"[npc {nid}] unknown dialogue '{dlg}'")
        enc = npc.get("encounter")
        if enc and enc not in world.encounters:
            world.warnings.append(f"[npc {nid}] unknown encounter '{enc}'")

    for iid, item in world.items.items():
        combo = item.get("combine") or {}
        if combo:
            for other in as_list(combo.get("with")):
                if other not in world.items:
                    world.warnings.append(f"[item {iid}] combine.with unknown '{other}'")
            result = combo.get("result")
            if result and result not in world.items:
                world.warnings.append(f"[item {iid}] combine.result unknown '{result}'")


def initial_location_items(world: World) -> dict[str, list]:
    out: dict[str, list] = {}
    for loc_id, loc in world.locations.items():
        out[loc_id] = list(loc.get("_item_ids") or [])
    return deep_copy(out)


def initial_location_npcs(world: World) -> dict[str, list]:
    out: dict[str, list] = {}
    for loc_id, loc in world.locations.items():
        out[loc_id] = list(loc.get("_npc_ids") or [])
    return deep_copy(out)
