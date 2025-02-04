from __future__ import annotations

from crcutil.dto.hash_diff_report_dto import HashDiffReportDTO
from crcutil.util.static import Static


class HashDiffReportSerializer(Static):
    @staticmethod
    def to_json(dto: HashDiffReportDTO) -> dict:
        dto = {}
        changes = dto.changes
        missing_1 = dto.missing_1
        missing_2 = dto.missing_2

        dto["Changes"] = changes
        dto["Present in 1 Missing in 2"] = missing_1
        dto["Present in 2 Missing in 1"] = missing_2
        return dto

    @staticmethod
    def to_dto(hash_diff_report_dict: dict) -> HashDiffReportDTO:
        raise NotImplementedError
