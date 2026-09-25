from pathlib import Path

from quantum_rpg.engine import Game, _rep_price
from quantum_rpg.loader import load_world
from quantum_rpg.ui import ScriptedIO

ROOT = Path(__file__).resolve().parents[1]
FORD = ROOT / "games" / "greyford"


def _game():
    w = load_world(FORD)
    return Game(w, ui=ScriptedIO([]), language="ru", seed=1, ask_name=False)


def test_bran_goes_to_the_shrine_at_night():
    g = _game()
    assert "bran" in g.state.location_npcs["square"]
    g.state.time = 13  # 9 + 13 = 22, night
    g.apply_schedules(announce=True)
    assert "bran" not in g.state.location_npcs["square"]
    assert "bran" in g.state.location_npcs["shrine"]
    assert "уходит" in g.ui.text
    g.state.time = 0
    g.apply_schedules()
    assert "bran" in g.state.location_npcs["square"]


def test_a_follower_ignores_schedule():
    g = _game()
    g.add_follower("bran")
    g.state.time = 13
    g.apply_schedules()
    assert "bran" in g.state.followers
    assert "bran" in g.state.location_npcs[g.state.location]


def test_shop_price_follows_reputation():
    g = _game()
    hilda = g.world.npcs["hilda"]
    assert _rep_price(g, hilda, 12) == 12
    g.state.reputation["village"] = 2
    assert _rep_price(g, hilda, 12) == 6
    assert _rep_price(g, hilda, 2, sell=True) == 3
    g.state.reputation["village"] = -2
    assert _rep_price(g, hilda, 12) == 18
