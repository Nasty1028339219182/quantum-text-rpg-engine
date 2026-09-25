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
  advance_quest: id   или {quest: id, step: home}
  start_combat
  encounter.actions: [{id, name, when, damage, say, fx, effects}]
  encounter.phases: [{id, at_hp: 50, say, effects}]   один раз за бой
               id боя
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
  time.shop_closed: [night]
  time.night_encounter_bonus: 20
  npc.shop_always: true
  chance_night: 60

СПУТНИК
  effects: [{follow: mira}, {unfollow: mira}]
  npc.combat: {hp: 8, attack: 1d4, cover: true}
  идёт в ту же комнату, в бою бьёт один раз за ход
  враг может сбить (cover), отдых поднимает
  карта: выходы между известными комнатами
  отряд до settings.party (4)
  factions + rep: {id: 1} / when: {rep_gte: {id: 2}}
  hunger.max включает голод, предмет sates
  граф диалога: клик по узлу

ЗВУК (wav, нет файла — тишина)
  audio.music_volume: 80
  audio.sfx_volume: 100
  громкость музыка 40 / громкость эффекты 80
  эффект не обрывает музыку
  команда: звук

ДЕНЬ И РЕПУТАЦИЯ
  schedule.night: shrine     # нет фазы — location, away — нигде
  спутник по расписанию не ходит
  shop_faction: village
  shop_discount: 25          # процент за пункт репутации

ОТРЯД
  order: {npc: mira, do: wait|follow|hold}
  приказ мира жди | за мной | не дерись
  отряд — кнопки тех же приказов

АВТОР
  Отсюда — играть с открытой комнаты
  Проверить — нет WAV, диалог ссылается в пустоту
  выход: hidden, trap dc / damage / skill

РЕГИОНЫ
  regions.ford.start: square
  regions.ford.rooms: [square, inn]
  roads: [{from: ford, to: hill, hours: 2, chance: 40, encounter: wolf}]
  ехать холм
  карта показывает только этот регион

СРОК, УРОВЕНЬ, СЛУХИ
  шаг within: 8 и on_expire
  levels: [{text: loc, effects: [...]}]
  give_ability: id
  rumors.id.knows / when / text
  слухи
  кнопка Собрать — zip одной игры

ПАНЕЛИ, ШКАЛЫ, СХЕМА, ЭФФЕКТ
  ui.panels: [map, meters, exits, party, inventory]
  ui.titles.shop: {ru: Прилавок}
  meters.thirst: {max: 10, move: 1, hour: 2, fight: 1, name: {ru: Жажда}}
  bands: [{at: 6, text: {ru: В горле сухо.}}]
  when: {meter: {thirst: {gte: 6}}}
  regen: 3
  шкалы

  - meter: {thirst: -4}
  map.ford: [["", shrine, ""], [inn, square, mill]]
  клетка соседа — ход; карта запад — тоже ход
  ? нехоженое, + отдых, $ лавка, ^ лестница, * пометка
  дверь: пробел открыта, > в одну сторону, × закрыта, ║ стены нет
  карта холм — другой этаж, если ты там был
  пометка текст
  пометки

  fx.blow: {style: shake, color: danger, text: {ru: Удар.}}
  - fx: blow
  стили: plain, banner, whisper, shout, shake, glitch, rule, beat, quote, center, particles
  repeat: 2
  steps: [sparks, {style: center, text: {ru: СДЕЛАНО}}]
  when: {flag: asked_hilda}
  hooks.enter.forest: quiet
  hooks: enter, combat, hit, kill, quest_done, quest_fail, level, rest, travel, death, ending
  не пиши on: — в YAML это логическое да

СЦЕНА
  scenes.thicket.beats:
    - say: {ru: Ели.}
    - who: bran
    - choose.options: [{label: {ru: Вверх}, goto: canopy}]
    - mark: canopy
    - ask: {prompt: {ru: Имя?}, var: track_name, flag: named_track}
  once: true по умолчанию
  - scene: thicket
  - scene: {id: thicket, again: true}
  сцена thicket — сыграть снова
  when: {var: {track_name: мох}}



  anim: type | slow    delay: 16    sound: hit
  particles: spark | rain | dust | pulse | ash
  ui.screens.shop.show: [gold, goods, sell]
  ui.actions: [{label: {ru: Поклониться}, command: look shrine}]










РЕДАКТОР
  умения, таблицы лута, time.*, note_night, random.chance
  npc.combat, shop_always, в реплике поле follow




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
  start_quest / advance_quest / complete_quest / fail_quest
  start_combat
  encounter.actions: [{id, name, when, damage, say, fx, effects}]
  encounter.phases: [{id, at_hp: 50, say, effects}]   один раз за бой

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
  shop_closed: [night], night_encounter_bonus, shop_always: true

FOLLOW — effect `follow: npc_id` / `unfollow: npc_id`
  npc.combat: {hp, attack}; they walk with you and strike once a round

INCLUDE — `include: [items/weapons.yaml]` from library/; local YAML wins.
""",
}
