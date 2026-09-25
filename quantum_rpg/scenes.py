"""A scene is one moment: lines, a branch, a question. No pictures."""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from .conditions import check
from .util import loc

if TYPE_CHECKING:
    from .engine import Game


def play(game: "Game", spec) -> None:
    if isinstance(spec, str):
        sid, again = spec, False
    elif isinstance(spec, dict):
        sid = str(spec.get("scene") or spec.get("id") or "")
        again = bool(spec.get("again"))
    else:
        return
    table = game.world.game.get("scenes") or {}
    scene = table.get(sid) if isinstance(table, dict) else None
    if not isinstance(scene, dict):
        return
    once = scene.get("once", True)
    key = f"scene:{sid}"
    if once and not again and key in game.state.once:
        return
    playing = game.__dict__.setdefault("_scenes", set())
    if sid in playing:
        return
    playing.add(sid)
    beats = scene.get("beats") or scene.get("steps") or []
    finished = False
    try:
        if isinstance(beats, list):
            finished = _run(game, beats)
    finally:
        playing.discard(sid)
    if once and finished:
        game.state.once.add(key)


def _run(game: "Game", beats: list) -> bool:
    marks = {}
    for index, beat in enumerate(beats):
        if isinstance(beat, dict) and beat.get("mark"):
            marks[str(beat.get("mark"))] = index
    index = 0
    guard = 0
    while index < len(beats) and guard < 200 and not game.state.ended:
        jump = _beat(game, beats[index])
        guard += 1
        if jump == "stop":
            return False
        if jump:
            if jump not in marks:
                return False
            index = marks[jump]
        else:
            index += 1
    return True


def _beat(game: "Game", beat) -> Optional[str]:
    if isinstance(beat, str):
        game.say(beat)
        return None
    if not isinstance(beat, dict):
        return None
    if beat.get("when") and not check(game, beat.get("when")):
        return None
    if beat.get("mark") and not any(k in beat for k in ("say", "fx", "effects", "choose", "ask", "goto", "scene", "end")):
        return None
    if beat.get("end") or beat.get("stop"):
        return "stop"
    if beat.get("say") or beat.get("text"):
        _say(game, beat)
    if beat.get("fx"):
        from . import fx

        fx.play(game, beat.get("fx"))
    if beat.get("effects"):
        from . import effects

        effects.apply(game, beat.get("effects"))
    if beat.get("scene"):
        play(game, beat.get("scene"))
    if beat.get("ask"):
        if _ask(game, beat.get("ask")) == "stop":
            return "stop"
    if beat.get("choose"):
        return _choose(game, beat.get("choose"))
    if beat.get("goto"):
        return str(beat.get("goto"))
    return None


def _say(game: "Game", beat: dict) -> None:
    text = loc(beat.get("say") or beat.get("text"), game.lang)
    if not text:
        return
    who = beat.get("who") or beat.get("speaker")
    if who:
        if isinstance(who, str) and who in game.world.npcs:
            name = game.npc_name(who)
        else:
            name = loc(who, game.lang)
        game.say(f"{name}: {text}")
        return
    game.say(text)


def _ask(game: "Game", spec) -> Optional[str]:
    if isinstance(spec, str):
        spec = {"prompt": spec, "var": spec}
    if not isinstance(spec, dict):
        return None
    prompt = loc(spec.get("prompt") or spec.get("say"), game.lang)
    if prompt:
        game.say(prompt)
    game.set_choices([])
    raw = (game.ui.read("> ") or "").strip()
    if raw.lower() == "quit":
        return "stop"
    key = str(spec.get("var") or spec.get("flag") or "")
    if key:
        game.state.vars[key] = raw
        if spec.get("flag"):
            game.state.flags.add(str(spec.get("flag")))
    return None


def _choose(game: "Game", spec) -> Optional[str]:
    if not isinstance(spec, dict):
        return None
    options = []
    for row in spec.get("options") or []:
        if isinstance(row, dict) and (not row.get("when") or check(game, row.get("when"))):
            options.append(row)
    if not options:
        return None
    prompt = loc(spec.get("prompt"), game.lang)
    if prompt:
        game.say(prompt)
    choices = []
    for index, row in enumerate(options, 1):
        label = loc(row.get("label") or row.get("say") or index, game.lang)
        game.say(f"  {index}. {label}")
        choices.append({"label": label, "command": str(index)})
    game.set_choices(choices)
    picked = None
    while game.running and not game.state.ended:
        raw = (game.ui.read("> ") or "").strip()
        if raw.lower() == "quit":
            game.set_choices([])
            return "stop"
        if not raw:
            picked = options[0]
            break
        if raw.isdigit() and 1 <= int(raw) <= len(options):
            picked = options[int(raw) - 1]
            break
        low = raw.lower()
        for row in options:
            label = loc(row.get("label") or "", game.lang).lower()
            if low and low == label:
                picked = row
                break
        if picked:
            break
        from .parser import parse

        cmd = parse(raw)
        if cmd and cmd.verb not in ("", "unknown"):
            game.set_choices([])
            game.handle(raw)
            return "stop"
        if prompt:
            game.say(prompt)
    game.set_choices([])
    if not picked:
        return None
    if picked.get("effects"):
        from . import effects

        effects.apply(game, picked.get("effects"))
    if picked.get("beats"):
        _run(game, picked.get("beats") or [])
    if picked.get("goto"):
        return str(picked.get("goto"))
    return None
