from quantum_rpg.effects import apply
from quantum_rpg.engine import Game
from quantum_rpg.gridmap import render, view
from quantum_rpg.loader import load_world
from quantum_rpg.ui import ScriptedIO
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _ford():
    w = load_world(ROOT / "games" / "greyford")
    return Game(w, ui=ScriptedIO([]), language="ru", seed=1, ask_name=False)


def test_grid_is_boxes_and_a_neighbor_is_a_step():
    g = _ford()
    g.state.visited.add("square")
    grid = view(g)
    text = render(grid)
    assert "┌" in text and "┬" in text and "┘" in text
    inn = grid[1][0]
    assert inn["id"] == "inn"
    assert inn["command"] == "west"
    g.handle("карта")
    assert "Холм" not in g.ui.text.split("Известные места")[-1]


def test_meter_rises_and_can_be_drunk_down():
    g = _ford()
    assert g.state.meters["thirst"] == 0
    g._hunger_tick()
    assert g.state.meters["thirst"] == 1
    apply(g, [{"meter": {"thirst": -1}}])
    assert g.state.meters["thirst"] == 0


def test_fx_banner_is_text():
    g = _ford()
    apply(g, [{"fx": "hill"}])
    assert "Ветер на холме" in g.ui.text
    assert "┌" in g.ui.text


def test_author_panel_order():
    g = _ford()
    g.world.game["ui"] = {"panels": ["inventory", "exits"], "titles": {"shop": {"ru": "Прилавок"}}}
    assert g.ui_panels() == ["inventory", "exits"]
    assert g.ui_title("shop", "Лавка") == "Прилавок"
