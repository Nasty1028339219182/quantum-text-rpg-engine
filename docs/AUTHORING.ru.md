# Как сделать игру (копируй и подставляй)

Игра = папка с YAML. Движок трогать не нужно.

```bash
python -m quantum_rpg new dungeon1
```

Появится `games/dungeon1/` (или `./games/dungeon1` в текущей папке). Ниже — готовые куски. Меняй только то, что в кавычках и id.

Тексты для игрока пиши так:

```yaml
name: {ru: Ржавый меч, en: Rusty sword}
```

Либо одной строкой, если язык один: `name: Ржавый меч`.

---

## 1. Паспорт игры — `game.yaml`

```yaml
id: dungeon1
title: {ru: Мой данжен, en: My Dungeon}
author: Твоё имя
version: "0.1.0"
language: ru
start:
  location: gate
intro:
  ru: Дождь. Перед тобой ворота.
  en: Rain. Gates ahead of you.
win:
  flags: [boss_dead]
  text: {ru: Ты победил., en: You won.}
player:
  name_prompt: true
  stats: {str: 12, dex: 10, int: 10, con: 12, cha: 8, per: 10}
  hp: 24
  max_hp: 24
  gold: 10
  inventory: [torch, rusty_sword]
  equipment:
    weapon: rusty_sword
```

`start.location` — id комнаты из `locations.yaml`.
`win.flags` — все перечисленные флаги должны стоять (через эффекты `set_flag`).

---

## 2. Комната — `locations.yaml`

```yaml
gate:
  name: {ru: Ворота, en: Gate}
  description:
    ru: Каменная арка. На севере — двор.
    en: A stone arch. North is the yard.
  exits:
    north: yard
  items: [torch]
  npcs: [guard]
  rest: true
```

### Запертый выход + ключ

```yaml
  exits:
    north:
      to: hall
      locked: true
      key: iron_key
      locked_text: {ru: Заперто., en: Locked.}
```

Игрок пишет `север` / `go north`. Если ключ в инвентаре — дверь открывается.

### Скрытый выход (найти поиском или осмотром)

```yaml
    down:
      to: crypt
      hidden: true
  search:
    dc: 10
    skill: perception
    reveal_exit: down
    text: {ru: Под ковром люк., en: A hatch under the rug.}
```

### Ловушка на лестнице

```yaml
    up:
      to: tower
      trap:
        skill: dex
        dc: 12
        damage: 1d6
        once: true
        text_fail: {ru: Ступень ломается., en: The step snaps.}
        text_success: {ru: Ты замечаешь щель., en: You spot the crack.}
```

### Тёмная комната

```yaml
cellar:
  dark: true
  # без предмета с light: true игрок почти ничего не видит
```

### Бой при входе (один раз)

```yaml
  on_enter:
    - when:
        not_flag: rats_cleared
      start_combat: cellar_rats
```

В `encounters.yaml` у этой встречи:

```yaml
cellar_rats:
  on_win:
    - set_flag: rats_cleared
```

### Сундук

```yaml
  containers:
    chest:
      name: {ru: сундук, en: chest}
      aliases: [сундук, chest]
      locked: true
      key: iron_key
      items: [health_potion]
      gold: 12
```

Игрок: `открыть сундук`.

---

## 3. Предмет — `items.yaml`

```yaml
rusty_sword:
  name: {ru: ржавый меч, en: rusty sword}
  aliases: [меч, sword]
  description: {ru: Ещё режет., en: It still cuts.}
  type: weapon          # weapon armor shield accessory consumable key book quest misc
  slot: weapon
  damage: 1d6+1
  hit: 1
  weight: 3
  value: 5

torch:
  name: {ru: факел, en: torch}
  type: misc
  light: true

health_potion:
  name: {ru: зелье, en: potion}
  type: consumable
  aliases: [зелье, potion]
  use:
    consume: true
    effects:
      - heal: 12
    text: {ru: Раны затягиваются., en: Wounds knit.}

letter:
  name: {ru: письмо, en: letter}
  type: book
  text: {ru: «Не спускайся без света.», en: "Do not go down without light."}
  on_read:
    - set_flag: read_letter
    - journal: {ru: В письме просят взять факел., en: The letter says take a torch.}
```

Соединить два предмета:

```yaml
rope:
  combine:
    with: [hook]
    result: grappling_hook
```

Игрок: `соединить верёвка крюк`.

---

## 4. NPC и диалог

`npcs.yaml`:

```yaml
guard:
  name: {ru: Страж, en: Guard}
  aliases: [страж, guard]
  description: {ru: У ворот., en: At the gate.}
  location: gate
  dialogue: guard
  shop:
    - {item: health_potion, price: 10, stock: 2}
```

`dialogues.yaml` — тот же id:

```yaml
guard:
  start: greeting
  nodes:
    greeting:
      text: {ru: Стой. Кто идёт?, en: Halt. Who goes?}
      choices:
        - text: {ru: Ищу работу., en: Looking for work.}
          goto: job
          effects:
            - start_quest: rats
        - text: {ru: Купить., en: Buy.}
          shop: true
        - text: {ru: Уйти., en: Leave.}
          end: true
    job:
      text: {ru: Вычисти погреб — и ключ твой., en: Clear the cellar and the key is yours.}
      choices:
        - text: {ru: Хорошо., en: Fine.}
          end: true
```

