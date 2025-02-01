from pathlib import Path
import zlib

from crcutil.dto.crc_dto import CrcDTO
from crcutil.dto.hash_dto import HashDTO
from crcutil.util.crcutil_logger import CrcutilLogger
from crcutil.util.file_importer import FileImporter

class crc:

    def __init__(self, location: Path, hash_dto: HashDTO) -> None:
        self.location = location
        self.hash_dto = hash_dto

    def do(self):

        self.hash_dto = HashDTO()
        parent_location = Path("/home/carlos/workspace/test")
        offset_position = ""
        offset_index = - 1
        original_crcs = self.hash_dto.crcs
        for index, crc_dto in enumerate(original_crcs):
            if not crc_dto.crc:
                offset_position = crc_dto.relative_path
                offset_index = index
                break
        if offset_index:
            offset_crcs = self.hash_dto.crcs[:offset_index]
            self.hash_dto = HashDTO(offset_crcs)


        filtered_locations = self.seek(parent_location, offset_position)
        print(f"filtered_locations: {filtered_locations}")

        for filtered_location in filtered_locations:

        for filtered_location in filtered_locations:
            crc = self.__get_crc_hash(
                (parent_location / Path(filtered_location)
            ).resolve(), parent_location)
            self.hash_dto.crcs.append(
                CrcDTO(relative_path=filtered_location, crc=crc)
            )
            FileImporter.write_hash(Path("test.json"), self.hash_dto)

        pass

    def __walk(self, path: Path) -> list[Path]:
        """
        Recursively collects all file/dirs in a given path

        Args:
            path (pathlib.Path): The parent directory to traverse

        Returns:
            [Path] All file/dir in the tree
        """
        items = []

        if path.is_file():
            items.append(path)
        elif path.is_dir():
            items.append(path)
            for child in path.iterdir():
                sub_items = self.__walk(child)
                items.extend(sub_items)

        return items


    def seek(self, initial_position: Path, offset_position: str = "") -> list[str]:

        raw =  self.__walk(initial_position)
        normalized = [x.relative_to(initial_position) for x in raw]
        sorted_normalized = sorted(normalized, key=lambda path: path.name)
        sorted_normalized = [str(x) for x in sorted_normalized]

        if not offset_position:
            return [
                path if path != Path() else str(initial_position)
                for path in sorted_normalized
            ]
        else:
            is_collect = False
            remaining = []
            for item in sorted_normalized:
                if item == offset_position:
                    is_collect = not is_collect
                    continue
                if is_collect:
                    remaining.append(item)
            return remaining

    def __is_locations_eq(
        self, display_name: str, location_a: Path, location_b: Path
    ) -> bool:
        result_a = self.__get_crc_hash(location_a, location_a)
        result_b = self.__get_crc_hash(location_b, location_b)
        is_eq = result_a == result_b

        description = (
            f"{display_name} CRC results: {result_a} - {result_b} -> "
            f"is_eq: {is_eq}"
        )
        CrcutilLogger.get_logger().debug(description)

        return is_eq

    def __get_crc_hash(self, location: Path, parent_location: Path) -> int:
        crc = 0
        crc = zlib.crc32(
            self.__get_crc_from_path(location, parent_location), crc
        )
        crc = zlib.crc32(self.__get_crc_from_attr(location), crc)

        if location.is_file():
            crc = zlib.crc32(self.__get_crc_from_file_contents(location), crc)

        if location.is_dir():
            children = location.iterdir()
            for child in children:
                child_crc = self.__get_crc_hash(child, parent_location)
                crc = zlib.crc32(child_crc.to_bytes(4, "little"), crc)

        return crc

    def __get_crc_from_path(
        self, location: Path, parent_location: Path
    ) -> bytes:
        return str(location.relative_to(parent_location)).encode("utf-8")

    def __get_crc_from_attr(self, location: Path) -> bytes:
        if location.is_dir():
            return location.name.encode("utf-8")
        stat = location.stat()
        file_size = stat.st_size
        file_mode = stat.st_mode
        return f"{file_size}:{file_mode}".encode()

    def __get_crc_from_file_contents(self, location: Path) -> bytes:
        file_crc = 0
        with location.open("rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                file_crc = zlib.crc32(chunk, file_crc)
        return file_crc.to_bytes(4, "little")
