# Quantum Text RPG Engine

**RU** · [English](README.md)

Движок для **полностью текстовых** RPG. Без графики, без картинок, без браузера. Игра — YAML. Python-хуки по желанию.

**1.6.0** — редактор умеет умения, лут, время, встречи и спутника. Без графики.

```text
python -m quantum_rpg
python -m quantum_rpg play shadow_keep
```

## Что нужно

- Python 3.10+
- PyYAML (`pip install pyyaml`)
- Окно использует Tkinter (в Windows идёт с Python)

## Установка

```bash
git clone https://github.com/Nasty1028339219182/quantum-text-rpg-engine.git
cd quantum-text-rpg-engine
pip install -r requirements.txt
python -m quantum_rpg
```

Игрок без Python: **QuantumRPG.exe** из [Releases](https://github.com/Nasty1028339219182/quantum-text-rpg-engine/releases). Автор: zip **author pack** там же.

## Играть

Окно (по умолчанию): `python -m quantum_rpg`

Терминал: `python -m quantum_rpg play shadow_keep`

В окне жми кнопки справа или набирай `взять ключ` внизу.

## Своя игра

```bash
python -m quantum_rpg new my_game
python -m quantum_rpg validate my_game
```

В окне — **Редактор** или **Новая игра**.

Гайд: [docs/EDITOR.md](docs/EDITOR.md) · [docs/AUTHORING.ru.md](docs/AUTHORING.ru.md)

## Лицензия

MIT. [LICENSE](LICENSE).
