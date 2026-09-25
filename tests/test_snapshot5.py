from quantum_rpg.conditions import check
from quantum_rpg.effects import apply
from quantum_rpg.engine import Game
from quantum_rpg.loader import load_world
from quantum_rpg.meters import bar
from quantum_rpg.ui import ScriptedIO
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _ford():
    w = load_world(ROOT / "games" / "greyford")
    return Game(w, ui=ScriptedIO([]), language="ru", seed=1, ask_name=False)


def test_hour_costs_more_than_a_step_when_asked():
    g = _ford()
    g.world.game["meters"]["thirst"]["hour"] = 3
    g._hunger_tick("move")
    assert g.state.meters["thirst"] == 1
    g._hunger_tick("hour")
    assert g.state.meters["thirst"] == 4
    g._hunger_tick("fight")
    assert g.state.meters["thirst"] == 5


def test_band_speaks_once_until_the_bar_falls():
    g = _ford()
    g.state.meters["thirst"] = 7
    g._hunger_tick("move")
    assert "В горле сухо" in g.ui.text
    g.ui.out.clear()
    g._hunger_tick("move")
    assert "В горле сухо" not in g.ui.text
    apply(g, [{"meter": {"thirst": -20}}])
    g.ui.out.clear()
    g.state.meters["thirst"] = 7
    g._hunger_tick("move")
    assert "В горле сухо" in g.ui.text


def test_meter_condition_and_bar():
    g = _ford()
    g.state.meters["thirst"] = 8
    assert check(g, {"meter": {"thirst": {"gte": 8}}})
    assert not check(g, {"meter": {"thirst": {"lte": 3}}})
    assert "█" in bar(8, 10) and "░" in bar(8, 10)
    g.handle("шкалы")
    assert "Жажда" in g.ui.text
    assert "Голод" in g.ui.text
