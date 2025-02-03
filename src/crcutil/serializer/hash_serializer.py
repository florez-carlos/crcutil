from __future__ import annotations

from crcutil.dto.hash_dto import HashDTO
from crcutil.util.static import Static


class HashSerializer(Static):
    @staticmethod
    def to_json(hash_dto: list[HashDTO]) -> dict:
        return {dto.file: dto.crc for dto in hash_dto}

    @staticmethod
    def to_dto(hash_dict: dict) -> list[HashDTO]:
        return [HashDTO(file=file, crc=crc) for file, crc in hash_dict.items()]
