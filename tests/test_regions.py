from pathlib import Path

from quantum_rpg.engine import Game
from quantum_rpg.loader import load_world
from quantum_rpg.ui import ScriptedIO

ROOT = Path(__file__).resolve().parents[1]


def test_travel_changes_region_and_hours():
    w = load_world(ROOT / "games" / "greyford")
    assert not w.errors, w.errors
    assert not any("region" in x or x.startswith("[road]") for x in w.warnings), w.warnings
    g = Game(w, ui=ScriptedIO([]), language="ru", seed=1, ask_name=False)
    g.world.game["roads"][0]["chance"] = 0
    assert g.region_of("square") == "ford"
    g.handle("ехать холм")
    assert g.state.location == "hill"
    assert g.state.time == 2
    g.handle("карта")
    shown = g.ui.text.split("Известные места")[-1]
    assert "Холм дозорных" in shown
    assert "Площадь" not in shown
    g.handle("ехать брод")
    assert g.state.location == "square"


def test_travel_can_start_an_encounter():
    w = load_world(ROOT / "games" / "greyford")
    g = Game(w, ui=ScriptedIO([]), language="ru", seed=1, ask_name=False)
    g.world.game["roads"][0]["chance"] = 100
    seen = []
    g.start_combat = lambda eid: seen.append(eid)
    g.travel_to("hill")
    assert seen == ["wolf"]
    assert g.state.location == "hill"


def test_game_without_regions_has_no_road():
    w = load_world(ROOT / "games" / "shadow_keep")
    g = Game(w, ui=ScriptedIO([]), language="ru", seed=1, ask_name=False)
    g.handle("ехать куда-нибудь")
    assert g.state.location != "hill"
    assert "нет дальней дороги" in g.ui.text


def test_map_stays_whole_without_regions():
    w = load_world(ROOT / "games" / "first_steps")
    g = Game(w, ui=ScriptedIO([]), language="ru", seed=1, ask_name=False)
    g.state.visited.update(g.world.locations)
    order = g._visit_order()
    assert set(order) == set(g.world.locations)
