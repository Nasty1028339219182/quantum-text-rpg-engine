import random

from quantum_rpg.util import loc, match_entity, roll, wrap


def test_loc_bilingual():
    v = {"ru": "меч", "en": "sword"}
    assert loc(v, "ru") == "меч"
    assert loc(v, "en") == "sword"
    assert loc("plain", "ru") == "plain"
    assert loc(None, "ru") == ""


def test_roll_flat_and_dice():
    rng = random.Random(0)
    assert roll(5, rng) == 5
    assert roll("2", rng) == 2
    n = roll("1d1+3", rng)
    assert n == 4
    n = roll("2d6", random.Random(1))
    assert 2 <= n <= 12


def test_match_entity():
    items = {
        "iron_key": {"name": {"ru": "железный ключ", "en": "iron key"}, "aliases": ["ключ", "key"]},
        "torch": {"name": {"ru": "факел", "en": "torch"}, "aliases": ["факел"]},
    }
    assert match_entity("ключ", items, "ru") == "iron_key"
    assert match_entity("torch", items, "en") == "torch"
    assert match_entity("iron_key", items, "en") == "iron_key"


def test_wrap_keeps_paragraphs():
    text = wrap("hello world", width=5)
    assert "hello" in text
