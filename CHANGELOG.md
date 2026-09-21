# Changelog

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
