# Changelog

## 3.0.0-snapshot.6 — not a release

Private snapshot. Deeper schematic map. Public line is still 2.6.0. No pictures.

- A floor is the grid you are on. `карта холм` shows another floor after you have been there
- Unknown rooms stay boxes with `?`. `reveal: fog` hides them. `reveal: all` prints names
- The border is the door: a gap is open, `>` is one way, `×` is locked, `║` means no door
- `$` shop, `+` rest, `^` stairs, or one letter from `map_tag`. Only after you have been there
- `пометка текст` marks the room. The cell gets `*`. `карта запад` walks that way

## 3.0.0-snapshot.5 — not a release

Private snapshot. Deeper meters. Public line is still 2.6.0. No pictures.

- `move`, `wait`, `hour`, and `fight` each add their own amount. `step` is the fallback. `fight` does not use `step` unless you write it
- A `band` speaks once when the bar crosses `at`, and again after it falls back
- `when: {meter: {thirst: {gte: 6}}}` and the same for hunger
- `шкалы` prints the bars. Hunger uses them too and stays the old key
- `regen` lowers a bar on rest when `rest` is omitted

## 3.0.0-snapshot.4 — not a release

Private snapshot. Deeper panels, plus three effect kinds. Public line is still 2.6.0. No pictures.

- `ui.screens` can hide gold, goods, or sell, and party HP or orders. A hint line is optional
- `ui.actions` adds the author's own buttons
- `anim: type` or `slow` reveals a line in the window. `delay` is the pause
- `style: particles` draws sparks, rain, dust, pulse, or ash from symbols
- `sound` on an effect plays a cue

## 3.0.0-snapshot.3 — not a release

Private snapshot. Panels, meters, a room grid, text effects. Public line is still 2.6.0. No pictures.

- `ui.panels` is the order of the side menus. `ui.titles` renames shop, party, and the rest. Leave them out and the default stays
- `meters` is any bar: thirst, morale, the next idea. Hunger is unchanged
- `map` is a grid of room ids. `карта` draws the boxes. A neighboring cell is a step
- `fx` is a text effect: banner, whisper, shout, shake, glitch, rule

## 3.0.0-snapshot.2 — not a release

Private snapshot. The rest of the original 3.0 plan. Public line is still 2.6.0.

- A quest step can expire with `within` and `on_expire`
- `levels:` makes level-up a choice. Without it, a level still adds 4 HP
- `give_ability` unlocks an ability the class did not start with
- `rumors` are said once by the NPCs who know them
- **Собрать** zips this game only, with its `include` files inside

## 3.0.0-snapshot.1 — not a release

Private snapshot. Regions and roads. The public line is still 2.6.0.

- A game may list `regions` and `roads`
- `ехать холм` spends hours, ticks hunger, may start a fight, then enters that region
- The map shows only the current region
- No `regions:` means one map, as in 2.6.0

Still to come on this line: quest deadlines, level-up choice, rumors, packaging.

## 2.6.0 — 2026-09-25

- Editor **From here** plays the open room and skips the name
- Validate names a missing WAV and a dialogue that points nowhere
- An exit row has hidden, and trap dc / damage / skill

## 2.5.0 — 2026-09-25

- `приказ` tells a follower to wait, follow, or stay out of the fight
- The same three orders are buttons on `отряд` and effects: `order`
- The party is still at most four

## 2.4.0 — 2026-09-25

- An NPC `schedule` sends them to another room by time of day, or `away`
- Followers stay with you
- After rest, the room says who left and who arrived
- `shop_faction` and `shop_discount` change buy and sell prices with reputation

## 2.3.0 — 2026-09-25

- A quest may list `steps`
- `advance_quest` moves to the next step, or to a named step
- The step past the last one completes the quest
- The current step shows under Quests and is copied into the journal
- Quests with no steps are unchanged

## 2.2.0 — 2026-09-25

- Music keeps playing while a sound effect plays
- `music_volume` and `sfx_volume`, or the command `громкость`
- `звук` still mutes

## 2.1.0 — 2026-09-25

- WAV music and sound effects from `audio:` in game.yaml
- A room, a fight, or an item can name a sound. Effects can too
- Missing files stay silent. `звук` turns sound off
- Greyford square has a short loop, a coin, and a hit. Replace the files

## 2.0.1 — 2026-09-25

- Hunger no longer rises when you look, talk, or check a menu. It rises on a step, on wait, and once per combat round
- Rest no longer spends a hunger step on the same turn
- A win is not replaced if something else tries to end the game on that turn
- The editor marks a game dirty only when the form actually changed

## 2.0.0 — 2026-09-25

Stable cut of the 2.0 snapshot. No pictures.

- Factions and `rep`
- Hunger when `hunger.max` is set
- Party of up to four
- Dialogue graph in the editor

## 2.0.0-snapshot — 2026-09-25

One snapshot build. It holds the four systems that were going to be 1.8, 1.9, 2.0 and 2.1. Stable 2.0.0 is this same cut.

- Factions: `factions`, `rep`, `when: {rep_gte}`
- Hunger: only if `hunger.max` is set. `sates` on food
- Party of up to 4 (`settings.party`)
- Dialogue graph in the editor: click a node

## 1.7.0 — 2026-09-25

- One enemy each round strikes a follower who is covering you
- At 0 hp they stop fighting until you rest
- `combat.cover: false` keeps them out of the blows
- `карта` shows visited rooms and the exits between them

## 1.6.0 — 2026-09-25

- Editor lists abilities and loot tables
- Game form: start hour, rest, closed shop phases, night encounter bonus
- Room form: `note_night`, random encounter chance and table
- NPC form: combat hp/attack, shop stays open
- Dialogue choice: `follow` field
- No new play rules. 1.7 and after are in ROADMAP.md

## 1.5.0 — 2026-09-24

- Shops close at night when the game has a `time:` block (`shop_closed`)
- Inns can stay open (`shop_always: true`)
- Night and evening raise random-encounter chance
- Followers: `follow` / `unfollow`, they change rooms with you
- A follower strikes once per combat round; rest restores their hp
- Mira in Greyford walks home instead of teleporting by a flag

## 1.4.0 — 2026-09-24

- Class abilities (`abilities.yaml`): combat buttons from 5, spend MP
- Warrior / rogue / speaker each get one ability in Shadow Keep and Greyford
- Clock foundation: night, morning, day, evening
- `when: {phase: night}`, `note_night` / `description_night`
- Rest advances the clock
- Companions and a fuller day/night simulation stay for 1.5.0

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
