# MovieTracker CLI — Claude Edition

**Версия:** 1.0.0  
**Автор:** Claude (Anthropic)  
**API:** [Кинопоиск Unofficial](https://kinopoiskapiunofficial.tech)  
**Язык:** Python 3.11+

---

## О версии

Реализация MovieTracker CLI, написанная ИИ-ассистентом **Claude (Anthropic)**.  
Вторая версия — **MovieTracker CLI Grok Edition** — написана Grok (xAI).  
Обе версии реализованы по одному техническому заданию независимо друг от друга.

---

## Установка

### Для пользователей — готовый бинарник (macOS / Linux)

Скачайте и установите одной командой, Python не нужен:

```bash
curl -fsSL https://raw.githubusercontent.com/YOUR_ORG/movie-tracker-cli/main/install.sh | bash
```

Или вручную:

**macOS (Apple Silicon)**
```bash
curl -fSL https://github.com/YOUR_ORG/movie-tracker-cli/releases/latest/download/movie-tracker-macos-arm64 \
     -o /usr/local/bin/movie-tracker
chmod +x /usr/local/bin/movie-tracker
```

**macOS (Intel)**
```bash
curl -fSL https://github.com/YOUR_ORG/movie-tracker-cli/releases/latest/download/movie-tracker-macos-x86_64 \
     -o /usr/local/bin/movie-tracker
chmod +x /usr/local/bin/movie-tracker
```

**Linux (x86_64)**
```bash
curl -fSL https://github.com/YOUR_ORG/movie-tracker-cli/releases/latest/download/movie-tracker-linux-x86_64 \
     -o /usr/local/bin/movie-tracker
chmod +x /usr/local/bin/movie-tracker
```

**Windows**  
Скачайте `movie-tracker.exe` со [страницы релизов](https://github.com/YOUR_ORG/movie-tracker-cli/releases/latest) и добавьте в `PATH`.

После установки на всех платформах:

```bash
movie-tracker-claude auth token YOUR_KINOPOISK_KEY
movie-tracker-claude check
movie-tracker-claude search 'Интерстеллар'
```

> **Получить бесплатный ключ:** [kinopoiskapiunofficial.tech](https://kinopoiskapiunofficial.tech)  
> Регистрация → Dashboard → API Keys · Лимит: 500 запросов в сутки

---

### Для разработчиков — установка из исходников

Требования: Python 3.11+, git

**macOS**
```bash
# Установить Python если нет
brew install python@3.12

# Клонировать и установить
git clone https://github.com/YOUR_ORG/movie-tracker-cli.git
cd movie-tracker-cli
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Задать API ключ
movie-tracker-claude auth token YOUR_KINOPOISK_KEY
movie-tracker-claude check
```

**Linux**
```bash
git clone https://github.com/YOUR_ORG/movie-tracker-cli.git
cd movie-tracker-cli
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

movie-tracker-claude auth token YOUR_KINOPOISK_KEY
movie-tracker-claude check
```

**Windows**
```bat
git clone https://github.com/YOUR_ORG/movie-tracker-cli.git
cd movie-tracker-cli
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"

movie-tracker-claude auth token YOUR_KINOPOISK_KEY
movie-tracker-claude check
```

**Альтернатива через pipx** (устанавливает глобально без venv):
```bash
pipx install .
movie-tracker-claude auth token YOUR_KINOPOISK_KEY
```

---

## Сборка бинарника

```bash
source .venv/bin/activate
pip install pyinstaller
python -m PyInstaller --onefile --name movie-tracker-claude src/movie_tracker/main.py
# Результат: dist/movie-tracker
```

---

## Команды

```
movie-tracker-claude search       🔍  Поиск по названию (ru/en)
movie-tracker-claude details      📄  Детали: инфо, актёры, рецензии, похожие
movie-tracker-claude add-watchlist ➕  Добавить в список просмотра
movie-tracker-claude list-watchlist 📋  Просмотреть список
movie-tracker-claude watchlist    🗂   update / remove
movie-tracker-claude rate         ⭐  Оценить фильм
movie-tracker-claude popular      🔥  Топ популярного
movie-tracker-claude trending     📈  Популярное / Топ-250
movie-tracker-claude recommend    🎯  Рекомендации по похожим
movie-tracker-claude auth         🔑  Управление API ключом
movie-tracker-claude check        🔧  Диагностика подключения
movie-tracker-claude cache        💾  Управление кэшем
```

Все команды поддерживают `-h` / `--help`.

---

## Тестирование

### Запуск тестов

```bash
# Активировать окружение (если не активно)
source .venv/bin/activate        # macOS / Linux
.venv\Scripts\activate           # Windows

# Все тесты
pytest tests/

# С подробным выводом
pytest tests/ -v

# Конкретный модуль
pytest tests/unit/test_models.py -v
pytest tests/integration/test_cli.py -v

# С покрытием кода
pip install pytest-cov
pytest tests/ --cov=movie_tracker --cov-report=term-missing

# Только быстрые unit-тесты
pytest tests/unit/ -v

# Только интеграционные (CLI)
pytest tests/integration/ -v
```

### Линтинг и форматирование

```bash
ruff check src/          # линтер
black src/ tests/        # форматирование
mypy src/                # статическая типизация
```

### Структура тестов

```
tests/
├── conftest.py           # Mock-данные Кинопоиска, фикстуры
├── unit/
│   ├── test_models.py    # SearchResult, WatchlistEntry, и др.
│   ├── test_validators.py # validate_rating, parse_tags, и др.
│   └── test_storage.py   # TinyDB CRUD операции
└── integration/
    └── test_cli.py       # Все CLI-команды через CliRunner
```

**85 тестов** · покрытие бизнес-логики >80%

---

## Технический стек

| Компонент | Технология | Версия |
|---|---|---|
| Язык | Python | 3.11+ |
| CLI-фреймворк | Typer | 0.12+ |
| HTTP-клиент | httpx (async) | 0.27+ |
| Вывод в терминал | Rich | 13+ |
| Кэширование | diskcache (SQLite) | 5.6+ |
| Локальная БД watchlist | TinyDB | 4.8+ |
| Конфигурация | dynaconf | 3.2+ |
| Логирование | loguru | 0.7+ |
| Тестирование | pytest + pytest-httpx | 8+/0.30+ |
| Сборка бинарника | PyInstaller | — |

---

## Архитектурные решения

### Layered Architecture

```
cli/        ← команды Typer — только UI-логика
api/        ← HTTP-клиент + маппинг ответов Кинопоиска
storage/    ← watchlist (TinyDB) + кэш (diskcache)
formatters/ ← Rich-таблицы, JSON, CSV
models/     ← dataclass-модели без бизнес-логики
```

### Async HTTP в синхронном CLI

Typer синхронный, httpx — async. Каждая команда запускает `asyncio.run()` — без глобального event loop, легко тестируется через `CliRunner`.

### Автофetch пагинации

`popular` и `trending` не требуют `--page`. Достаточно `--limit N` — клиент сам загрузит нужное число страниц и вернёт первые N результатов.

### Кэширование с дифференцированным TTL

| Тип | TTL |
|---|---|
| Поиск | 60 мин |
| Детали фильма | 24 ч |
| Популярное | 3 ч |
| Популярное сейчас | 30 мин |
| Топ-250 | 3 ч |
| Рекомендации | 12 ч |

### Абсолютные URL

Клиент строит URL явно: `https://kinopoiskapiunofficial.tech/api/v2.2/films` — без `base_url`, без неочевидного поведения httpx при путях с `/`.

---

## API Кинопоиска — используемые Endpoint-ы

| Метод | Путь | Команда |
|---|---|---|
| GET | `/api/v2.2/films?keyword=...` | search |
| GET | `/api/v2.2/films/{id}` | details |
| GET | `/api/v2.2/films/top?type=...` | popular, trending |
| GET | `/api/v2.2/films/{id}/similars` | recommend |
| GET | `/api/v1/staff?filmId={id}` | details --section cast |
| GET | `/api/v1/reviews?filmId={id}` | details --section reviews |

Авторизация: заголовок `X-API-KEY`.

---

## Локальные данные

Все данные хранятся на устройстве пользователя, ничего не передаётся на сторонние серверы:

| Файл | Назначение |
|---|---|
| `~/.movie-tracker/settings.toml` | Конфигурация и API ключ |
| `~/.movie-tracker/watchlist.json` | Список фильмов |
| `~/.movie-tracker/cache/` | Кэш запросов (авто-очистка по TTL) |
| `~/.movie-tracker/movie-tracker.log` | Логи |
