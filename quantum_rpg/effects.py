"""Apply YAML `effects:` blocks to the running game."""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

from .conditions import check
from .i18n import t
from .state import StatusEffect
from .util import as_effects, as_list, loc, roll

if TYPE_CHECKING:
    from .engine import Game


def apply(game: "Game", effects: Any) -> None:
    for eff in as_effects(effects):
        _apply_one(game, eff)


def _apply_one(game: "Game", eff: dict) -> None:
    if not isinstance(eff, dict):
        return
    if "when" in eff and not check(game, eff["when"]):
        return
    if "effects" in eff and len(eff) <= 3:
        apply(game, eff["effects"])
        if "message" not in eff and "set_flag" not in eff:
            return

    p = game.state.player
    st = game.state
    lang = st.language

    def msg(value):
        text = loc(value, lang)
        if text:
            game.say(text)

    if "message" in eff:
        msg(eff["message"])
    if "journal" in eff:
        entry = loc(eff["journal"], lang)
        if entry and entry not in st.journal:
            st.journal.append(entry)
            game.say(entry)
    if "set_flag" in eff:
        for f in as_list(eff["set_flag"]):
            st.flags.add(str(f))
    if "clear_flag" in eff:
        for f in as_list(eff["clear_flag"]):
            st.flags.discard(str(f))
    if "toggle_flag" in eff:
        f = str(eff["toggle_flag"])
        if f in st.flags:
            st.flags.discard(f)
        else:
            st.flags.add(f)
    if "give_item" in eff:
        for iid in as_list(eff["give_item"]):
            game.give_item(str(iid), silent=False)
    if "take_item" in eff:
        for iid in as_list(eff["take_item"]):
            game.take_from_inv(str(iid), silent=True)
    if "give_gold" in eff:
        n = int(eff["give_gold"])
        p.gold += n
        game.say(t(lang, "gold_gain", n=n))
    if "take_gold" in eff:
        n = int(eff["take_gold"])
        p.gold = max(0, p.gold - n)
        game.say(t(lang, "gold_lose", n=n))
    if "heal" in eff:
        n = roll(eff["heal"], game.rng)
        old = p.hp
        p.hp = min(p.max_hp, p.hp + n)
        game.say(t(lang, "healed", n=p.hp - old))
    if "damage" in eff:
        n = roll(eff["damage"], game.rng)
        p.hp = max(0, p.hp - n)
        game.say(t(lang, "damaged", n=n))
        if p.hp <= 0:
            game.finish("lose")
    if "restore_mp" in eff:
        n = roll(eff["restore_mp"], game.rng)
        p.mp = min(p.max_mp, p.mp + n)
    if "spend_mp" in eff:
        p.mp = max(0, p.mp - int(eff["spend_mp"]))
    if "add_xp" in eff:
        game.add_xp(int(eff["add_xp"]))
    if "modify_stat" in eff:
        data = eff["modify_stat"] or {}
        for k, v in data.items():
            p.stats[k] = int(p.stats.get(k, 10)) + int(v)
    if "teleport" in eff:
        game.move_to(str(eff["teleport"]), silent=False)
    if "start_quest" in eff:
        qid = str(eff["start_quest"])
        if st.quests.get(qid) not in ("done", "failed"):
            st.quests[qid] = "active"
            q = game.world.quests.get(qid, {})
            title = loc(q.get("name") or qid, lang)
            game.say(f"* {title}")
            desc = loc(q.get("start_text") or q.get("description"), lang)
            if desc:
                game.say(desc)
    if "complete_quest" in eff:
        qid = str(eff["complete_quest"])
        if st.quests.get(qid) == "done":
            pass
        else:
            st.quests[qid] = "done"
            q = game.world.quests.get(qid, {})
            reward = q.get("reward")
            if reward:
                apply(game, reward)
            text = loc(q.get("done_text"), lang)
            if text:
                game.say(text)
    if "fail_quest" in eff:
        st.quests[str(eff["fail_quest"])] = "failed"
    if "start_combat" in eff:
        game.start_combat(str(eff["start_combat"]))
    if "reveal_exit" in eff:
        info = eff["reveal_exit"]
        if isinstance(info, dict):
            loc_id = info.get("location") or st.location
            direction = info.get("dir") or info.get("direction")
        else:
            loc_id, direction = st.location, str(info)
        st.revealed_exits.setdefault(loc_id, [])
        if direction not in st.revealed_exits[loc_id]:
            st.revealed_exits[loc_id].append(direction)
    if "unlock" in eff:
        info = eff["unlock"]
        if isinstance(info, dict):
            key = f"{info.get('location') or st.location}:{info.get('dir') or info.get('direction')}"
        elif ":" in str(info):
            key = str(info)
        else:
            key = f"{st.location}:{info}"
        st.unlocked.add(key)
        game.say(t(lang, "unlocked"))
    if "lock" in eff:
        info = eff["lock"]
        key = f"{st.location}:{info}" if not isinstance(info, dict) else (
            f"{info.get('location') or st.location}:{info.get('dir')}"
        )
        st.unlocked.discard(key)
    if "spawn_item" in eff:
        info = eff["spawn_item"]
        if isinstance(info, dict):
            iid = str(info.get("item") or info.get("id"))
            where = info.get("location") or st.location
        else:
            iid, where = str(info), st.location
        game.place_item(where, iid)
    if "spawn_npc" in eff:
        info = eff["spawn_npc"]
        if isinstance(info, dict):
            nid = str(info.get("npc") or info.get("id"))
            where = info.get("location") or st.location
        else:
            nid, where = str(info), st.location
        game.place_npc(where, nid)
    if "remove_npc" in eff:
        nid = str(eff["remove_npc"])
        game.remove_npc(nid)
    if "follow" in eff:
        game.add_follower(eff["follow"])
    if "unfollow" in eff:
        game.remove_follower(str(eff["unfollow"]))
    if "rep" in eff:
        game.change_rep(eff["rep"])
    if "set_rep" in eff:
        game.set_rep(eff["set_rep"])
    if "sound" in eff or "music" in eff or "sfx" in eff:
        game.audio.cue(eff if "sfx" in eff or "music" in eff else {"sound": eff.get("sound")})
    if "rest" in eff and eff["rest"]:
        p.hp = p.max_hp
        p.mp = p.max_mp
        game.say(t(lang, "rest_ok"))
    if "game_over" in eff:
        game.finish(str(eff["game_over"]))
    if "add_status" in eff:
        data = dict(eff["add_status"])
        sid = str(data.get("id") or data.get("name") or "effect")
        p.status.append(
            StatusEffect(
                id=sid,
                name=data.get("name") or sid,
                turns=int(data.get("turns", 3)),
                attack=int(data.get("attack", 0)),
                ac=int(data.get("ac", 0)),
                defense=int(data.get("defense", 0)),
                dot=int(data.get("dot", 0)),
                str_mod=int(data.get("str_mod", 0)),
                dex_mod=int(data.get("dex_mod", 0)),
                data=data,
            )
        )
    if "remove_status" in eff:
        rid = str(eff["remove_status"])
        p.status = [s for s in p.status if getattr(s, "id", s) != rid]
    if "counter_add" in eff:
        data = eff["counter_add"]
        if isinstance(data, dict):
            for k, v in data.items():
                st.counters[k] = int(st.counters.get(k, 0)) + int(v)
    if "counter_set" in eff:
        data = eff["counter_set"]
        if isinstance(data, dict):
            for k, v in data.items():
                st.counters[k] = int(v)
    if "hook" in eff:
        name = str(eff["hook"])
        game.hooks.call(name, game, **(eff.get("args") or {}))
    if "once_id" in eff:
        st.once.add(str(eff["once_id"]))
