from quantum_rpg.parser import parse


def test_bare_direction_en():
    c = parse("north")
    assert c.verb == "go" and c.direction == "north"


def test_bare_direction_ru():
    c = parse("север")
    assert c.verb == "go" and c.direction == "north"
    c = parse("в")
    assert c.verb == "go" and c.direction == "east"


def test_verbs_bilingual():
    assert parse("взять ключ").verb == "take"
    assert parse("take key").argstr == "key"
    assert parse("говорить гром").verb == "talk"
    assert parse("inventory").verb == "inventory"
    assert parse("инвентарь").verb == "inventory"
    assert parse("помощь").verb == "help"
    assert parse("осмотреться").verb == "look"


def test_go_with_word():
    c = parse("идти на север")
    assert c.verb == "go"
    assert c.direction == "north"


def test_empty():
    assert parse("") is None
    assert parse("   ") is None
