import zlib
from pathlib import Path

from crcutil.core.prompt import Prompt
from crcutil.dto.hash_dto import HashDTO
from crcutil.enums.user_request import UserRequest
from crcutil.util.crcutil_logger import CrcutilLogger
from crcutil.util.file_importer import FileImporter


class crc:
    def __init__(
        self,
        location: Path,
        hash_file_location: Path,
        user_request: UserRequest,
    ) -> None:
        self.location = location
        self.hash_file_location = hash_file_location
        self.user_request = user_request

    def do(self):
        if self.user_request is UserRequest.HASH:
            match self.__get_hash_status():
                case -1:
                    self.__create_hash()
                case 0:
                    self.__continue_hash()
                case 1:
                    self.__create_hash(is_hash_overwrite=True)
        elif self.user_request is UserRequest.DIFF:
            # TODO:
            pass
        else:
            description = f"Unsupported request: {self.user_request!s}"
            raise ValueError(description)

    def __create_hash(self, is_hash_overwrite=False) -> None:
        if is_hash_overwrite:
            Prompt.overwrite_hash_confirm()

        self.hash_file_location.write_text("{}")

        all_locations = self.seek(self.location)
        self.__write_hash(self.location, all_locations)

    def __continue_hash(self) -> None:
        offset_position = ""
        # offset_index = - 1

        original_hashes = FileImporter.get_hash(self.hash_file_location)

        for index, hash_dto in enumerate(original_hashes):
            if not hash_dto.crc:
                offset_position = hash_dto.file
                # offset_index = index
                break

        # if offset_index:
        #     offset_hashes = original_hashes[:offset_index]

        filtered_locations = self.seek(self.location, offset_position)
        self.__write_hash(self.location, filtered_locations)

    def __write_hash(
        self, parent_location: Path, str_relative_locations: list[str]
    ) -> None:
        for str_relative_location in str_relative_locations:
            relative_location = Path(str_relative_location)
            abs_location = (parent_location / relative_location).resolve()

            crc = self.__get_crc_hash(abs_location, parent_location)
            hashes = FileImporter.get_hash(self.hash_file_location)
            hashes.append(HashDTO(file=str_relative_location, crc=crc))
            FileImporter.save_hash(self.hash_file_location, hashes)

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

    def seek(
        self, initial_position: Path, offset_position: str = ""
    ) -> list[str]:
        raw = self.__walk(initial_position)
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

    def __get_hash_status(self) -> int:
        """
        Gets the current status of a Hash file:
        Possible values:
        -1) File does not exist
         0) File exists and is incomplete/pending
         1) File exists and is finished

        Returns:
            int: The status of the hash file
        """
        status = -1
        if self.hash_file_location.exists():
            hash_dto = FileImporter.get_hash(self.hash_file_location)

            for dto in hash_dto:
                if dto.crc is None:
                    status = 0
                    return status

            status = 1

        return status

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
