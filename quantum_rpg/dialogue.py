"""Dialogue trees from YAML. Numbered choices, conditions, skill checks."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

from .conditions import check, skill_bonus
from .effects import apply as apply_effects
from .i18n import t
from .parser import parse
from .util import loc, roll

if TYPE_CHECKING:
    from .engine import Game


def run(game: "Game", npc_id: str) -> None:
    npc = game.world.npcs.get(npc_id) or {}
    dlg_id = npc.get("dialogue") or npc_id
    dialogue = game.world.dialogues.get(dlg_id)
    if not dialogue:
        text = loc(npc.get("talk") or npc.get("description"), game.lang)
        game.say(text or t(game.lang, "nothing"))
        if npc.get("shop"):
            from . import engine as eng

            eng.open_shop(game, npc_id)
        return

    handled = game.hooks.call("on_talk", game, npc_id)
    if handled:
        return

    start = dialogue.get("start") or "start"
    # allow flag-based start
    for alt in dialogue.get("start_if") or []:
        if isinstance(alt, dict) and check(game, alt.get("when")):
            start = alt.get("node") or start
            break
    node_id = start
    game.in_dialogue = True
    while node_id and game.running and not game.state.ended:
        node = (dialogue.get("nodes") or {}).get(node_id) or {}
        if not node:
            break
        text = loc(node.get("text"), game.lang)
        if text:
            speaker = loc(npc.get("name") or npc_id, game.lang)
            game.say(f"{speaker}: {text}")
        apply_effects(game, node.get("effects"))
        if node.get("end") or node.get("shop"):
            if node.get("shop"):
                from . import engine as eng

                eng.open_shop(game, npc_id)
            break
        choices = _visible_choices(game, node.get("choices") or [])
        if not choices:
            break
        for i, ch in enumerate(choices, 1):
            label = loc(ch.get("text"), game.lang)
            game.say(f"  {i}. {label}")
        raw = (game.ui.read(t(game.lang, "prompt")) or "").strip()
        cmd = parse(raw)
        if cmd and cmd.verb in ("go", "quit", "look", "inventory", "help"):
            game.in_dialogue = False
            if cmd.verb != "look":
                game.handle(raw)
            break
        picked = _pick(raw, choices)
        if picked is None:
            if raw.lower() in ("0", "leave", "уйти", "выход", "quit"):
                break
            game.say(t(game.lang, "unknown"))
            continue
        apply_effects(game, picked.get("effects"))
        if picked.get("shop"):
            from . import engine as eng

            eng.open_shop(game, npc_id)
            break
        if picked.get("end"):
            break
        # skill check branch
        sk = picked.get("skill") or picked.get("skill_check")
        if sk:
            spec = sk if isinstance(sk, dict) else {"skill": sk, "dc": picked.get("dc", 10)}
            skill = spec.get("skill") or spec.get("stat") or "cha"
            dc = int(spec.get("dc") or picked.get("dc") or 10)
            total = roll("1d20", game.rng) + skill_bonus(game, skill)
            ok = total >= dc
            game.say(t(game.lang, "skill_ok" if ok else "skill_fail", roll=total, dc=dc))
            apply_effects(game, picked.get("success_effects" if ok else "fail_effects"))
            node_id = picked.get("success" if ok else "fail") or picked.get("goto")
            if picked.get("end_on_fail") and not ok:
                break
            continue
        node_id = picked.get("goto")
        if picked.get("end") or node_id in (None, False, "end"):
            break
    game.in_dialogue = False


def _visible_choices(game: "Game", choices: list) -> list[dict]:
    out = []
    for ch in choices:
        if not isinstance(ch, dict):
            continue
        if ch.get("when") and not check(game, ch["when"]):
            continue
        out.append(ch)
    return out


def _pick(raw: str, choices: list[dict]) -> Optional[dict]:
    if not raw:
        return None
    if raw.isdigit():
        i = int(raw) - 1
        if 0 <= i < len(choices):
            return choices[i]
        return None
    q = raw.lower()
    hits = []
    for ch in choices:
        label = loc(ch.get("text"), "ru").lower() + " " + loc(ch.get("text"), "en").lower()
        if q in label or q == str(ch.get("goto") or "").lower():
            hits.append(ch)
    if len(hits) == 1:
        return hits[0]
    return None
