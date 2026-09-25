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
    "loot_tables",
    "abilities",
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
    loot_tables: dict = field(default_factory=dict)
    abilities: dict = field(default_factory=dict)
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
    world.loot_tables = _loot_tables(raw.get("loot_tables"))
    if isinstance(game.get("loot_tables"), dict):
        world.loot_tables.update(_loot_tables(game.get("loot_tables")))
    world.abilities = _index(raw.get("abilities"), "abilities")
    if isinstance(game.get("abilities"), dict):
        for k, v in game["abilities"].items():
            if k not in world.abilities and isinstance(v, dict):
                row = dict(v)
                row.setdefault("id", k)
                world.abilities[k] = row
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
    _apply_includes(world, path)
    _attach_ids(world)
    _validate(world)
    return world


def _loot_tables(data: Any) -> dict:
    if not isinstance(data, dict):
        return {}
    out = {}
    for k, v in data.items():
        if isinstance(v, dict) and "drops" in v:
            out[str(k)] = v["drops"]
        else:
            out[str(k)] = v
    return out


def _apply_includes(world: World, game_dir: Path) -> None:
    from .library import load_include
    from .util import as_list

    rels = as_list(world.game.get("include") or world.game.get("includes"))
    for rel in rels:
        pack = load_include(str(rel), game_dir)
        if not pack:
            world.warnings.append(f"include not found: {rel}")
            continue
        _merge_kind(world.locations, pack.get("locations"))
        _merge_kind(world.items, pack.get("items"))
        _merge_kind(world.npcs, pack.get("npcs"))
        _merge_kind(world.dialogues, pack.get("dialogues"))
        _merge_kind(world.quests, pack.get("quests"))
        _merge_kind(world.encounters, pack.get("encounters"))
        _merge_kind(world.recipes, pack.get("recipes"))
        extra_loot = pack.get("loot_tables") or {}
        for k, v in extra_loot.items():
            if k not in world.loot_tables:
                if isinstance(v, dict) and "drops" in v:
                    world.loot_tables[k] = v["drops"]
                elif isinstance(v, dict) and v.get("id") and "drops" not in v:
                    # entity-shaped; skip
                    world.loot_tables[k] = v.get("drops") or v
                else:
                    world.loot_tables[k] = v


def _merge_kind(dest: dict, src: Optional[dict]) -> None:
    if not src:
        return
    for k, v in src.items():
        if k not in dest:
            dest[k] = v


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

    _warn_dialogues(world)
    _warn_audio(world)
    _warn_regions(world)


def _warn_dialogues(world: World) -> None:
    for did, dlg in (world.dialogues or {}).items():
        if not isinstance(dlg, dict):
            continue
        nodes = dlg.get("nodes") or {}
        if not isinstance(nodes, dict):
            world.warnings.append(f"[dialogue {did}] nodes must be a mapping")
            continue
        start = str(dlg.get("start") or "start")
        if nodes and start not in nodes:
            world.warnings.append(f"[dialogue {did}] start '{start}' has no node")
        for rule in dlg.get("start_if") or []:
            if isinstance(rule, dict) and rule.get("node") and str(rule["node"]) not in nodes:
                world.warnings.append(f"[dialogue {did}] start_if goes to missing '{rule['node']}'")
        for nid, node in nodes.items():
            if not isinstance(node, dict):
                continue
            for i, choice in enumerate(node.get("choices") or [], 1):
                if not isinstance(choice, dict):
                    continue
                goto = choice.get("goto")
                if goto and str(goto) not in nodes:
                    world.warnings.append(
                        f"[dialogue {did}.{nid}] choice {i} goes to missing '{goto}'"
                    )


def _warn_audio(world: World) -> None:
    spec = world.game.get("audio") or {}
    if not isinstance(spec, dict) or not spec:
        return
    root = Path(world.path)
    music = spec.get("music") if isinstance(spec.get("music"), dict) else {}
    sfx = spec.get("sfx") if isinstance(spec.get("sfx"), dict) else {}

    def missing(kind: str, name: str, rel: str) -> None:
        path = Path(str(rel))
        if not path.is_absolute():
            path = root / path
        if not path.is_file():
            world.warnings.append(f"[audio.{kind}.{name}] missing file '{rel}'")

    for name, rel in music.items():
        missing("music", str(name), str(rel))
    for name, rel in sfx.items():
        missing("sfx", str(name), str(rel))

    def known(table: dict, name: str) -> bool:
        if name in table:
            return True
        path = Path(name)
        if not path.is_absolute():
            path = root / path
        return path.is_file()

    for loc_id, loc in world.locations.items():
        clip = loc.get("music")
        if clip and not known(music, str(clip)):
            world.warnings.append(f"[{loc_id}] music '{clip}' is not in audio.music")
    for eid, enc in world.encounters.items():
        for key, table in (("music", music), ("sound", sfx)):
            clip = enc.get(key)
            if clip and not known(table, str(clip)):
                world.warnings.append(f"[encounter {eid}] {key} '{clip}' is not in audio.{key}")
    for iid, item in world.items.items():
        clip = item.get("sound")
        if clip and not known(sfx, str(clip)):
            world.warnings.append(f"[item {iid}] sound '{clip}' is not in audio.sfx")
    cues = spec.get("cues") or spec.get("on") or spec.get(True) or {}
    if isinstance(cues, dict):
        for event, cue in cues.items():
            if isinstance(cue, str) and not known(sfx, cue) and not known(music, cue):
                world.warnings.append(f"[audio.cues.{event}] unknown '{cue}'")
            elif isinstance(cue, dict):
                for key, table in (("music", music), ("sfx", sfx), ("sound", sfx)):
                    clip = cue.get(key)
                    if clip and not known(table, str(clip)):
                        world.warnings.append(f"[audio.cues.{event}] {key} '{clip}' has no file")


def _warn_regions(world: World) -> None:
    regions = world.game.get("regions") or {}
    if not isinstance(regions, dict) or not regions:
        return
    for rid, body in regions.items():
        if not isinstance(body, dict):
            world.warnings.append(f"[region {rid}] must be a mapping")
            continue
        start = body.get("start")
        if start and start not in world.locations:
            world.warnings.append(f"[region {rid}] start '{start}' is not a room")
        for room in body.get("rooms") or []:
            if str(room) not in world.locations:
                world.warnings.append(f"[region {rid}] unknown room '{room}'")
    for road in world.game.get("roads") or []:
        if not isinstance(road, dict):
            continue
        for key in ("from", "to"):
            if str(road.get(key) or "") not in regions:
                world.warnings.append(f"[road] {key} '{road.get(key)}' is not a region")
        enc = road.get("encounter")
        if enc and enc not in world.encounters:
            world.warnings.append(f"[road] unknown encounter '{enc}'")


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
