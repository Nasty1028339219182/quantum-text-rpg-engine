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
    ui = ScriptedIO(["осмотреться", "ждать"])
    g = Game(w, ui=ui, language="ru", seed=1, ask_name=False)
    g.state.hunger = 10
    g.handle("осмотреться")
    g._tick()
    assert g.state.hunger == 10
    g.handle("ждать")
    assert g.state.hunger == 11
    g.state.hunger = 39
    g._hunger_tick()
    assert g.state.hunger == 40
    assert g.state.player.hp < g.state.player.max_hp
    g.sate(4)
    assert g.state.hunger == 36
    g.finish("win")
    g.finish("lose")
    assert g.state.ended == "win"


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


def test_sound_ids_and_mute():
    w = load_world(FORD)
    ui = ScriptedIO([])
    g = Game(w, ui=ui, language="ru", seed=1, ask_name=False)
    played = []
    g.audio.play = lambda name: played.append(("sfx", name))
    g.audio.play_music = lambda name, force=False: played.append(("music", name))
    assert g.audio._resolve("village", "music") is not None
    g.audio.event("take")
    g.handle("звук")
    assert g.audio.muted
    g.audio.event("hit")
    assert played == [("sfx", "coin")]
    assert "выключен" in ui.text


def test_mixer_keeps_music_and_volume():
    from quantum_rpg.audio import Audio

    audio = Audio(FORD, {"music_volume": 100, "sfx_volume": 100})
    audio._music_samples = [1000] * 50
    audio._music_pos = 0
    audio._sfx.append({"samples": [1000] * 10, "pos": 0})
    chunk = audio.render(20)
    assert audio._music_samples is not None
    assert audio._music_pos == 20
    assert chunk[0] == 2000
    assert chunk[15] == 1000
    assert audio._sfx == []

    w = load_world(FORD)
    g = Game(w, ui=ScriptedIO([]), language="ru", seed=1, ask_name=False)
    g.handle("громкость эффекты 40")
    assert g.audio.sfx_volume == 40
    assert g.state.sfx_volume == 40
    assert g.audio.music_volume == 80




def test_editor_freeze_ignores_unchanged_open():
    from quantum_rpg.project import Project

    p = Project.load(KEEP)
    token = p.freeze()
    assert p.freeze() == token
    p.locations["courtyard"]["name"] = {"ru": "Другой", "en": "Other"}
    assert p.freeze() != token
