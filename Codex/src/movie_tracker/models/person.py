from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Person:
    name: str
    role: str = ""
    profession: str = ""
