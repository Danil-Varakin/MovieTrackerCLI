# MovieTracker CLI

Два независимых CLI-приложения для поиска фильмов и сериалов, написанные разными ИИ-ассистентами по одному техническому заданию.

Оба используют **Kinopoisk API Unofficial** и реализуют одинаковый функционал: поиск, watchlist, оценки, рекомендации, популярное.

- `Claude/` — версия от Claude (Anthropic), команда `movie-tracker-claude`
- `Codex/` — версия от Codex (OpenAI), команда `movie-tracker`

---

## Возможности

| Действие | Claude Edition | Codex Edition |
|---|---|---|
| Поиск фильма | `movie-tracker-claude search "Название"` | `movie-tracker search "Название"` |
| Подробная информация | `movie-tracker-claude details ID` | `movie-tracker details ID` |
| Добавить в список | `movie-tracker-claude add-watchlist ID` | `movie-tracker add-watchlist ID` |
| Показать список | `movie-tracker-claude list-watchlist` | `movie-tracker list-watchlist` |
| Поставить оценку | `movie-tracker-claude rate ID 8.5` | `movie-tracker rate ID 8.5` |
| Рекомендации | `movie-tracker-claude recommend --based-on ID` | `movie-tracker recommend --based-on ID` |
| Популярное | `movie-tracker-claude popular` | `movie-tracker popular` |
| В тренде | `movie-tracker-claude trending` | `movie-tracker trending` |

---

## Требования

- Python 3.11+
- git
- Бесплатный API-ключ Kinopoisk: [kinopoiskapiunofficial.tech](https://kinopoiskapiunofficial.tech) → Регистрация → Dashboard → API Keys (лимит: 500 запросов в сутки)

---

## Структура репозитория

```text
MovieTrackerCLI/
├── Claude/     # Claude Edition — movie-tracker-claude
└── Codex/      # Codex Edition — movie-tracker
```

---

## Запуск Claude Edition

### macOS / Linux

```bash
git clone https://github.com/Danil-Varakin/MovieTrackerCLI.git
cd MovieTrackerCLI/Claude
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
movie-tracker-claude init
movie-tracker-claude auth token ВАШ_КЛЮЧ
movie-tracker-claude search "Интерстеллар"
```

### Windows (PowerShell)

```powershell
git clone https://github.com/Danil-Varakin/MovieTrackerCLI.git
cd MovieTrackerCLI\Claude
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e .
movie-tracker-claude init
movie-tracker-claude auth token ВАШ_КЛЮЧ
movie-tracker-claude search "Интерстеллар"
```

---

## Запуск Codex Edition

### macOS / Linux

```bash
git clone https://github.com/Danil-Varakin/MovieTrackerCLI.git
cd MovieTrackerCLI/Codex
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
movie-tracker init
movie-tracker auth token ВАШ_КЛЮЧ
movie-tracker search "Интерстеллар"
```

### Windows (PowerShell)

```powershell
git clone https://github.com/Danil-Varakin/MovieTrackerCLI.git
cd MovieTrackerCLI\Codex
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e .
movie-tracker init
movie-tracker auth token ВАШ_КЛЮЧ
movie-tracker search "Интерстеллар"
```

---

## Документация для разработчиков

- [Claude Edition](./Claude/CLAUDE_VERSION.md)
- [Codex Edition](./Codex/MOVIETRACKER_CLI_CODEX_VERSION.md)
