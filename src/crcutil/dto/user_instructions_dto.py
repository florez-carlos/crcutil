from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from crcutil.enums.user_request import UserRequest


# Frozen=True creates an implicit hash method, eq is created by default
@dataclass(frozen=True)
class UserInstructionsDTO:
    request: UserRequest
    location: Path
    crc_diff_files: list[Path]
    output: Path
