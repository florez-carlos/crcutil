from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from crcutil.dto.checksum_dto import ChecksumDTO


from dataclasses import dataclass


# Frozen=True creates an implicit hash method, eq is created by default
@dataclass(frozen=True)
class CrcDiffReportDTO:
    changes: list[ChecksumDTO]
    missing_1: list[ChecksumDTO]
    missing_2: list[ChecksumDTO]
