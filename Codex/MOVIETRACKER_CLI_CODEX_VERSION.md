# MovieTracker CLI Codex

**MovieTracker CLI Codex** — моя версия консольного MovieTracker по ТЗ. Она сохраняет интерфейс `movie-tracker`, но вместо TMDB использует **Kinopoisk API Unofficial** и честно разделяет API-функции и локальные пользовательские функции.

## Чем эта версия отличается

- Внешний API: `https://kinopoiskapiunofficial.tech/api`.
- Авторизация: API-ключ сохраняется командой `movie-tracker auth token`; OAuth-login из TMDB заменён на понятное сообщение, потому что Kinopoisk API Unofficial не предоставляет TMDB-подобную пользовательскую сессию.
- Watchlist, личные оценки, отзывы, заметки и теги хранятся локально в `~/.movie-tracker`.
- `recommend` использует похожие фильмы Kinopoisk или локальные жанровые предпочтения из watchlist.
- `popular` и `trending` адаптированы под доступные коллекции/топы Kinopoisk API Unofficial.
- Утилита устанавливается как обычная глобальная команда `movie-tracker`, чтобы ей можно было пользоваться из терминала после установки.

## Установка для разработчиков

Требования: **Python 3.11+**, **git**

### macOS / Linux

```bash
git clone https://github.com/Danil-Varakin/MovieTrackerCLI.git
cd MovieTrackerCLI/Codex
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
movie-tracker init
movie-tracker auth token ВАШ_КЛЮЧ
movie-tracker --help
```

### Windows (PowerShell)

```powershell
git clone https://github.com/Danil-Varakin/MovieTrackerCLI.git
cd MovieTrackerCLI\Codex
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
movie-tracker init
movie-tracker auth token ВАШ_КЛЮЧ
movie-tracker --help
```

### Hatch

```bash
pip install hatch
hatch env create
hatch run movie-tracker --help
```

Сборка переносимого бинарника:

```bash
pip install -e ".[dev]"
pyinstaller packaging/movie-tracker.spec
# результат появится в dist/
```

## Конфигурация

Основные способы передать ключ:

```bash
movie-tracker auth token YOUR_KINOPOISK_API_KEY
```

или через переменную окружения:

```bash
MOVIE_TRACKER_API__KEY=YOUR_KINOPOISK_API_KEY
```

Поддерживаются также `KINOPOISK_API_KEY` и `KINOPOISK_UNOFFICIAL_API_KEY`.

## Тестирование

```bash
pytest
pytest --cov=movie_tracker --cov-report=term-missing
ruff check src tests
mypy src
```

Через Hatch:

```bash
hatch run test
hatch run coverage
hatch run lint
```

## Примеры команд

```bash
movie-tracker search "Брат" --type movie --output table
movie-tracker details 41519 --section cast
movie-tracker add-watchlist 41519 --status unwatched --priority 4 --tags "россия,классика"
movie-tracker list-watchlist --stats
movie-tracker rate 41519 9.0 --review "Нужно пересмотреть"
movie-tracker recommend --genres драма,криминал --exclude-watched
movie-tracker cache clear
```

## Ограничения Kinopoisk API Unofficial

Kinopoisk API Unofficial не является полным аналогом TMDB: в нём нет OAuth-сессии пользователя, удалённой синхронизации watchlist и отправки пользовательских оценок в профиль. Поэтому эта версия делает пользовательскую часть локальной и воспроизводимой, а сетевые команды используют только публичные данные API.
