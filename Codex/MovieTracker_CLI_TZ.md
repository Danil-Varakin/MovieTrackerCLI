# MovieTracker CLI — Техническое задание

**Версия:** 1.0.0 | **Дата:** Апрель 2025 | **Статус:** Draft

---

## Содержание

1. [Общее описание проекта](#1-общее-описание-проекта)
2. [Функциональные требования](#2-функциональные-требования)
3. [Технические требования](#3-технические-требования)
4. [Конфигурация](#4-конфигурация)
5. [Логирование](#5-логирование)
6. [Тестирование](#6-тестирование)
7. [Документация TMDB API](#7-документация-tmdb-api)
8. [Нефункциональные требования](#8-нефункциональные-требования)
9. [Установка и развёртывание](#9-установка-и-развёртывание)
10. [Глоссарий](#10-глоссарий)

---

## 1. Общее описание проекта

### 1.1 Назначение

**MovieTracker CLI** — консольная утилита для поиска, отслеживания и анализа кинофильмов и телесериалов. Утилита интегрирована с внешним REST API **The Movie Database (TMDB)** и предоставляет пользователям богатый функционал: от поиска контента до управления персональными списками просмотра, оценки фильмов и получения рекомендаций на основе предпочтений.

### 1.2 Цели и задачи

- Обеспечить удобный консольный интерфейс для работы с базой данных фильмов и сериалов TMDB
- Предоставить функционал управления персональными списками просмотра с локальным хранилищем данных
- Реализовать систему аутентификации через TMDB для персонализированных действий (оценки, списки)
- Минимизировать количество запросов к API за счёт локального кэширования
- Обеспечить расширяемую архитектуру для добавления новых подкоманд и функций

### 1.3 Целевая аудитория

- Разработчики и технические специалисты, предпочитающие работу в терминале
- Кинофанаты, ведущие учёт просмотренного контента
- Пользователи, интегрирующие утилиту в собственные скрипты и автоматизации

### 1.4 Контекст и ограничения

> ⚠️ **Ключевые ограничения**
>
> - Для персонализированных действий (rate, watchlist на TMDB) требуется наличие аккаунта TMDB и авторизация.
> - TMDB API имеет rate limit: **40 запросов / 10 сек** (бесплатный тариф). Кэширование обязательно.
> - Локальный watchlist хранится в JSON-файле на устройстве пользователя, без облачной синхронизации.
> - Утилита работает только с публично доступными данными TMDB (без доступа к частным спискам без авторизации).

---

## 2. Функциональные требования

### 2.1 Глобальный синтаксис и структура команд

```
movie-tracker <command> [subcommand] [arguments] [options]

Глобальные флаги:
  --config <path>     Путь к кастомному конфиг-файлу
  --output <format>   Формат вывода: table | json | csv (default: table)
  --no-color          Отключить цветной вывод
  --verbose, -v       Подробный вывод (включая debug-инфо)
  --quiet, -q         Минимальный вывод
  --version           Версия утилиты
  --help, -h          Справка по команде
```

### 2.2 Описание команд

---

#### 2.2.1 `search` — Поиск фильмов и сериалов

```
movie-tracker search <query> [options]

Аргументы:
  <query>             Строка поиска (название, ключевые слова)

Опции:
  --type <type>       Тип контента: movie | tv | all (default: all)
  --genre <id|name>   Фильтр по жанру (ID или название, напр: 28 или 'Action')
  --year <yyyy>       Год выхода
  --lang <code>       Язык результатов: en-US, ru-RU и т.д. (default: из конфига)
  --page <n>          Номер страницы результатов (default: 1)
  --per-page <n>      Результатов на странице: 5 | 10 | 20 (default: 10)
  --sort <field>      Сортировка: relevance | popularity | rating | year
```

**Примеры использования:**

```bash
movie-tracker search 'The Dark Knight'
movie-tracker search 'Breaking Bad' --type tv --year 2008
movie-tracker search '' --genre Action --sort popularity --page 2
movie-tracker search 'Inception' --output json
```

**Ожидаемое поведение:**

- Отправляет GET-запрос к `/search/multi` (или `/search/movie`, `/search/tv` при `--type`)
- Результаты отображаются постранично в виде таблицы с колонками: ID, Название, Тип, Год, Рейтинг, Жанры
- При пустом `query` с указанным жанром переключается на `/discover` endpoint
- При отсутствии результатов: `Ничего не найдено. Попробуйте изменить запрос.`
- Кэш результатов сохраняется на 1 час

---

#### 2.2.2 `details` — Детальная информация о фильме/сериале

```
movie-tracker details <id> [options]

Аргументы:
  <id>                TMDB ID фильма или сериала

Опции:
  --type <type>       Тип: movie | tv (default: auto-detect)
  --section <s>       Секции: info | cast | reviews | similar | all (default: all)
  --lang <code>       Язык описания
  --reviews-page <n>  Страница отзывов
```

**Примеры использования:**

```bash
movie-tracker details 550 --type movie
movie-tracker details 1396 --type tv --section cast
movie-tracker details 550 --section reviews --reviews-page 2
```

**Ожидаемое поведение:**

- Отображает полную информацию: описание, жанры, рейтинг TMDB/IMDB, страна, бюджет/сборы (для фильмов)
- Секция `cast`: список актёров (имя, персонаж, порядок), режиссёр, сценаристы
- Секция `reviews`: список рецензий (автор, оценка, текст, дата)
- Секция `similar`: список похожих фильмов/сериалов
- Для сериалов дополнительно: количество сезонов/эпизодов, статус (Running/Ended), сеть

---

#### 2.2.3 `add-watchlist` — Добавление в список просмотра

```
movie-tracker add-watchlist <id> [options]

Аргументы:
  <id>                TMDB ID фильма или сериала

Опции:
  --type <type>       Тип: movie | tv (default: auto-detect)
  --status <status>   Начальный статус: unwatched | watched | watching (default: unwatched)
  --priority <n>      Приоритет 1-5 (default: 3)
  --note <text>       Личная заметка
  --tags <t1,t2>      Теги через запятую
```

**Примеры использования:**

```bash
movie-tracker add-watchlist 550 --type movie
movie-tracker add-watchlist 1396 --type tv --status watching --priority 5
movie-tracker add-watchlist 550 --note 'Посмотреть с друзьями' --tags 'drama,cult'
```

**Ожидаемое поведение:**

- Добавляет запись в локальный JSON-файл `~/.movie-tracker/watchlist.json`
- При попытке добавить уже существующий ID — предупреждает и предлагает обновить запись
- Если авторизован через TMDB — синхронно добавляет в watchlist на TMDB
- Выводит подтверждение с названием и ID добавленного элемента

---

#### 2.2.4 `list-watchlist` — Просмотр списка

```
movie-tracker list-watchlist [options]

Опции:
  --status <s>        Фильтр: watched | unwatched | watching | all (default: all)
  --type <type>       Фильтр по типу: movie | tv | all (default: all)
  --sort <field>      Сортировка: added | priority | rating | title | year
  --order <dir>       Направление: asc | desc (default: desc)
  --tags <t1,t2>      Фильтр по тегам
  --search <q>        Поиск по названию в списке
  --page <n>          Пагинация
  --stats             Показать статистику (кол-во, % просмотрено и т.д.)
```

**Примеры использования:**

```bash
movie-tracker list-watchlist
movie-tracker list-watchlist --status unwatched --sort priority
movie-tracker list-watchlist --type tv --stats
movie-tracker list-watchlist --tags drama --output json
```

**Ожидаемое поведение:**

- Читает локальный `watchlist.json` и отображает в табличном виде: ID, Название, Тип, Статус, Оценка, Приоритет, Дата добавления
- При `--stats` добавляет блок статистики: итого записей, % просмотрено, средняя оценка
- При пустом списке: `Ваш список пуст. Добавьте фильм: movie-tracker add-watchlist <id>`

---

#### 2.2.5 `rate` — Оценка контента

```
movie-tracker rate <id> <rating> [options]

Аргументы:
  <id>                TMDB ID
  <rating>            Оценка от 0.5 до 10.0 (шаг 0.5)

Опции:
  --type <type>       Тип: movie | tv
  --local-only        Сохранить только локально (не отправлять в TMDB)
  --review <text>     Добавить личный отзыв
```

**Примеры использования:**

```bash
movie-tracker rate 550 9.5
movie-tracker rate 1396 8.0 --type tv
movie-tracker rate 550 7.5 --local-only --review 'Хороший фильм, но концовка слабая'
```

**Ожидаемое поведение:**

- Если авторизован: отправляет рейтинг через TMDB API (`POST /movie/{id}/rating`) и сохраняет локально
- Если не авторизован или `--local-only`: сохраняет только в `watchlist.json`
- Автоматически обновляет статус в watchlist на `watched` при выставлении оценки
- Валидация: значение должно быть кратно 0.5 и в диапазоне 0.5–10.0

---

#### 2.2.6 `recommend` — Персональные рекомендации

```
movie-tracker recommend [options]

Опции:
  --based-on <id>     Рекомендации на основе конкретного фильма/сериала
  --type <type>       Тип контента: movie | tv | all (default: all)
  --genres <g1,g2>    Предпочтительные жанры
  --exclude-watched   Исключить просмотренное из watchlist
  --limit <n>         Количество рекомендаций (default: 10, max: 40)
  --page <n>          Пагинация
```

**Примеры использования:**

```bash
movie-tracker recommend --based-on 550 --type movie
movie-tracker recommend --genres Action,Thriller --exclude-watched
movie-tracker recommend --based-on 1396 --limit 5
```

**Ожидаемое поведение:**

- При `--based-on`: использует `/movie/{id}/recommendations` или `/tv/{id}/recommendations`
- Без `--based-on`: анализирует watchlist, вычисляет топ-жанры и строит рекомендации через `/discover`
- При `--exclude-watched` фильтрует ID из watchlist со статусом `watched`
- Отображает результаты с кратким описанием каждого элемента

---

#### 2.2.7 `popular` — Популярный контент

```
movie-tracker popular [options]

Опции:
  --type <type>       Тип: movie | tv (default: movie)
  --region <code>     Регион (ISO 3166-1): US, RU, DE и т.д.
  --page <n>          Страница (default: 1)
  --limit <n>         Количество (default: 20, max: 100)
```

**Примеры использования:**

```bash
movie-tracker popular --type movie
movie-tracker popular --type tv --region RU --page 2
```

**Ожидаемое поведение:**

- Использует `/movie/popular` или `/tv/popular` с параметром `region`
- Таблица с колонками: Место, ID, Название, Год, Рейтинг, Голоса, Жанры
- Кэш обновляется раз в 3 часа

---

#### 2.2.8 `trending` — Трендовый контент

```
movie-tracker trending [options]

Опции:
  --type <type>       Тип: movie | tv | all (default: all)
  --window <period>   Период: day | week (default: day)
  --page <n>          Страница
  --limit <n>         Количество (default: 20)
```

**Примеры использования:**

```bash
movie-tracker trending --window week --type movie
movie-tracker trending --type tv --window day --output json
```

**Ожидаемое поведение:**

- Использует endpoint `/trending/{media_type}/{time_window}`
- Отображает тренд-метрику: место в тренде, динамику (↑↓)
- Кэш для `day`: 30 минут, для `week`: 3 часа

---

#### 2.2.9 `auth` — Аутентификация

```bash
movie-tracker auth login           # Запуск OAuth flow через TMDB
movie-tracker auth logout          # Выход и удаление токена
movie-tracker auth status          # Проверка статуса авторизации
movie-tracker auth token <key>     # Ручная установка API ключа
```

**Примеры использования:**

```bash
movie-tracker auth login
movie-tracker auth status
movie-tracker auth token my_api_key_here
```

**Ожидаемое поведение:**

- `login`: Генерирует request token через `/authentication/token/new`, открывает браузер для подтверждения, получает `session_id`
- Токен и `session_id` сохраняются в `~/.movie-tracker/auth.json` (права `600`)
- `status`: Показывает имя пользователя, ID аккаунта, дату входа, статус сессии
- `logout`: Инвалидирует сессию на TMDB и удаляет локальный `auth.json`

---

#### 2.2.10 `watchlist update` и `watchlist remove`

```
movie-tracker watchlist update <id> [options]
  --status <s>        Обновить статус: watched | unwatched | watching
  --rating <n>        Обновить оценку
  --note <text>       Обновить заметку
  --tags <t1,t2>      Обновить теги

movie-tracker watchlist remove <id>
  --force             Без подтверждения
```

**Примеры использования:**

```bash
movie-tracker watchlist update 550 --status watched --rating 9.0
movie-tracker watchlist remove 550 --force
```

---

## 3. Технические требования

### 3.1 Технологический стек

| Компонент | Технология / Библиотека | Версия | Назначение |
|---|---|---|---|
| Язык разработки | Python | 3.11+ | Основной язык |
| CLI framework | Typer | 0.12+ | Парсинг команд, help-генерация |
| HTTP-клиент | httpx | 0.27+ | Async HTTP запросы к TMDB |
| Форматирование вывода | Rich | 13.x | Таблицы, прогресс-бары, цвет |
| Кэширование | diskcache | 5.6+ | Persistent кэш на диске |
| Локальная БД | TinyDB | 4.8+ | Хранение watchlist |
| Конфигурация | dynaconf | 3.2+ | Настройки из файла и env |
| Логирование | loguru | 0.7+ | Структурированные логи |
| Тестирование | pytest + pytest-httpx | 8.x | Unit и интеграционные тесты |
| Покрытие кода | coverage.py | 7.x | Отчёт покрытия |
| Линтер | ruff | 0.4+ | Быстрый Python linter |
| Форматтер | black | 24.x | Форматирование кода |
| Типизация | mypy | 1.10+ | Статическая проверка типов |
| Сборка пакета | hatch | 1.9+ | Build system |

### 3.2 Структура проекта

```
movie-tracker/
├── pyproject.toml              # Метаданные, зависимости, hatch config
├── README.md
├── CHANGELOG.md
├── .env.example                # Шаблон переменных окружения
├── settings.toml               # Конфигурация dynaconf
├── src/
│   └── movie_tracker/
│       ├── __init__.py
│       ├── main.py             # Точка входа Typer app
│       ├── cli/                # Команды CLI
│       │   ├── __init__.py
│       │   ├── search.py
│       │   ├── details.py
│       │   ├── watchlist.py
│       │   ├── rate.py
│       │   ├── recommend.py
│       │   ├── popular.py
│       │   ├── trending.py
│       │   └── auth.py
│       ├── api/                # TMDB API клиент
│       │   ├── __init__.py
│       │   ├── client.py       # Базовый async httpx клиент
│       │   ├── auth.py         # Аутентификация TMDB
│       │   ├── search.py
│       │   ├── details.py
│       │   ├── recommendations.py
│       │   ├── trending.py
│       │   └── watchlist.py
│       ├── storage/            # Локальное хранилище
│       │   ├── __init__.py
│       │   ├── watchlist.py    # TinyDB watchlist операции
│       │   └── auth.py         # Хранение токенов
│       ├── cache/              # Кэширование
│       │   ├── __init__.py
│       │   └── manager.py      # diskcache wrapper
│       ├── formatters/         # Форматирование вывода
│       │   ├── __init__.py
│       │   ├── table.py        # Rich tables
│       │   ├── json.py
│       │   └── csv.py
│       ├── models/             # Pydantic/dataclass модели
│       │   ├── __init__.py
│       │   ├── movie.py
│       │   ├── tv.py
│       │   ├── person.py
│       │   └── watchlist.py
│       ├── config.py           # Загрузка конфигурации
│       ├── exceptions.py       # Кастомные исключения
│       └── utils/
│           ├── __init__.py
│           ├── validators.py
│           └── helpers.py
└── tests/
    ├── conftest.py
    ├── unit/
    │   ├── test_cli/
    │   ├── test_api/
    │   ├── test_storage/
    │   └── test_formatters/
    └── integration/
        ├── test_search.py
        ├── test_watchlist.py
        └── test_auth.py
```

### 3.3 REST API TMDB — Используемые Endpoints

| Команда | Метод | Endpoint | Описание |
|---|---|---|---|
| search | GET | `/search/multi` | Поиск по всем типам |
| search | GET | `/search/movie` | Поиск фильмов |
| search | GET | `/search/tv` | Поиск сериалов |
| search (genre) | GET | `/discover/movie` | Поиск по жанру |
| search (genre) | GET | `/discover/tv` | Поиск сериалов по жанру |
| details | GET | `/movie/{id}` | Детали фильма |
| details | GET | `/tv/{id}` | Детали сериала |
| details cast | GET | `/movie/{id}/credits` | Актёры фильма |
| details cast | GET | `/tv/{id}/credits` | Актёры сериала |
| details reviews | GET | `/movie/{id}/reviews` | Отзывы к фильму |
| rate | POST | `/movie/{id}/rating` | Выставить оценку фильму |
| rate | POST | `/tv/{id}/rating` | Выставить оценку сериалу |
| recommend | GET | `/movie/{id}/recommendations` | Рекомендации по фильму |
| recommend | GET | `/tv/{id}/recommendations` | Рекомендации по сериалу |
| popular | GET | `/movie/popular` | Популярные фильмы |
| popular | GET | `/tv/popular` | Популярные сериалы |
| trending | GET | `/trending/{type}/{window}` | Трендовый контент |
| auth | GET | `/authentication/token/new` | Получить request token |
| auth | POST | `/authentication/session/new` | Создать сессию |
| auth | DELETE | `/authentication/session` | Удалить сессию |
| auth status | GET | `/account` | Информация об аккаунте |
| genres | GET | `/genre/movie/list` | Список жанров фильмов |
| genres | GET | `/genre/tv/list` | Список жанров сериалов |

### 3.4 Обработка ошибок

| Код / Тип ошибки | Описание | Поведение системы |
|---|---|---|
| HTTP 401 | Неверный или отсутствующий API ключ | `Ошибка авторизации. Проверьте API ключ.` + exit code 1 |
| HTTP 404 | Контент не найден по ID | `Фильм/сериал с ID {id} не найден.` + exit code 2 |
| HTTP 429 | Rate limit TMDB превышен | Exponential backoff, 3 retry (1s, 2s, 4s), затем ошибка |
| HTTP 5xx | Ошибка сервера TMDB | Retry 2 раза, затем: `Сервис TMDB временно недоступен.` |
| ConnectionError | Нет подключения к интернету | `Нет подключения к сети. Проверьте интернет-соединение.` |
| TimeoutError | Превышен таймаут запроса (30s) | `Запрос занял слишком долго. Попробуйте позже.` |
| InvalidRating | Рейтинг вне диапазона 0.5–10.0 | `Оценка должна быть от 0.5 до 10.0 (кратно 0.5)` |
| DuplicateWatchlist | ID уже в watchlist | Предупреждение + предложение обновить запись |
| AuthRequired | Действие требует авторизации | `Для этого действия нужна авторизация: movie-tracker auth login` |
| ConfigNotFound | Конфиг-файл не найден | Инициализация с дефолтными значениями + уведомление |

### 3.5 Кэширование

| Тип запроса | TTL | Стратегия инвалидации |
|---|---|---|
| search (поиск) | 60 минут | По истечению TTL или принудительно (`--no-cache`) |
| details (детали) | 24 часа | По истечению TTL |
| popular | 3 часа | По истечению TTL |
| trending (day) | 30 минут | По истечению TTL |
| trending (week) | 3 часа | По истечению TTL |
| recommendations | 12 часов | При изменении watchlist |
| genres list | 7 дней | По истечению TTL |
| account info | Не кэшируется | Всегда актуальный запрос |

**Хранилище кэша:** `~/.movie-tracker/cache/` (diskcache, SQLite-based). Максимальный объём: 100 МБ. При переполнении вытесняются старейшие записи (LRU).

**Команда очистки:** `movie-tracker cache clear [--older-than <hours>]`

---

## 4. Конфигурация

### 4.1 Файл конфигурации

Конфигурация хранится в `~/.movie-tracker/settings.toml` и поддерживает переопределение через переменные окружения с префиксом `MOVIE_TRACKER_`.

```toml
# ~/.movie-tracker/settings.toml

[api]
key = ""                       # TMDB API ключ (обязателен)
base_url = "https://api.themoviedb.org/3"
timeout = 30                   # Таймаут запроса в секундах
max_retries = 3                # Количество повторных попыток
retry_backoff = 1.0            # Начальный интервал backoff (сек)

[output]
format = "table"               # table | json | csv
language = "ru-RU"             # Язык ответов TMDB
region = "RU"                  # Регион для локализации
color = true                   # Цветной вывод
page_size = 10                 # Результатов на странице

[cache]
enabled = true
dir = "~/.movie-tracker/cache"
max_size_mb = 100

[storage]
dir = "~/.movie-tracker"
watchlist_file = "watchlist.json"

[logging]
level = "WARNING"              # DEBUG | INFO | WARNING | ERROR
file = "~/.movie-tracker/movie-tracker.log"
rotation = "10 MB"
retention = "30 days"
```

### 4.2 Переменные окружения

| Переменная | Описание | Приоритет |
|---|---|---|
| `MOVIE_TRACKER_API__KEY` | TMDB API ключ | Высший (переопределяет settings.toml) |
| `MOVIE_TRACKER_OUTPUT__FORMAT` | Формат вывода | Высший |
| `MOVIE_TRACKER_OUTPUT__LANGUAGE` | Язык | Высший |
| `MOVIE_TRACKER_CACHE__ENABLED` | Включить кэш | Высший |
| `MOVIE_TRACKER_LOGGING__LEVEL` | Уровень логов | Высший |
| `TMDB_API_KEY` | Альтернативный ключ (legacy) | Средний |

---

## 5. Логирование

### 5.1 Уровни и формат логов

| Уровень | Когда используется | Пример |
|---|---|---|
| `DEBUG` | Детали HTTP запросов, ответов, кэш hit/miss | `GET /search/multi?query=Inception → 200 OK (123ms, cache miss)` |
| `INFO` | Успешные операции пользователя | `Добавлен в watchlist: Fight Club (ID: 550)` |
| `WARNING` | Некритичные проблемы, fallback | `Cache hit expired, refetching...` |
| `ERROR` | Ошибки API, хранилища, конфига | `TMDB API returned 404 for movie ID 9999999` |
| `CRITICAL` | Фатальные ошибки (выход из приложения) | `Config file corrupted, cannot proceed` |

### 5.2 Формат JSON-лога (файл)

```json
{
  "timestamp": "2025-04-15T14:32:01.123Z",
  "level": "ERROR",
  "message": "TMDB API request failed",
  "command": "details",
  "tmdb_id": 550,
  "http_status": 429,
  "retry_attempt": 2,
  "elapsed_ms": 5043
}
```

---

## 6. Тестирование

### 6.1 Стратегия тестирования

| Уровень | Инструмент | Цель покрытия | Описание |
|---|---|---|---|
| Unit тесты | pytest | ≥ 80% | Тестирование отдельных функций и классов с mock-ами |
| Интеграционные | pytest + pytest-httpx | ≥ 60% | Тестирование взаимодействия компонентов |
| CLI тесты | typer.testing.CliRunner | 100% команд | Тестирование каждой команды и её опций |
| Contract тесты | pytest + httpx mock | Все endpoints | Проверка соответствия TMDB API контрактам |

### 6.2 Тест-кейсы по командам

| Команда | Позитивные сценарии | Негативные сценарии |
|---|---|---|
| search | Найден 1 результат; несколько результатов; пагинация; фильтр по жанру | Пустой запрос; нет результатов; невалидный тип |
| details | Полная инфо о фильме; секция cast; секция reviews | Несуществующий ID; нет прав доступа |
| add-watchlist | Новый элемент; с заметкой; с тегами | Дубликат; невалидный ID; нет сети |
| list-watchlist | Пустой список; фильтр по статусу; сортировка; `--stats` | Повреждённый файл watchlist |
| rate | Авторизован, оценка отправлена; только локально | Оценка вне диапазона; не авторизован |
| recommend | По ID; по жанрам; `--exclude-watched` | Нет данных для рекомендаций |
| popular | Фильмы; сериалы; с регионом | Невалидный регион; нет сети |
| trending | Day; week; по типу | Невалидный window; нет сети |
| auth | login flow; logout; status авторизован; status не авторизован | Неверный токен; истёкшая сессия |

### 6.3 CI/CD интеграция

- GitHub Actions pipeline: `lint (ruff, mypy)` → `unit tests` → `integration tests` → `coverage report`
- Порог покрытия: **80%**. При падении ниже — пайплайн завершается с ошибкой
- Матрица тестирования: Python 3.11, 3.12, 3.13 на `ubuntu-latest` и `macos-latest`
- Команды для локального запуска: `hatch run test`, `hatch run lint`, `hatch run coverage`

---

## 7. Документация TMDB API

### 7.1 Аутентификация

TMDB поддерживает два метода аутентификации:

- **API Key (v3 auth):** передаётся в заголовке `Authorization: Bearer {api_key}` или query param `api_key=`. Требуется для всех запросов.
- **Session ID:** требуется для действий от имени пользователя (оценки, watchlist). Получается через 3-шаговый OAuth flow.

```http
GET https://api.themoviedb.org/3/movie/550
Authorization: Bearer eyJhbGciOiJIUzI1NiJ9...
Content-Type: application/json
Accept: application/json
```

### 7.2 Структура ответа — Поиск (`/search/multi`)

```json
{
  "page": 1,
  "results": [
    {
      "id": 550,
      "media_type": "movie",
      "title": "Fight Club",
      "original_title": "Fight Club",
      "overview": "A ticking-time-bomb insomniac...",
      "release_date": "1999-10-15",
      "genre_ids": [18, 53, 35],
      "vote_average": 8.439,
      "vote_count": 29150,
      "popularity": 76.321,
      "poster_path": "/pB8BM7pdSp6B6Ih7QZ4DrQ3PmJK.jpg",
      "backdrop_path": "/hZkgoQYus5vegHoetLkCJzb17zJ.jpg"
    }
  ],
  "total_pages": 5,
  "total_results": 97
}
```

### 7.3 Rate Limits и квоты

> ⚠️ **Rate Limit TMDB API**
>
> - Бесплатный план: **40 запросов / 10 секунд**
> - При превышении: HTTP `429` с заголовком `Retry-After`
> - Стратегия: exponential backoff с jitter (1s → 2s → 4s)
> - Кэширование снижает реальное количество запросов на 60–80%

### 7.4 Получение API ключа

1. Зарегистрируйтесь или войдите на [themoviedb.org](https://www.themoviedb.org)
2. Перейдите в **Settings → API**
3. Запросите API ключ (Developer use / Personal)
4. Укажите ключ в конфиге: `movie-tracker auth token YOUR_API_KEY`

---

## 8. Нефункциональные требования

### 8.1 Производительность

- Время запуска утилиты (холодный старт): не более **500 мс**
- Время выполнения команды при cache hit: не более **200 мс**
- Время выполнения команды при cache miss (сетевой запрос): не более **3 сек** при нормальном соединении
- Размер исполняемого файла (при сборке в бинарь через PyInstaller): не более **30 МБ**

### 8.2 Совместимость

| Платформа | Поддерживаемые версии | Метод установки |
|---|---|---|
| macOS | 12 Monterey, 13 Ventura, 14 Sonoma, 15+ | pip, homebrew, скачать бинарь |
| Linux (Debian/Ubuntu) | 20.04, 22.04, 24.04 LTS | pip, apt (PPA), скачать бинарь |
| Linux (RHEL/Fedora) | RHEL 8+, Fedora 38+ | pip, скачать бинарь |
| Windows | Windows 10, Windows 11 | pip, winget, скачать .exe |
| Python версия | 3.11, 3.12, 3.13 | Требование для pip установки |

### 8.3 Безопасность

- API ключ и `session_id` хранятся в `auth.json` с правами доступа `600` (только владелец)
- API ключ никогда не отображается в логах (маскируется: `sk-***...xxx`)
- Персональные заметки watchlist хранятся локально, не передаются на сервер
- HTTPS-only для всех запросов к TMDB API (проверка SSL сертификата обязательна)
- Входные данные валидируются перед отправкой в API (injection prevention)

### 8.4 Расширяемость

- Архитектура плагинов: новые команды добавляются созданием модуля в `cli/` с регистрацией в `main.py`
- Поддержка нескольких форматтеров вывода (table / json / csv) с возможностью добавления новых
- Абстракция хранилища: возможность замены TinyDB на SQLite без изменения CLI-слоя

---

## 9. Установка и развёртывание

### 9.1 Установка из PyPI

```bash
# Установка
pip install movie-tracker-cli

# Инициализация конфигурации
movie-tracker init

# Установка API ключа
movie-tracker auth token YOUR_TMDB_API_KEY

# Проверка установки
movie-tracker --version
```

### 9.2 Установка из исходников (разработка)

```bash
git clone https://github.com/your-org/movie-tracker-cli.git
cd movie-tracker-cli

# Установка hatch
pip install hatch

# Создание окружения и установка зависимостей
hatch env create

# Запуск в dev-режиме
hatch run movie-tracker --help

# Запуск тестов
hatch run test

# Линтинг
hatch run lint
```

### 9.3 Быстрый старт после установки

1. Установите утилиту: `pip install movie-tracker-cli`
2. Получите API ключ на [themoviedb.org/settings/api](https://www.themoviedb.org/settings/api)
3. Сохраните ключ: `movie-tracker auth token YOUR_KEY`
4. Выполните первый поиск: `movie-tracker search 'Inception'`
5. *(Опц.)* Войдите в TMDB для полного функционала: `movie-tracker auth login`

---

## 10. Глоссарий

| Термин | Определение |
|---|---|
| **TMDB** | The Movie Database — открытая база данных кинофильмов и сериалов с публичным API (themoviedb.org) |
| **CLI** | Command Line Interface — интерфейс взаимодействия с программой через командную строку |
| **Watchlist** | Персональный список фильмов/сериалов для просмотра, хранимый локально |
| **Session ID** | Идентификатор сессии TMDB, выдаваемый после OAuth авторизации пользователя |
| **Request Token** | Временный токен TMDB (15 мин.), используемый при OAuth flow для получения Session ID |
| **Cache Hit** | Ситуация, когда данные найдены в кэше и HTTP-запрос к API не выполняется |
| **Cache Miss** | Ситуация, когда данных нет в кэше и выполняется HTTP-запрос к API |
| **Rate Limit** | Ограничение количества запросов к API в единицу времени (40 req/10s для TMDB) |
| **Exponential Backoff** | Стратегия повтора запросов с экспоненциально увеличивающимися паузами |
| **TTL** | Time To Live — время жизни записи в кэше, после которого она считается устаревшей |
| **Endpoint** | Конкретный URL-адрес API, предназначенный для выполнения определённого действия |
| **IMDB ID** | Идентификатор в базе данных IMDb (формат: `tt1234567`), возвращается TMDB в деталях |

---

> **Ссылки:**
> [TMDB API Docs](https://developer.themoviedb.org/docs) ·
> [TMDB API Reference](https://developer.themoviedb.org/reference/intro/getting-started) ·
> [Typer Docs](https://typer.tiangolo.com) ·
> [Rich Docs](https://rich.readthedocs.io)

---

*Версия ТЗ: 1.0.0 | Дата: Апрель 2025 | Статус: Draft*
