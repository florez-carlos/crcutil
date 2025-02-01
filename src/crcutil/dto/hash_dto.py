from __future__ import annotations

from dataclasses import dataclass, field

from crcutil.dto.crc_dto import CrcDTO


# Frozen=True creates an implicit hash method, eq is created by default
@dataclass(frozen=True)
class HashDTO:
    crcs: list[CrcDTO] = field(default_factory=list)
