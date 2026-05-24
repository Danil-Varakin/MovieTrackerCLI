from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SeasonSummary:
    number: int
    episodes: int
