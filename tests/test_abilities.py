from pathlib import Path

from quantum_rpg.abilities import available
from quantum_rpg.clock import clock
from quantum_rpg.combat import run
from quantum_rpg.conditions import check
from quantum_rpg.engine import Game
from quantum_rpg.loader import load_world
from quantum_rpg.ui import ScriptedIO

ROOT = Path(__file__).resolve().parents[1]
KEEP = ROOT / "games" / "shadow_keep"
FORD = ROOT / "games" / "greyford"


def test_shadow_keep_starts_at_night():
    w = load_world(KEEP)
    g = Game(w, ui=ScriptedIO(["quit"]), language="ru", seed=1, ask_name=False)
    assert clock(g) == (22, "night")
    assert check(g, {"phase": "night"})
    assert "smash" in w.abilities


def test_warrior_ability_costs_mp():
    w = load_world(KEEP)
    ui = ScriptedIO(["5"] + ["1"] * 12)
    g = Game(w, ui=ui, language="ru", seed=3, ask_name=False, player_class="warrior")
    assert [a[0] for a in available(g)] == ["smash"]
    assert g.state.player.mp == 6
    run(g, "giant_rat")
    assert g.state.player.mp == 4
    assert "всем весом" in ui.text


def test_no_class_hides_abilities():
    w = load_world(KEEP)
    g = Game(w, ui=ScriptedIO(["quit"]), language="ru", seed=1, ask_name=False)
    assert available(g) == []


def test_rest_moves_to_morning_note():
    w = load_world(KEEP)
    ui = ScriptedIO([])
    g = Game(w, ui=ui, language="ru", seed=1, ask_name=False)
    g.handle("отдохнуть")
    assert clock(g)[1] == "morning"
    g._look()
    assert "серое" in ui.text


def test_greyford_night_note():
    w = load_world(FORD)
    ui = ScriptedIO([])
    g = Game(w, ui=ui, language="ru", seed=1, ask_name=False)
    assert clock(g)[1] == "morning"
    g.state.time = 17  # 9 + 17 = 26 → hour 2, night
    g._look()
    assert clock(g)[1] == "night"
    assert "Фонарей" in ui.text
