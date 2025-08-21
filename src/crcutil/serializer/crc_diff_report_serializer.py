from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from crcutil.dto.crc_diff_report_dto import CrcDiffReportDTO

from crcutil.util.static import Static


class CrcDiffReportSerializer(Static):
    @staticmethod
    def to_json(dto: CrcDiffReportDTO) -> dict:
        obj = {}
        changes = dto.changes
        missing_1 = dto.missing_1
        missing_2 = dto.missing_2

        obj["Changes"] = [x.file for x in changes]
        obj["Present in 1 Missing in 2"] = [x.file for x in missing_1]
        obj["Present in 2 Missing in 1"] = [x.file for x in missing_2]
        return obj

    @staticmethod
    def to_dto(crc_diff_report_dict: dict) -> CrcDiffReportDTO:
        raise NotImplementedError
