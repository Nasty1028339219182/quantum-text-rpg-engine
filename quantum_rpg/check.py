"""Read a game and say what does not join up. It does not fix anything."""

from __future__ import annotations

import re

from .loader import World
from .util import as_list

_ID = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def problems(world: World) -> list[str]:
    out: list[str] = []
    locs = world.locations
    items = world.items
    npcs = world.npcs
    quests = world.quests
    encounters = world.encounters
    game = world.game if isinstance(world.game, dict) else {}
    fx = game.get("fx") if isinstance(game.get("fx"), dict) else {}
    scenes = game.get("scenes") if isinstance(game.get("scenes"), dict) else {}
    meters = set(game["meters"]) if isinstance(game.get("meters"), dict) else set()
    if isinstance(game.get("hunger"), dict) and game["hunger"].get("max"):
        meters.add("hunger")

    def add(text: str) -> None:
        if text not in out:
            out.append(text)

    def fx_known(name: str) -> bool:
        if name in fx and name not in ("hooks", "bind"):
            return True
        return not _ID.match(name)

    def scene_known(name: str) -> bool:
        return name in scenes

    def check_fx(spec, where: str) -> None:
        if isinstance(spec, str):
            if not fx_known(spec):
                add(f"[{where}] fx '{spec}' does not exist")
            return
        if isinstance(spec, list):
            for step in spec:
                check_fx(step, where)
            return
        if not isinstance(spec, dict):
            return
        if _effect_body(spec):
            if isinstance(spec.get("steps"), list):
                check_fx(spec.get("steps"), where)
            return
        for key, value in spec.items():
            check_fx(value, f"{where}.{key}")

    def check_scene(spec, where: str) -> None:
        name = spec.get("id") if isinstance(spec, dict) else spec
        if isinstance(spec, dict) and spec.get("scene"):
            name = spec.get("scene")
        name = str(name or "")
        if name and not scene_known(name):
            add(f"[{where}] scene '{name}' does not exist")

    def check_ref(kind: str, table: dict, value, where: str) -> None:
        ref = _ref(value)
        if ref and ref not in table:
            add(f"[{where}] {kind} '{ref}' does not exist")

    def check_effects(node, where: str) -> None:
        if isinstance(node, list):
            for step in node:
                check_effects(step, where)
            return
        if not isinstance(node, dict):
            return
        pairs = (
            ("give_item", "item", items),
            ("take_item", "item", items),
            ("spawn_item", "item", items),
            ("start_quest", "quest", quests),
            ("complete_quest", "quest", quests),
            ("fail_quest", "quest", quests),
            ("advance_quest", "quest", quests),
            ("start_combat", "encounter", encounters),
            ("spawn_npc", "npc", npcs),
            ("remove_npc", "npc", npcs),
            ("teleport", "location", locs),
        )
        for key, kind, table in pairs:
            if key in node:
                check_ref(kind, table, node.get(key), where)
        if "fx" in node:
            check_fx(node.get("fx"), where)
        if "scene" in node:
            check_scene(node.get("scene"), where)
        if "when" in node:
            check_when(node.get("when"), where)

    def check_when(node, where: str) -> None:
        if isinstance(node, list):
            for step in node:
                check_when(step, where)
            return
        if not isinstance(node, dict):
            return
        meter = node.get("meter")
        if isinstance(meter, dict):
            for mid in meter:
                if str(mid) not in meters:
                    add(f"[{where}] meter '{mid}' is not defined")
        for key in ("all", "any", "not"):
            if key in node:
                check_when(node.get(key), where)

    for loc_id, room in locs.items():
        if not isinstance(room, dict):
            continue
        exits = room.get("exits") or {}
        if isinstance(exits, dict):
            for direction, dest in exits.items():
                target = dest if isinstance(dest, str) else (dest or {}).get("to")
                if target and target not in locs:
                    add(f"[{loc_id}] exit {direction} goes to missing '{target}'")
        for key in ("on_enter", "on_first_enter", "on_rest"):
            check_effects(room.get(key), loc_id)
        search = room.get("search")
        if isinstance(search, dict):
            check_effects(search.get("effects"), loc_id)

    for cell in _map_rooms(game.get("map")):
        if cell not in locs:
            add(f"[map] room '{cell}' is not a location")

    for qid, quest in quests.items():
        if not isinstance(quest, dict):
            continue
        if not str(qid).strip():
            add("[quest] empty id")
        check_effects(quest.get("reward"), f"quest {qid}")
        for index, step in enumerate(quest.get("steps") or [], 1):
            if isinstance(step, dict) and "id" in step and not str(step.get("id") or "").strip():
                add(f"[quest {qid}] step {index} has an empty id")

    rumors = game.get("rumors") if isinstance(game.get("rumors"), dict) else {}
    for rid, rumor in rumors.items():
        if not isinstance(rumor, dict):
            continue
        if not str(rid).strip():
            add("[rumor] empty id")
        for nid in as_list(rumor.get("knows")):
            if str(nid) not in npcs:
                add(f"[rumor {rid}] knows missing npc '{nid}'")
        check_when(rumor.get("when"), f"rumor {rid}")

    hooks = fx.get("hooks") if isinstance(fx.get("hooks"), dict) else {}
    for moment, spec in hooks.items():
        check_fx(spec, f"fx.hooks.{moment}")

    for sid, scene in scenes.items():
        if isinstance(scene, dict):
            _scene_beats(
                scene.get("beats") or scene.get("steps") or [],
                f"scene {sid}",
                add,
                check_effects,
                check_fx,
                check_when,
                check_scene,
            )

    for eid, enc in encounters.items():
        if not isinstance(enc, dict):
            continue
        for ref in enc.get("enemies") or []:
            if str(ref) not in encounters:
                add(f"[encounter {eid}] enemy '{ref}' does not exist")
        check_effects(enc.get("on_win"), f"encounter {eid}")
        check_effects(enc.get("on_lose"), f"encounter {eid}")
        for row in enc.get("actions") or []:
            if isinstance(row, dict):
                check_effects(row.get("effects"), f"encounter {eid}")
                check_fx(row.get("fx"), f"encounter {eid}")
                check_when(row.get("when"), f"encounter {eid}")
        for row in enc.get("phases") or []:
            if isinstance(row, dict):
                check_effects(row.get("effects"), f"encounter {eid}")

    return out


