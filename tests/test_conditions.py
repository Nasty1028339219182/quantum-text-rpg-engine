from pathlib import Path

from quantum_rpg.conditions import check
from quantum_rpg.effects import apply
from quantum_rpg.engine import Game
from quantum_rpg.loader import load_world
from quantum_rpg.ui import ScriptedIO

DEMO = Path(__file__).resolve().parents[1] / "games" / "shadow_keep"


def _game():
    world = load_world(DEMO)
    g = Game(world, ui=ScriptedIO([]), language="ru", seed=1, ask_name=False)
    return g


def test_flags_and_items():
    g = _game()
    assert check(g, {"not_flag": "x"})
    apply(g, {"set_flag": "x"})
    assert check(g, {"flag": "x"})
    apply(g, {"give_item": "torch"})
    assert check(g, {"has_item": "torch"})
    assert check(g, {"any": [{"flag": "nope"}, {"flag": "x"}]})
    assert not check(g, {"all": [{"flag": "x"}, {"flag": "nope"}]})


def test_win_when_any():
    g = _game()
    apply(g, {"set_flag": "demon_slain"})
    assert g._ending_matches(g.world.game["win"])
