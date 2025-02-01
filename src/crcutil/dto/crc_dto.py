from __future__ import annotations

from dataclasses import dataclass


# Frozen=True creates an implicit hash method, eq is created by default
@dataclass(frozen=True)
class CrcDTO:
    relative_path: str
    crc: int = 0
