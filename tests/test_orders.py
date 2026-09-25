from pathlib import Path

from quantum_rpg.combat import _allies_act, _cover_allies
from quantum_rpg.effects import apply
from quantum_rpg.engine import Game
from quantum_rpg.loader import load_world
from quantum_rpg.ui import ScriptedIO

ROOT = Path(__file__).resolve().parents[1]
FORD = ROOT / "games" / "greyford"


def _game():
    w = load_world(FORD)
    g = Game(w, ui=ScriptedIO([]), language="ru", seed=1, ask_name=False)
    g.add_follower("mira")
    return g


def test_wait_stays_and_follow_catches_up():
    g = _game()
    g.handle("приказ мира жди")
    assert g.state.followers["mira"]["order"] == "wait"
    assert g.state.followers["mira"]["wait_at"] == "square"
    g.move_to("forest")
    assert "mira" in g.state.location_npcs["square"]
    assert "mira" not in (g.state.location_npcs.get("forest") or [])
    g.handle("приказ мира за мной")
    assert g.state.followers["mira"]["order"] == "follow"
    assert "mira" in g.state.location_npcs["forest"]
    assert "догоняет" in g.ui.text


def test_hold_stays_out_of_the_fight():
    g = _game()
    apply(g, [{"order": {"npc": "mira", "do": "hold"}}])
    assert g.state.followers["mira"]["order"] == "hold"
    assert _cover_allies(g) == []

    class Enemy:
        name = "Кайн"
        hp = 5
        max_hp = 5
        defense = 0
        ac_bonus = 0

    enemy = Enemy()
    _allies_act(g, [enemy])
    assert enemy.hp == 5


def test_party_still_caps_at_four():
    g = _game()
    for nid in ("bran", "hilda", "osip", "kain"):
        g.add_follower(nid)
    assert set(g.state.followers) == {"mira", "bran", "hilda", "osip"}
