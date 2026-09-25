"""Text effects. No pictures: a line can shout, whisper, shake, or sit in a box."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .util import loc

if TYPE_CHECKING:
    from .engine import Game

PARTICLES = {
    "spark": ("  *   *  *   *", " *  *    * *  *"),
    "rain": (" | |  | | | | |", "  | | |  | | | "),
    "dust": (" .  . .   .  .", "  .   . .  . . "),
    "pulse": (" ·   ·   ·   ·", "   ·   ·   ·  "),
    "ash": (" +  + +   +  +", "  +   + +  + + "),
}


def resolve(game: "Game", spec) -> dict:
    table = game.world.game.get("fx") or {}
    if isinstance(spec, str):
        found = table.get(spec) if isinstance(table, dict) else None
        if isinstance(found, dict):
            return found
        return {"text": spec, "style": "plain"}
    return spec if isinstance(spec, dict) else {}


def render(spec: dict, lang: str) -> list[tuple[str, str]]:
    if not spec:
        return []
    style = str(spec.get("style") or "plain")
    text = loc(spec.get("text") or spec.get("line"), lang)
    color = str(spec.get("color") or _color(style))
    if style == "particles":
        kind = str(spec.get("particles") or spec.get("particle") or "spark")
        rows = PARTICLES.get(kind, PARTICLES["spark"])
        count = max(1, min(int(spec.get("rows") or len(rows)), len(rows)))
        out = [(row, color or "accent") for row in rows[:count]]
        if text:
            out.append((str(text), color or "accent"))
        return out
    if style in ("rule", "beat") or (not text and style == "rule"):
        return [("────────" if style == "rule" else " ", color or "dim")]
    if not text:
        return []
    if style == "shout":
        return [(str(text).upper(), color or "accent")]
    if style == "whisper":
        return [(f"… {text}", color or "dim")]
    if style == "quote":
        return [(f"« {text} »", color or "dim")]
    if style == "center":
        return [(str(text).center(28), color or "accent")]
    if style == "shake":
        return [(f" {text}", color or "danger"), (f"{text} ", color or "danger")]
    if style == "glitch":
        return [(f"░▒ {text} ▒░", color or "danger")]
    if style == "banner":
        bar = "─" * max(4, len(str(text)))
        return [(f"┌{bar}┐", color or "accent"), (f"│{text}│", color or "accent"), (f"└{bar}┘", color or "accent")]
    return [(str(text), color or "fg")]


def play(game: "Game", spec) -> None:
    if isinstance(spec, list):
        for step in spec:
            play(game, step)
        return
    body = resolve(game, spec)
    if not body:
        return
    if body.get("when"):
        from .conditions import check

        if not check(game, body.get("when")):
            return
    steps = body.get("steps")
    repeat = _repeat(body)
    if isinstance(steps, list):
        for _ in range(repeat):
            play(game, steps)
        return
    for _ in range(repeat):
        _once(game, body)


def _repeat(body: dict) -> int:
    try:
        return max(1, min(int(body.get("repeat") or 1), 4))
    except (TypeError, ValueError):
        return 1


def run_on(game: "Game", moment: str, key: str = "") -> None:
    table = game.world.game.get("fx") or {}
    if not isinstance(table, dict):
        return
    hooks = table.get("hooks") or table.get("bind") or {}
    if not isinstance(hooks, dict) or moment not in hooks:
        return
    spec = hooks.get(moment)
    if isinstance(spec, dict) and not _is_effect(spec):
        chosen = spec.get(key) if key else None
        if chosen is None:
            chosen = spec.get("any")
        if chosen is None:
            return
        play(game, chosen)
        return
    play(game, spec)


def _once(game: "Game", body: dict) -> None:
    sound = body.get("sound") or body.get("sfx")
    if sound and getattr(game, "audio", None) is not None:
        game.audio.cue(sound)
    anim = str(body.get("anim") or "")
    delay = int(body.get("delay") or 0)
    for text, color in render(body, game.lang):
        fn = getattr(game.ui, "fx", None)
        if callable(fn):
            fn(text, color, anim, delay)
        else:
            game.say(text)


def _is_effect(spec: dict) -> bool:
    return any(key in spec for key in ("style", "text", "line", "steps", "sound", "sfx", "particles", "anim", "repeat"))


def _color(style: str) -> str:
    return {
        "shout": "accent",
        "whisper": "dim",
        "shake": "danger",
        "glitch": "danger",
        "banner": "accent",
        "rule": "dim",
        "beat": "dim",
        "quote": "dim",
        "center": "accent",
        "particles": "accent",
    }.get(style, "fg")