Проверка навыка в выборе:

```yaml
        - text: {ru: Пропусти меня. (харизма), en: Let me through. (cha)}
          skill: persuasion
          dc: 12
          success: pass
          fail: refuse
```

---

## 5. Бой — `encounters.yaml`

```yaml
giant_rat:
  name: {ru: Крыса, en: Rat}
  hp: 8
  attack: 1d4
  defense: 0
  xp: 10
  loot:
    - {item: rat_tooth, chance: 50}
  phrases:
    appear: {ru: Крыса выскакивает из тьмы., en: A rat leaps from the dark.}
    hit: {ru: Крыса кусает., en: The rat bites.}

cellar_rats:
  enemies: [giant_rat, giant_rat]
  on_win:
    - set_flag: rats_cleared
    - complete_quest: rats
    - give_item: iron_key
```

В бою игрок жмёт `1` атака, `2` предмет, `3` защита, `4` бежать.

Чтобы напасть на NPC, укажи `encounter: giant_rat` и `hostile: true`.

---

## 6. Квест — `quests.yaml`

```yaml
rats:
  name: {ru: Крысы в погребе, en: Cellar rats}
  description: {ru: Вычистить погреб., en: Clear the cellar.}
  start_text: {ru: Страж обещает ключ., en: The guard promises a key.}
  done_text: {ru: Погреб тих., en: The cellar is quiet.}
  reward:
    - give_gold: 15
    - add_xp: 20
```

Запуск: эффект `start_quest: rats`. Финиш: `complete_quest: rats`.

---

## 7. Условия `when:` и эффекты

Любой триггер (`on_enter`, выбор диалога, использование предмета) может содержать:

```yaml
when:
  flag: door_open          # есть флаг
  not_flag: boss_dead
  has_item: iron_key
  not_item: torch
  in_location: hall
  gold_gte: 10
  stat_gte: {str: 14}
  quest: {id: rats, status: active}
  defeated: giant_rat
  any:
    - has_item: pitchfork
    - stat_gte: {str: 14}
  all:
    - flag: a
    - flag: b
```

Эффекты (вставляй списком):

```yaml
effects:
  - set_flag: door_open
  - clear_flag: alarm
  - give_item: iron_key
  - take_item: torch
  - give_gold: 10
  - take_gold: 5
  - heal: 8
  - damage: 1d4
  - add_xp: 15
  - teleport: cellar
  - start_quest: rats
  - complete_quest: rats
  - start_combat: giant_rat
  - message: {ru: Щёлк., en: Click.}
  - journal: {ru: Дверь открыта., en: The door is open.}
  - reveal_exit: down
  - unlock: north
  - spawn_item: {item: torch, location: hall}
  - add_status: {id: bless, name: {ru: благословение, en: bless}, turns: 10, attack: 2}
  - game_over: win          # win | lose
  - hook: my_function       # функция из hooks.py
```

---

## 8. Крафт — `recipes.yaml`

```yaml
health_potion:
  name: {ru: зелье, en: potion}
  aliases: [зелье, potion]
  ingredients: [herbs, mushroom, flask]
  station: kitchen          # id комнаты; без поля — крафт везде
  result: health_potion
  text: {ru: Отвар готов., en: The draught is ready.}
```

Игрок: `создать зелье`. Ингредиенты списываются.

---

## 9. События — `events.yaml`

```yaml
night_fall:
  once: true
  trigger: turn
  when:
    time_gte: 40
    not_flag: night
  effects:
    - set_flag: night
    - message: {ru: Небо чернеет., en: The sky goes black.}
```

`trigger`: `enter` | `turn`. Для входа в комнату:

```yaml
  trigger: enter
  when:
    enter: crypt
    not_flag: seen_crypt
```

---

## 10. Мини-игра с нуля за 5 файлов

Скопируй в новую папку, поменяй тексты — уже играется.

**game.yaml** — паспорт из §1, `start.location: gate`, `win.flags: [boss_dead]`.

**locations.yaml** — `gate` → `yard` → `lair`.

**items.yaml** — меч, ключ, зелье.

**npcs.yaml** + **dialogues.yaml** — страж выдаёт квест.

**encounters.yaml** — крыса во дворе, босс в логове с `on_win: [{set_flag: boss_dead}]`.

Демо `games/shadow_keep/` — собранный данжен, все системы сразу. Открывай файлы рядом с этим гайдом.

---

## Частые ошибки

- Выход `to: hal` — опечатка, комнаты `hall` нет. `python -m quantum_rpg validate my_game`.
- Предмет в комнате, но его нет в `items.yaml`.
- `start.location` не совпадает с id комнаты.
- В диалоге `goto: job`, а узла `job` нет.
- Игрок пишет «взять ключ», а в `aliases` нет слова «ключ».
