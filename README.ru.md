# Quantum Text RPG Engine

**RU** · [English](README.md)

Движок для **полностью текстовых** RPG. Без графики, без картинок, без браузера. Игра пишется YAML-файлами (комнаты, предметы, NPC, квесты, бой, диалоги). Python-хуки — по желанию, только если YAML не хватает.

Копируешь кусок из документации, подставляешь свои названия, запускаешь.

```text
python -m quantum_rpg play shadow_keep
```

## Что нужно

- Python 3.10+
- PyYAML (`pip install pyyaml`)

## Установка

```bash
git clone https://github.com/Nasty1028339219182/quantum-text-rpg-engine.git
cd quantum-text-rpg-engine
pip install -r requirements.txt
```

Либо `pip install .` — появится команда `quantum-rpg`.

## Демо: фэнтези-данжен

```bash
python -m quantum_rpg play shadow_keep
python -m quantum_rpg play shadow_keep --lang en
python -m quantum_rpg play shadow_keep --name Герой --seed 7
```

**Тень Крепости** — короткий данжен: запертые двери, поиск, крысы, узник с истинным именем, часовня, журнал капитана, оружейная, крипта, демон. Две концовки (убийство / сделка).

Интерфейс — строка ввода. Команда `помощь`.

## Своя игра без кода движка

```bash
python -m quantum_rpg new my_game
# правишь games/my_game/*.yaml
python -m quantum_rpg validate my_game
python -m quantum_rpg play my_game
```

Идентификаторы — на английском (`iron_key`). То, что видит игрок:

```yaml
name: {ru: железный ключ, en: iron key}
```

Полный гайд с копипастой: [docs/AUTHORING.ru.md](docs/AUTHORING.ru.md)

Справочник полей: [docs/YAML_REFERENCE.md](docs/YAML_REFERENCE.md)

Хуки: [docs/HOOKS.md](docs/HOOKS.md)

## Лицензия

MIT. [LICENSE](LICENSE).
