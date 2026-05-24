"""Фикстуры и тестовые данные для Кинопоиск API."""

import pytest

# ─── Mock-данные в формате Кинопоиска ────────────────────────

MOCK_KP_SEARCH_RESPONSE = {
    "total": 1,
    "totalPages": 1,
    "items": [
        {
            "kinopoiskId": 447301,
            "type": "FILM",
            "nameRu": "Начало",
            "nameEn": "Inception",
            "nameOriginal": "Inception",
            "year": 2010,
            "rating": 8.7,
            "ratingVoteCount": 500000,
            "genres": [{"genre": "фантастика"}, {"genre": "боевик"}],
            "description": "Профессиональный вор, крадущий идеи...",
        }
    ],
}

MOCK_KP_FILM_DETAILS = {
    "kinopoiskId": 447301,
    "type": "FILM",
    "nameRu": "Начало",
    "nameEn": "Inception",
    "nameOriginal": "Inception",
    "year": 2010,
    "ratingKinopoisk": 8.7,
    "ratingImdb": 8.8,
    "description": "Профессиональный вор, крадущий идеи из подсознания...",
    "genres": [{"genre": "фантастика"}, {"genre": "боевик"}],
    "countries": [{"country": "США"}],
    "filmLength": 148,
    "slogan": "Your mind is the scene of the crime",
    "posterUrl": "https://example.com/poster.jpg",
}

MOCK_KP_STAFF = [
    {
        "staffId": 26204,
        "nameRu": "Кристофер Нолан",
        "nameEn": "Christopher Nolan",
        "professionKey": "DIRECTOR",
        "professionText": "Режиссёр",
        "description": "",
        "order": 0,
    },
    {
        "staffId": 6498,
        "nameRu": "Леонардо ДиКаприо",
        "nameEn": "Leonardo DiCaprio",
        "professionKey": "ACTOR",
        "professionText": "Актёр",
        "description": "Кобб",
        "order": 1,
    },
]

MOCK_KP_TOP = {
    "pagesCount": 5,
    "films": [
        {
            "filmId": 326,
            "nameRu": "Побег из Шоушенка",
            "nameEn": "The Shawshank Redemption",
            "year": "1994",
            "rating": "9.1",
            "genres": [{"genre": "драма"}],
        }
    ],
}

# Обратная совместимость с тестами — оставляем алиасы
MOCK_SEARCH_RESPONSE = MOCK_KP_SEARCH_RESPONSE
MOCK_GENRES_MOVIE = {}
