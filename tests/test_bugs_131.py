from pathlib import Path

from quantum_rpg.combat import _victory
from quantum_rpg.effects import apply
from quantum_rpg.engine import Game
from quantum_rpg.loader import load_world
from quantum_rpg.loot import resolve_loot
from quantum_rpg.ui import ScriptedIO

ROOT = Path(__file__).resolve().parents[1]


def test_bilingual_player_name():
    w = load_world(ROOT / "games" / "greyford")
    g = Game(w, ui=ScriptedIO(["quit"]), language="ru", seed=1, ask_name=False)
    assert g.state.player.name == "Путник"
    g2 = Game(w, ui=ScriptedIO(["quit"]), language="en", seed=1, ask_name=False)
    assert g2.state.player.name == "Traveler"


def test_class_prompt_snapshot_mode():
    w = load_world(ROOT / "games" / "greyford")
    g = Game(w, ui=ScriptedIO(["quit"]), language="ru", seed=1, ask_name=False)
    g.set_choices([{"label": "1. Воин", "command": "1"}])
    snap = g.snapshot()
    assert snap["mode"] == "prompt"
    assert snap["choices"]


def test_complete_quest_reward_once():
    w = load_world(ROOT / "games" / "greyford")
    g = Game(w, ui=ScriptedIO(["quit"]), language="ru", seed=1, ask_name=False)
    gold = g.state.player.gold
    apply(g, [{"complete_quest": "missing_mira"}])
    apply(g, [{"complete_quest": "missing_mira"}])
    # reward is add_xp 20, not gold — gold must not jump twice either
    assert g.state.quests["missing_mira"] == "done"
    assert g.state.player.gold == gold
    assert g.state.player.xp == 20


def test_loot_no_id_as_item_from_table_meta():
    w = load_world(ROOT / "games" / "greyford")
    rows = resolve_loot(w, {"id": "traveler_pouch", "drops": [{"item": "bread", "chance": 100}]})
    assert {r["item"] for r in rows} == {"bread"}


def test_solo_encounter_loot_not_doubled():
    w = load_world(ROOT / "games" / "greyford")
    g = Game(w, ui=ScriptedIO(["quit"]), language="ru", seed=1, ask_name=False)
    enc = dict(w.encounters["wolf"])
    enc["id"] = "wolf"
    enc["loot"] = [{"item": "fang", "chance": 100}]
    # fake one fighter with the same loot (old bug copied enc.loot onto the fighter)
    from quantum_rpg.combat import Fighter

    enemy = Fighter(
        id="wolf", name="Wolf", hp=1, max_hp=1, attack="1d2", defense=0,
        loot=[{"item": "fang", "chance": 100}], xp=0,
    )
    _victory(g, enc, [enemy])
    got = [i for i in g.state.player.inventory if i == "fang"]
    assert len(got) == 1
    text = g.ui.text
    assert "Добыча" in text
    assert text.count("Добыча") == 1