def _scene_beats(beats, where, add, check_effects, check_fx, check_when, check_scene) -> None:
    if not isinstance(beats, list):
        return
    marks = set()
    for beat in beats:
        if isinstance(beat, dict) and beat.get("mark"):
            marks.add(str(beat.get("mark")))
    for beat in beats:
        if not isinstance(beat, dict):
            continue
        check_effects(beat.get("effects"), where)
        check_fx(beat.get("fx"), where)
        check_when(beat.get("when"), where)
        if beat.get("scene"):
            check_scene(beat.get("scene"), where)
        goto = beat.get("goto")
        if goto and str(goto) not in marks:
            add(f"[{where}] goto '{goto}' has no mark")
        choose = beat.get("choose")
        if isinstance(choose, dict):
            for option in choose.get("options") or []:
                if not isinstance(option, dict):
                    continue
                dest = option.get("goto")
                if dest and str(dest) not in marks:
                    add(f"[{where}] choice goes to missing '{dest}'")
                check_effects(option.get("effects"), where)
                check_when(option.get("when"), where)
                _scene_beats(
                    option.get("beats") or [],
                    where,
                    add,
                    check_effects,
                    check_fx,
                    check_when,
                    check_scene,
                )


def _map_rooms(raw) -> list[str]:
    found: list[str] = []

    def walk(node) -> None:
        if isinstance(node, list):
            for row in node:
                if isinstance(row, list):
                    for cell in row:
                        text = str(cell or "").strip()
                        if text:
                            found.append(text)
                else:
                    walk(row)
        elif isinstance(node, dict):
            for key, value in node.items():
                if key in ("reveal", "name"):
                    continue
                walk(value)

    walk(raw)
    return found


def _ref(value) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        for key in ("id", "quest", "to", "item", "npc", "scene"):
            if value.get(key):
                return str(value.get(key))
    return ""


def _effect_body(spec: dict) -> bool:
    return any(key in spec for key in ("style", "text", "line", "steps", "sound", "sfx", "particles", "anim", "repeat"))
