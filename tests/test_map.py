from pathlib import Path

from quantum_rpg.combat import Fighter, _enemy_hit_ally
from quantum_rpg.engine import Game
from quantum_rpg.loader import load_world
from quantum_rpg.ui import ScriptedIO

ROOT = Path(__file__).resolve().parents[1]
KEEP = ROOT / "games" / "shadow_keep"
FORD = ROOT / "games" / "greyford"


def test_map_shows_visited_exits():
    w = load_world(KEEP)
    ui = ScriptedIO(["восток", "карта", "quit"])
    g = Game(w, ui=ui, language="ru", seed=1, ask_name=False)
    g.start()
    assert "Конюшня" in ui.text
    assert "восток —" in ui.text
    assert "запад —" in ui.text


def test_enemy_can_drop_follower():
    w = load_world(FORD)
    ui = ScriptedIO([])
    g = Game(w, ui=ui, language="ru", seed=1, ask_name=False)
    g.add_follower("mira")
    g.state.followers["mira"]["hp"] = 1
    enemy = Fighter(id="bandit", name="Бандит", hp=6, max_hp=6, attack="1d4", defense=30)
    _enemy_hit_ally(g, enemy, "mira", g.state.followers["mira"])
    assert g.state.followers["mira"]["hp"] == 0
    assert "падает" in ui.text
    g.handle("отдохнуть")
    assert g.state.followers["mira"]["hp"] == 8
    assert "Снова на ногах" in ui.text


def test_cover_false_skips_the_blow():
    w = load_world(FORD)
    ui = ScriptedIO(["1", "1", "1", "1", "1", "1", "quit"])
    g = Game(w, ui=ui, language="ru", seed=1, ask_name=False)
    g.add_follower({"npc": "mira", "hp": 4, "attack": "1d4", "cover": False})
    assert g.state.followers["mira"]["cover"] is False
    hp = g.state.followers["mira"]["hp"]
    before = g.state.player.hp
    from quantum_rpg import combat

    combat.run(g, "wolf")
    assert g.state.followers["mira"]["hp"] == hp
    assert g.state.player.hp <= before
