# Quantum Text RPG Engine

**EN** · [Русский](README.ru.md)

A data-driven engine for **fully textual** RPGs. No graphics, no pictures, no browser. Games are YAML. Optional Python hooks exist for logic YAML cannot express.

**1.4.0** — class abilities in combat, and a day/night clock foundation. No graphics.

```text
python -m quantum_rpg
python -m quantum_rpg play shadow_keep
```

## Requirements

- Python 3.10+
- PyYAML (`pip install pyyaml`)
- Window UI uses Tkinter (comes with Python on Windows)

## Install

```bash
git clone https://github.com/Nasty1028339219182/quantum-text-rpg-engine.git
cd quantum-text-rpg-engine
pip install -r requirements.txt
python -m quantum_rpg
```

Player on Windows without Python: download **QuantumRPG.exe** from [Releases](https://github.com/Nasty1028339219182/quantum-text-rpg-engine/releases). Authors: download the **author pack** zip from the same release.

## Play

Window (default):

```bash
python -m quantum_rpg
python -m quantum_rpg gui --lang ru
```

Terminal (1.0.0 mode):

```bash
python -m quantum_rpg play shadow_keep
python -m quantum_rpg play shadow_keep --lang en
```

**Shadow Keep / Тень Крепости** — dungeon. **Greyford / Седой Брод** — village and road. **First Steps / Первые шаги** — tutorial.

```yaml
include:
  - items/weapons.yaml
  - encounters/wildlife.yaml
```

In the window: click **восток** / **take key** / **говорить: Гром**, or type `взять ключ` at the bottom.

## Make your own game (no engine code)

```bash
python -m quantum_rpg new my_game
python -m quantum_rpg validate my_game
python -m quantum_rpg play my_game
```

Then in the window: **Редактор** or **Новая игра**. Guide: [docs/EDITOR.md](docs/EDITOR.md) · [docs/AUTHORING.md](docs/AUTHORING.md)

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
| Window UI | buttons + command line (1.1.0) |
| Editor | forms + library insert (1.2–1.3) |
| Classes | `classes:` in game.yaml |
| Library | `library/` + `include:` |

## License

MIT. See [LICENSE](LICENSE).
