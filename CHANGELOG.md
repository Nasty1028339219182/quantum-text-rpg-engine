# Changelog

## 1.3.1 — 2026-09-22

- Player `name: {ru, en}` no longer stored as a Python dict string
- Class pick shows numbered buttons in the window (mode `prompt`)
- Combat loot: one message, no duplicate table from the same enemy
- `complete_quest` does not pay the reward twice
- Loot tables with `{id, drops}` no longer spawn the table id as an item

## 1.3.0 — 2026-09-22

- YAML library (`library/`) — rooms, items, NPCs, dialogues, quests, fights, loot tables
- `include:` in game.yaml (library files; local ids win)
- Editor: **Библиотека** insert + **Справка** (effects/conditions)
- Classes at start (`classes:` + `class_prompt`)
- Loot tables (`loot_tables.yaml` or `loot: table_id`)
- Random encounters: weights + `once`
- New games: **Седой Брод / Greyford**, **Первые шаги / First Steps**
- Shadow Keep: classes, battlements, deserter side-quest

## 1.2.0 — 2026-09-21

- Game editor in the same window / same `QuantumRPG.exe`
- Forms: game, rooms, items, NPCs, dialogues, quests, encounters, recipes
- Raw text for `events.yaml` and `hooks.py`
- Extra YAML on rooms/items/NPCs keeps traps, `on_enter`, containers
- New game, save, validate, playtest
- Author games: `games/` or `%APPDATA%\quantum-rpg\games`

## 1.1.0 — 2026-09-21

- Window UI (Tk): log, HP/gold, clickable exits/items/NPCs, inventory actions, command line
- `python -m quantum_rpg` / `python -m quantum_rpg gui` opens the window
- Terminal `play` is unchanged
- Windows player `QuantumRPG.exe` (GitHub Actions) + author zip pack
- Saves from the frozen exe go to `%APPDATA%/quantum-rpg/saves`

## 1.0.0 — 2026-09-21

First public release.

- YAML-authored text RPG engine (rooms, items, NPCs, dialogue, combat, quests, shops, crafting, save/load)
- Optional Python hooks
- Bilingual UI and content (`ru` / `en`)
- Bundled demo dungeon **Shadow Keep / Тень Крепости**
- Template game via `python -m quantum_rpg new`
