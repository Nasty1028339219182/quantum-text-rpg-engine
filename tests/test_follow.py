from pathlib import Path

from quantum_rpg.clock import encounter_chance, shop_is_open
from quantum_rpg.engine import Game
from quantum_rpg.loader import load_world
from quantum_rpg.ui import ScriptedIO

ROOT = Path(__file__).resolve().parents[1]
FORD = ROOT / "games" / "greyford"
KEEP = ROOT / "games" / "shadow_keep"


def test_mira_follows_and_stays_home():
    w = load_world(FORD)
    ui = ScriptedIO([])
    g = Game(w, ui=ui, language="ru", seed=1, ask_name=False)
    g.add_follower("mira")
    assert "mira" in g.state.followers
    assert "mira" in g.state.location_npcs["square"]
    g.move_to("forest")
    assert "mira" in g.state.location_npcs["forest"]
    assert "mira" not in (g.state.location_npcs.get("square") or [])
    assert "С тобой" in ui.text
    g.state.flags.add("mira_saved")
    g.move_to("square")
    assert "mira_home" in g.state.flags
    assert "mira" not in g.state.followers
    assert "mira" in g.state.location_npcs["square"]


def test_shop_closed_at_night_inn_open():
    keep = load_world(KEEP)
    g = Game(keep, ui=ScriptedIO([]), language="ru", seed=1, ask_name=False)
    grom = keep.npcs["grom"]
    assert shop_is_open(g, grom) is False
    g.handle("магазин гром")
    assert "закрыта" in g.ui.text
    g.state.time = 12  # 22+12 = 34 → hour 10, morning
    assert shop_is_open(g, grom) is True

    ford = load_world(FORD)
    night = Game(ford, ui=ScriptedIO([]), language="ru", seed=1, ask_name=False)
    night.state.time = 17  # hour 2, night
    assert shop_is_open(night, ford.npcs["hilda"]) is True
    assert shop_is_open(night, {}) is False


def test_night_encounter_bonus():
    w = load_world(FORD)
    g = Game(w, ui=ScriptedIO([]), language="ru", seed=1, ask_name=False)
    table = w.locations["road"]["random_encounters"]
    assert encounter_chance(g, table) == 35
    g.state.time = 17
    assert encounter_chance(g, table) == 60
