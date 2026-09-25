# YAML reference

All player-facing strings may be a plain string or `{ru: "...", en: "..."}`.

## Files in a game folder

| File | Required | Contents |
|---|---|---|
| `game.yaml` | yes | title, start, intro, win/lose, player |
| `locations.yaml` | yes | rooms |
| `items.yaml` | no | items |
| `npcs.yaml` | no | people |
| `dialogues.yaml` | no | dialogue trees (id = npc.dialogue) |
| `quests.yaml` | no | quests |
| `encounters.yaml` | no | combat |
| `recipes.yaml` | no | crafting |
| `events.yaml` | no | world events |
| `hooks.py` | no | optional Python |

## game.yaml

```yaml
id: string
title: loc
author: string
version: string
language: ru|en
start: {location: room_id}
intro: loc
include: [items/weapons.yaml, encounters/wildlife.yaml]   # from library/
class_prompt: true
classes:
  warrior:
    name: loc
    text: loc
    stats: {str, dex, int, con, cha, per}
    hp, gold, inventory, equipment, skills
win: {flags: [flag], flag: flag, when: condition, text: loc, pact_text: loc}
lose: {when: condition, text: loc}
player:
  name: string
  name_prompt: bool
  stats: {str, dex, int, con, cha, per}
  hp, max_hp, mp, max_mp, gold, xp, level
  inventory: [item_id]
  equipment: {weapon: item_id, armor: item_id, shield: item_id}
  skills: {perception: 1, persuasion: 0, ...}
settings:
  inventory_limit: int
  weight_limit: int
time:
  day_length: 24
  start_hour: 22         # night 21–5, morning 6–11, day 12–17, evening 18–20
  rest_hours: 8
  shop_closed: [night]   # omitted time: block → shops always open
  night_encounter_bonus: 20
```

NPC shop: `shop_always: true` or `shop_hours: [morning, day]`.
Room `random_encounters.chance_night` overrides the bonus for that room.

Follower:

```yaml
# effect
- follow: mira
- unfollow: mira
- rep: {village: 1}
```

`settings.party` defaults to 4. `factions:` plus `when: {rep_gte: {village: 2}}`.
`hunger.max` turns hunger on; item `sates` lowers it. Omit `hunger` and nothing starves.
Each enemy strikes one standing follower, then the player. `combat.cover: false` opts out.
`карта` lists visited rooms and exits. The dialogue editor draws the node graph.

## Sound

WAV only. A missing file is silence. `звук` turns it off.

```yaml
audio:
  music_volume: 80
  sfx_volume: 100
  music:
    village: audio/village.wav
  sfx:
    coin: audio/coin.wav
    hit: audio/hit.wav
  cues:
    take: coin
    hit: hit
    win: coin
```

Music keeps playing under a sound effect. `громкость музыка 40` and `громкость эффекты 80` (or `громкость 50` for both). `звук` still mutes. Room or fight: `music: village`. Fight or item: `sound: hit`.






`abilities.yaml` — combat buttons from 5. Shown only if `class:` matches the chosen class.

```yaml
smash:
  name: loc
  class: warrior
  mp: 2
  damage: 1d8+1
  hit: 0
  text: loc
```

Room text by phase: `description_night` replaces `description`. `note_night` is appended.
`when: {phase: night}` or `{hour_gte: 18}`.


## locations.yaml — per room

```
name, description, dark, rest, tags, stations
exits:
  north: room_id
  north:
    to, locked, key, locked_text, hidden, when, blocked_text
    trap: {skill, dc, damage, once, text_fail, text_success, effects}
    on_use: effects
items: [item_id]
hidden_items: [item_id]
npcs: [npc_id]
containers:
  id: {name, aliases, locked, key, lockpick, items, gold, effects}
features:
  id: {name, aliases, description, on_examine}
search: {dc, skill, reveal, reveal_exit, text, effects}
on_enter / on_first_enter / on_rest: effects
random_encounters: {chance: 0-100, once: true, table: [{encounter, weight}]}

## loot_tables.yaml

```
table_id:
  - {item: id, chance: 0-100}
```

Encounter `loot:` may be an item id, a table id, `{table: id}`, or a list of those.

```

Directions: `north south east west up down`.

## items.yaml — per item

