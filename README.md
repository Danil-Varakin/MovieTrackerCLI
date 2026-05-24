# MovieTracker CLI — Сравнение двух ИИ-реализаций

Два независимых CLI-приложения для поиска фильмов и сериалов, написанные разными ИИ-ассистентами по одному техническому заданию. Оба используют **Kinopoisk API Unofficial**, но различаются архитектурой, инструментарием и деталями реализации.

| | Claude Edition | Codex Edition |
|---|---|---|
| **Автор** | Claude (Anthropic) | Codex (OpenAI) |
| **Папка** | [`Claude/`](./Claude/) | [`Codex/`](./Codex/) |
| **Команда** | `movie-tracker-claude` | `movie-tracker` |
| **Сборка** | setuptools | hatchling |
| **API** | Kinopoisk API Unofficial | Kinopoisk API Unofficial |

---

## Структура репозитория

```
MovieTrackerCLI/
├── Claude/          # Claude Edition — реализация от Claude (Anthropic)
│   ├── src/
│   ├── tests/
│   ├── pyproject.toml
│   └── CLAUDE_VERSION.md
└── Codex/           # Codex Edition — реализация от Codex (OpenAI)
    ├── src/
    ├── tests/
    ├── packaging/
    ├── pyproject.toml
    └── MOVIETRACKER_CLI_CODEX_VERSION.md
```

---

## Claude Edition

Реализация с акцентом на async-запросы (anyio) и строгую типизацию.

### Установка

```bash
cd Claude
python -m venv .venv
source .venv/bin/activate      # macOS / Linux
# или: .\.venv\Scripts\Activate.ps1  (Windows PowerShell)

pip install -e .
```

### Первый запуск

```bash
movie-tracker-claude auth token YOUR_KINOPOISK_API_KEY
movie-tracker-claude check
movie-tracker-claude search "Интерстеллар"
```

### Основные команды

```bash
movie-tracker-claude search "Матрица" --type movie
movie-tracker-claude details 361
movie-tracker-claude add-watchlist 361 --priority 5 --tags "драма,классика"
movie-tracker-claude list-watchlist --stats
movie-tracker-claude rate 361 9.5 --review "Сильное кино"
movie-tracker-claude recommend --based-on 361 --limit 5
movie-tracker-claude popular --type movie --limit 10
movie-tracker-claude trending --window week
```

### Разработка и тесты

```bash
pip install -e ".[dev]"
pytest
ruff check src tests
mypy src
```

---

## Codex Edition

Реализация с упором на бинарную сборку (PyInstaller) и чёткое разделение API-функций и локальных данных.

### Установка

```bash
cd Codex
python -m venv .venv
source .venv/bin/activate      # macOS / Linux
# или: .\.venv\Scripts\Activate.ps1  (Windows PowerShell)

pip install -e .
```

Или через pipx (рекомендуется для глобального использования):

```bash
pipx install ./Codex
```

### Первый запуск

```bash
movie-tracker init
movie-tracker auth token YOUR_KINOPOISK_API_KEY
movie-tracker search "Интерстеллар"
```

### Основные команды

```bash
movie-tracker search "Бойцовский клуб" --type movie
movie-tracker details 361 --section all
movie-tracker add-watchlist 361 --priority 5 --tags "драма,классика"
movie-tracker list-watchlist --stats
movie-tracker rate 361 9.5 --review "Сильное кино"
movie-tracker recommend --based-on 361 --limit 5
movie-tracker popular --type movie --limit 10
movie-tracker trending --window week
```

### Разработка и тесты

```bash
pip install -e ".[dev]"
pytest
ruff check src tests
mypy src
```

### Сборка бинарника

```bash
pip install -e ".[dev]"
pyinstaller packaging/movie-tracker.spec
# готовый файл появится в dist/
```

---

## Получение API-ключа

Оба приложения используют **Kinopoisk API Unofficial**. Ключ можно получить на сайте [kinopoiskapiunofficial.tech](https://kinopoiskapiunofficial.tech).

---

## Установка обеих версий одновременно

Команды у версий разные (`movie-tracker-claude` и `movie-tracker`), поэтому их можно поставить в одно виртуальное окружение без конфликтов:

```bash
python -m venv .venv
source .venv/bin/activate

pip install -e ./Claude
pip install -e ./Codex

movie-tracker-claude --help
movie-tracker --help
```
