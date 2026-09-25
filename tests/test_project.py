from pathlib import Path

from quantum_rpg.loader import load_world
from quantum_rpg.project import Project, loc_value
from quantum_rpg.util import loc

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "games" / "template"
DEMO = ROOT / "games" / "shadow_keep"


def test_template_roundtrip(tmp_path):
    p = Project.load(TEMPLATE)
    p.locations["start_room"]["name"] = {"ru": "Зал", "en": "Hall"}
    dest = tmp_path / "g"
    p.save(dest)
    w = load_world(dest)
    assert not w.errors
    assert loc(w.locations["start_room"]["name"], "ru") == "Зал"
    assert w.locations["other_room"].get("on_enter")
    assert (dest / "game.yaml").read_text(encoding="utf-8").startswith("id:")


def test_add_and_rename(tmp_path):
    p = Project.load(TEMPLATE)
    p.add("items", "rope", {"name": loc_value("верёвка", "rope"), "type": "misc"})
    p.rename("locations", "other_room", "end_room")
    dest = tmp_path / "g"
    p.save(dest)
    w = load_world(dest)
    assert "rope" in w.items
    assert "end_room" in w.locations
    assert "other_room" not in w.locations
    assert w.locations["start_room"]["exits"]["north"] == "end_room"


def test_shadow_keep_save_validates(tmp_path):
    p = Project.load(DEMO)
    dest = tmp_path / "sk"
    p.save(dest)
    w = load_world(dest)
    assert not w.errors
    orig = load_world(DEMO)
    assert set(w.locations) == set(orig.locations)
    assert set(w.items) == set(orig.items)
    assert set(w.npcs) == set(orig.npcs)
    # trap / extra keys survive a load-save without form collect
    crypt = next(iter(w.locations.values()))
    assert crypt.get("name")


def test_editor_files_roundtrip(tmp_path):
    p = Project.load(DEMO)
    assert p.abilities["smash"]["class"] == "warrior"
    assert p.abilities["smash"]["mp"] == 2
    assert p.game["time"]["start_hour"] == 22
    assert p.locations["stables"].get("note_night")
    p.add("abilities", "shout", {"name": {"ru": "Крик", "en": "Shout"}, "class": "speaker", "mp": 1, "damage": "1d4"})
    p.add("loot_tables", "pouch", {"drops": [{"item": "torch", "chance": 50}]})
    dest = tmp_path / "sk"
    p.save(dest)
    w = load_world(dest)
    assert "smash" in w.abilities and "shout" in w.abilities
    assert w.loot_tables["pouch"][0]["item"] == "torch"
    again = Project.load(dest)
    assert again.loot_tables["pouch"]["drops"][0]["chance"] == 50
    assert again.locations["stables"].get("note_night")
    assert again.locations["courtyard"].get("note_morning")


def test_greyford_follow_fields():
    p = Project.load(ROOT / "games" / "greyford")
    assert p.npcs["mira"]["combat"]["attack"] == "1d4"
    assert p.npcs["hilda"].get("shop_always") is True
    road = p.locations["road"]["random_encounters"]
    assert road["chance"] == 35
    assert road["table"][0]["encounter"] == "wolf"
    start = p.dialogues["kain"]["nodes"]["start"]["choices"][0]
    assert any(isinstance(e, dict) and e.get("follow") == "mira" for e in start["effects"])
