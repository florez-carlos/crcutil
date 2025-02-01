from crcutil.dto.crc_dto import CrcDTO
from crcutil.dto.hash_dto import HashDTO
from crcutil.util.static import Static


class HashSerializer(Static):
    @staticmethod
    def to_json(hash_dto: HashDTO) -> dict:
        return {
            crc_dto.relative_path: crc_dto.crc for crc_dto in hash_dto.crcs
        }

    @staticmethod
    def to_dto(hash_dict: dict) -> HashDTO:
        return HashDTO(
            crcs=[
                CrcDTO(relative_path=path, crc=crc)
                for path, crc in hash_dict.items()
            ]
        )
