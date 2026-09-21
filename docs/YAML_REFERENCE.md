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
```

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
random_encounters: {chance: 0-100, table: [{encounter, weight}]}
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

`message journal set_flag clear_flag toggle_flag give_item take_item give_gold take_gold heal damage restore_mp spend_mp add_xp modify_stat teleport start_quest complete_quest fail_quest start_combat reveal_exit unlock lock spawn_item spawn_npc remove_npc rest game_over add_status remove_status counter_add counter_set hook once_id`

`game_over: win|lose`
