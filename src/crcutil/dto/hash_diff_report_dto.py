from __future__ import annotations

from dataclasses import dataclass

from crcutil.dto.hash_dto import HashDTO


# Frozen=True creates an implicit hash method, eq is created by default
@dataclass(frozen=True)
class HashDiffReportDTO:
    changes: list[HashDTO]
    missing_1: list[HashDTO]
    missing_2: list[HashDTO]
