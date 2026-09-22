from pathlib import Path

from quantum_rpg.engine import Game
from quantum_rpg.library import catalog, load_include
from quantum_rpg.loader import load_world
from quantum_rpg.loot import resolve_loot
from quantum_rpg.ui import ScriptedIO

ROOT = Path(__file__).resolve().parents[1]


def test_catalog_has_bricks():
    bricks = catalog(ROOT / "library")
    kinds = {b.kind for b in bricks}
    ids = {b.eid for b in bricks}
    assert len(bricks) >= 30
    assert "items" in kinds and "encounters" in kinds
    assert "short_sword" in ids
    assert "wolf" in ids


def test_include_greyford():
    w = load_world(ROOT / "games" / "greyford")
    assert not w.errors, w.errors
    assert "short_sword" in w.items
    assert "wolf" in w.encounters
    assert "bran" in w.npcs
    assert "traveler_pouch" in w.loot_tables


def test_include_does_not_overwrite():
    w = load_world(ROOT / "games" / "first_steps")
    assert not w.errors, w.errors
    # local torch kept
    assert "travel_torch" in w.items
    assert "chest_key" in w.items
    assert "short_sword" in w.items


def test_resolve_loot_table():
    w = load_world(ROOT / "games" / "greyford")
    rows = resolve_loot(w, "beast_remains")
    ids = {r["item"] for r in rows}
    assert "wolf_pelt" in ids
    mixed = resolve_loot(w, [{"table": "traveler_pouch"}, {"item": "dagger", "chance": 10}])
    assert any(r["item"] == "dagger" for r in mixed)


def test_apply_class():
    w = load_world(ROOT / "games" / "greyford")
    g = Game(w, ui=ScriptedIO(["quit"]), language="ru", seed=1, ask_name=False, player_class="warrior")
    assert g.state.player.max_hp >= 30
    assert "wood_axe" in g.state.player.inventory
    assert "class_warrior" in g.state.flags


def test_first_steps_win():
    lines = [
        "взять факел",
        "говорить наставник",
        "1",
        "восток",
        "искать",
        "взять ключ",
        "открыть сундук",
        "запад",
        "север",
        "1", "1", "1", "1", "1", "1",
        "юг",
        "запад",
    ]
    w = load_world(ROOT / "games" / "first_steps")
    ui = ScriptedIO(lines)
    g = Game(w, ui=ui, language="ru", seed=1, ask_name=False)
    ending = g.start()
    assert ending == "win"
    assert "lesson_done" in g.state.flags


def test_greyford_win():
    lines = [
        "говорить бран",
        "1",
        "запад",
        "говорить хильда",
        "2",
        "1",
        "восток",
        "восток",
        "говорить осип",
        "1",
        "запад",
        "юг",
        "1", "1", "1", "1", "1", "1", "1", "1",
        "юг",
        "юг",
        "говорить кайн",
        "1",
        "север",
        "1", "1", "1", "1",
        "север",
        "север",
    ]
    w = load_world(ROOT / "games" / "greyford")
    assert not w.errors, w.errors
    ui = ScriptedIO(lines)
    g = Game(w, ui=ui, language="ru", seed=7, ask_name=False)
    ending = g.start()
    assert "mira_saved" in g.state.flags or "mira_home" in g.state.flags
    assert ending == "win"
