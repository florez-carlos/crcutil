from __future__ import annotations

from crcutil.dto.checksum_dto import ChecksumDTO
from crcutil.util.static import Static


class ChecksumSerializer(Static):
    @staticmethod
    def to_json(checksums: list[ChecksumDTO]) -> dict:
        return {checksum.file: checksum.crc for checksum in checksums}

    @staticmethod
    def to_dto(checksums_dict: dict) -> list[ChecksumDTO]:
        return [
            ChecksumDTO(file=file, crc=crc)
            for file, crc in checksums_dict.items()
        ]
