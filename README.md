# Quantum Text RPG Engine

**EN** · [Русский](README.ru.md)

A data-driven engine for **fully textual** RPGs. No graphics, no maps-as-pictures, no browser. You write a game as YAML files (rooms, items, NPCs, quests, combat, dialogue). Optional Python hooks exist for logic YAML cannot express.

Copy a snippet, paste your names, play.

```text
python -m quantum_rpg play shadow_keep
```

## Requirements

- Python 3.10+
- PyYAML (`pip install pyyaml`)

## Install

```bash
git clone https://github.com/Nasty1028339219182/quantum-text-rpg-engine.git
cd quantum-text-rpg-engine
pip install -r requirements.txt
```

Or: `pip install .`  → command `quantum-rpg`.

## Play the demo (fantasy dungeon)

```bash
python -m quantum_rpg play shadow_keep
python -m quantum_rpg play shadow_keep --lang en
python -m quantum_rpg play shadow_keep --name Hero --seed 7
```

**Shadow Keep / Тень Крепости** — a short dungeon: locked doors, a search, rats, a prisoner who knows a true name, a chapel, a captain's journal, an armory, a crypt, a demon. Two endings (kill / bargain).

Interface is a prompt. Type `help` / `помощь`.

## Make your own game (no engine code)

```bash
python -m quantum_rpg new my_game
# edit games/my_game/*.yaml
python -m quantum_rpg validate my_game
python -m quantum_rpg play my_game
```

You only edit YAML. IDs stay in English (`iron_key`). Player-facing strings are:

```yaml
name: {ru: железный ключ, en: iron key}
```

or a plain string used for every language.

Full copy-paste guide: [docs/AUTHORING.md](docs/AUTHORING.md) · [docs/AUTHORING.ru.md](docs/AUTHORING.ru.md)

Field reference: [docs/YAML_REFERENCE.md](docs/YAML_REFERENCE.md)

Python hooks (optional): [docs/HOOKS.md](docs/HOOKS.md)

## What the engine already does

| System | How you author it |
|---|---|
| Rooms & exits | `locations.yaml` — lock, key, hidden, trap, skill/`when` |
| Items | take, drop, equip, use, light, read, combine |
| Inventory | optional weight / slot limits |
| NPCs | talk, shop, give, attack |
| Dialogue trees | numbered choices, flags, skill checks |
| Turn-based combat | attack / item / defend / flee, loot, XP |
| Quests | start / complete / fail, journal |
| Conditions | flags, items, stats, gold, HP, location, quests |
| Effects | give/take, heal, teleport, combat, win/lose… |
| Crafting | recipes + ingredients + optional station |
| Search / containers | hidden items, locked chests |
| Save / load | `save slot1` · JSON files |
| Darkness | room `dark: true` + item `light: true` |
| Status | bless, poison, defend |
| Language | `language ru` / `language en` at runtime |

## Commands (both languages)

`look` / `осмотреться` · `go north` / `север` · `take` / `взять` · `drop` / `положить` · `use` / `использовать` · `equip` / `надеть` · `inventory` / `инвентарь` · `talk` / `говорить` · `attack` / `атаковать` · `search` / `искать` · `open` / `открыть` · `read` / `читать` · `buy` `sell` · `craft` / `создать` · `stats` / `характеристики` · `quests` / `задания` · `journal` / `журнал` · `map` / `карта` · `rest` / `отдохнуть` · `save` `load` · `help` / `помощь` · `quit` / `выход`

## Project layout

```text
quantum_rpg/          engine (you don't touch this to make a game)
games/shadow_keep/    complete demo
games/template/       empty skeleton used by `new`
docs/                 authoring docs
tests/                pytest
```

## Tests

```bash
pip install pytest pyyaml
pytest -q
```

## License

MIT. See [LICENSE](LICENSE).