```
name, aliases, description, type, slot, damage, hit, ac, light,
heal, weight, value, takeable, text, use, combine, on_read
use: {consume, when, text, effects}
combine: {with: [item_id], result: item_id, effects}
```

Types: `weapon armor shield accessory consumable key book quest misc`.
Slots: `weapon armor shield accessory`.

## npcs.yaml

```
name, aliases, description, location, dialogue, shop, hostile,
encounter, wants, on_give, on_death, attack_text, talk
shop: [{item, price, stock}]
```

## dialogues.yaml

```
start: node_id
start_if: [{when, node}]
nodes:
  id:
    text, effects, end, shop
    choices:
      - text, goto, end, shop, when, effects
        skill, dc, success, fail, success_effects, fail_effects
```

## encounters.yaml

```
name, hp, attack, defense, ac, xp, loot, phrases, appear, flee_dc
enemies: [encounter_id]          # group fight
on_win, on_lose: effects
loot: [{item, chance}]
```

Attack/damage strings: `1d8+2`, `2d6`, `4`.

## quests.yaml

```
name, description, start_text, done_text, auto_start, reward
```

## recipes.yaml

```
name, aliases, ingredients, station, result, text, effects
```

## events.yaml

List or mapping:

```
id: {once, trigger: enter|turn, when, effects}
```

## Conditions (`when`)

`flag not_flag has_item not_item has_any_item in_location visited gold_gte gold_lte hp_gte hp_lte hp_pct_lte stat_gte stat_lte quest defeated npc_here npc_alive counter_gte time_gte equipped once skill_check lang all any not`

## Effects

`message journal set_flag clear_flag toggle_flag give_item take_item give_gold take_gold heal damage restore_mp spend_mp add_xp modify_stat teleport start_quest advance_quest complete_quest fail_quest start_combat reveal_exit unlock lock spawn_item spawn_npc remove_npc rest game_over add_status remove_status counter_add counter_set hook once_id`

`game_over: win|lose`

## Quest steps

Optional. A quest with no `steps` still uses only `start_quest` and `complete_quest`.

```yaml
steps:
  - id: ask
    text: {ru: Спросить., en: Ask.}
  - id: home
    text: {ru: Привести домой., en: Bring her home.}
```

```yaml
- advance_quest: missing_mira
- advance_quest: {quest: missing_mira, step: home}
```

The next step after the last one completes the quest. `задания` shows the current step and copies it into the journal. `when: {quest_step: {missing_mira: home}}`.

## Day and reputation

```yaml
schedule:
  night: shrine
  evening: inn
```

A missing phase uses `location`. `away` means the NPC is nowhere. A follower is not moved. After rest the room hears who left and who arrived.

```yaml
shop_faction: village
shop_discount: 25
```

Each reputation point changes the price by that many percent. Buying gets cheaper, selling pays more. The price stays between 25% and 300% of the list, and never below 1. No `shop_faction` means the list price.

## Party orders

Still at most four. Default is follow, and they fight.

```yaml
- order: {npc: mira, do: wait}    # stays in this room
- order: {npc: mira, do: follow}
- order: {npc: mira, do: hold}    # follows, stays out of the fight
```

In play: `приказ мира жди`, `приказ мира за мной`, `приказ мира не дерись`. `отряд` shows the order and offers the same three buttons.

## Author tools

**Отсюда** in the editor plays from the open room and skips the name. **Проверить** also warns when:

- an `audio` file is missing
- a room, fight, item, or cue names a sound that is not there
- a dialogue `goto` or `start` points at a node that does not exist

An exit row has `hidden` and `trap dc / damage / skill`. Empty trap fields mean no trap. Text for the trap can stay in the exit dict.

## Regions

Optional. No `regions:` means the game is one map, as before.

```yaml
regions:
  ford:
    name: {ru: Седой Брод, en: Greyford}
    start: square
    rooms: [square, inn]
  hill:
    name: {ru: Холм дозорных, en: Watch hill}
    aliases: [холм, hill]
    start: hill
    rooms: [hill]
roads:
  - from: ford
    to: hill
    hours: 2
    chance: 40
    encounter: wolf
    both: true
```

`ехать холм` spends the hours, ticks hunger once an hour, may start the encounter, then puts you in that region's `start`. `both` defaults to true. The map shows only the current region. A room can also set `region: hill`.





