from pathlib import Path

from quantum_rpg.conditions import check
from quantum_rpg.engine import Game
from quantum_rpg.graph import dialogue_layout
from quantum_rpg.loader import load_world
from quantum_rpg.ui import ScriptedIO

ROOT = Path(__file__).resolve().parents[1]
FORD = ROOT / "games" / "greyford"
KEEP = ROOT / "games" / "shadow_keep"


def test_reputation_and_party_cap():
    w = load_world(FORD)
    ui = ScriptedIO([])
    g = Game(w, ui=ui, language="ru", seed=1, ask_name=False)
    assert g.state.reputation["village"] == 0
    g.change_rep({"village": 2})
    assert check(g, {"rep_gte": {"village": 2}})
    assert "Седой Брод" in ui.text
    for i in range(4):
        g.add_follower(f"ally{i}")
    g.add_follower("ally4")
    assert "ally4" not in g.state.followers
    assert "уже 4" in ui.text


def test_hunger_damages_only_when_enabled():
    keep = load_world(KEEP)
    quiet = Game(keep, ui=ScriptedIO([]), language="ru", seed=1, ask_name=False)
    before = quiet.state.player.hp
    quiet._tick()
    assert quiet.state.player.hp == before
    assert quiet.state.hunger == 0

    w = load_world(FORD)
    ui = ScriptedIO([])
    g = Game(w, ui=ui, language="ru", seed=1, ask_name=False)
    g.state.hunger = 39
    g._tick()
    assert g.state.hunger == 40
    assert g.state.player.hp == before - 1 or g.state.player.hp < g.state.player.max_hp
    g.sate(4)
    assert g.state.hunger == 36


def test_dialogue_graph_edges():
    nodes = {
        "start": {"choices": [{"goto": "job"}, {"end": True}]},
        "job": {"choices": [{"goto": "start"}]},
    }
    boxes, edges, height = dialogue_layout(nodes)
    assert set(boxes) == {"start", "job"}
    assert ("start", "job") in edges
    assert ("job", "start") in edges
    assert height > 40
