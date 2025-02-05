from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from crcutil.dto.hash_dto import HashDTO


from dataclasses import dataclass


# Frozen=True creates an implicit hash method, eq is created by default
@dataclass(frozen=True)
class HashDiffReportDTO:
    changes: list[HashDTO]
    missing_1: list[HashDTO]
    missing_2: list[HashDTO]
