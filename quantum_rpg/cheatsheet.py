"""Effects / conditions list for the editor help dialog."""

HELP = {
    "ru": """ЭФФЕКТЫ (effects:)
  message / journal          текст
  set_flag / clear_flag      имя флага
  give_item / take_item      id
  give_gold / take_gold      число
  heal / damage              1d6+1 или число
  add_xp / modify_stat
  teleport                   id комнаты
  start_quest / complete_quest / fail_quest
  start_combat               id боя
  reveal_exit / unlock / lock
  spawn_item / spawn_npc / remove_npc
  rest / game_over: win|lose
  add_status / remove_status
  counter_add / counter_set
  hook                       имя хука

УСЛОВИЯ (when:)
  flag / not_flag
  has_item / not_item / has_any_item / equipped
  in_location / visited
  gold_gte / hp_gte / hp_lte / stat_gte
  quest / defeated / npc_here / npc_alive
  all / any / not
  skill_check: {skill, dc}

ЛУТ
  loot: item_id
  loot: [{item: x, chance: 60}]
  loot: table_id          # loot_tables.yaml
  loot: [{table: table_id}, {item: y, chance: 10}]

ВСТРЕЧИ В КОМНАТЕ
  random_encounters:
    chance: 30
    once: true
    table:
      - {encounter: wolf, weight: 2}
      - {encounter: bandit, weight: 1}

КЛАССЫ (game.yaml)
  class_prompt: true
  classes:
    warrior:
      name: {ru: Воин, en: Warrior}
      mp: 6
      max_mp: 6

УМЕНИЯ (abilities.yaml) — кнопка в бою, с 5
  smash:
    name: {ru: Сокрушить, en: Smash}
    class: warrior
    mp: 2
    damage: 1d8+1
    text: {ru: Ты бьёшь всем весом., en: You put your weight behind it.}

ВРЕМЯ (фундамент, game.yaml)
  time: {day_length: 24, start_hour: 22, rest_hours: 8}
  фазы: night 21–5, morning 6–11, day 12–17, evening 18–20
  when: {phase: night}
  комната: note_night / description_night
  отдых сдвигает часы


INCLUDE
  include:
    - items/weapons.yaml
    - encounters/wildlife.yaml
  (файлы из library/; свои поля в игре перекрывают библиотеку)
""",
    "en": """EFFECTS
  message / journal
  set_flag / clear_flag
  give_item / take_item
  give_gold / take_gold
  heal / damage
  add_xp / modify_stat
  teleport
  start_quest / complete_quest / fail_quest
  start_combat
  reveal_exit / unlock / lock
  spawn_item / spawn_npc / remove_npc
  rest / game_over: win|lose
  add_status / counter_add / hook

CONDITIONS (when:)
  flag / not_flag / has_item / not_item
  in_location / visited / gold_gte / hp_gte
  stat_gte / quest / defeated / npc_here
  all / any / not / skill_check

LOOT
  loot: id | [{item, chance}] | table_id | [{table: id}]

RANDOM ENCOUNTERS
  random_encounters: {chance, once, table: [{encounter, weight}]}

CLASSES — game.yaml `classes:` + `class_prompt: true`

ABILITIES — abilities.yaml, combat button from 5, `class:` must match
  smash: {name, class: warrior, mp: 2, damage: 1d8+1, text}

TIME — game.yaml `time: {day_length, start_hour, rest_hours}`
  phases: night 21–5, morning 6–11, day 12–17, evening 18–20
  when: {phase: night}
  room: note_night / description_night
  rest advances the clock

INCLUDE — `include: [items/weapons.yaml]` from library/; local YAML wins.
""",
}
