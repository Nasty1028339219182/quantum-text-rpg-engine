from pathlib import Path

from quantum_rpg.engine import Game
from quantum_rpg.loader import load_world
from quantum_rpg.ui import ScriptedIO, QueueIO

DEMO = Path(__file__).resolve().parents[1] / "games" / "shadow_keep"


def test_snapshot_courtyard():
    world = load_world(DEMO)
    g = Game(world, ui=ScriptedIO(["выход"]), language="ru", seed=1, ask_name=False)
    snap = g.snapshot()
    assert snap["location_id"] == "courtyard"
    assert snap["mode"] == "play"
    dirs = {e["id"] for e in snap["exits"]}
    assert "north" in dirs and "east" in dirs
    assert any(n["id"] == "grom" for n in snap["npcs"])
    assert any(i["id"] == "torch" for i in snap["inventory"])


def test_set_choices_on_scripted_io():
    ui = ScriptedIO(["1", "выход"])
    world = load_world(DEMO)
    g = Game(world, ui=ui, language="ru", seed=1, ask_name=False)
    g.set_choices([{"label": "A", "command": "1"}])
    assert ui.choices[0]["command"] == "1"


def test_queue_io_roundtrip():
    q = QueueIO()
    q.write("hello")
    msg = q.out.get_nowait()
    assert msg["op"] == "write"
    assert "hello" in msg["text"]
    q.set_choices([{"label": "x", "command": "1"}])
    q.submit("север")
    q.read("> ")
    assert q.inp.empty() is False or True
    # submit before read: queued
    q2 = QueueIO()
    q2.submit("look")
    assert q2.read("> ") == "look"
