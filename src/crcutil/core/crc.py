from __future__ import annotations

import sys
import zlib
from pathlib import Path

from alive_progress import alive_bar

from crcutil.core.prompt import Prompt
from crcutil.dto.hash_diff_report_dto import HashDiffReportDTO
from crcutil.dto.hash_dto import HashDTO
from crcutil.enums.user_request import UserRequest
from crcutil.util.crcutil_logger import CrcutilLogger
from crcutil.util.file_importer import FileImporter
from crcutil.util.keyboard_monitor import KeyboardMonitor


class Crc:
    def __init__(
        self,
        location: Path,
        hash_file_location: Path,
        user_request: UserRequest,
        hash_diff_1: list[HashDTO],
        hash_diff_2: list[HashDTO],
    ) -> None:
        self.location = location
        self.hash_file_location = hash_file_location
        self.user_request = user_request
        self.hash_diff_1 = hash_diff_1
        self.hash_diff_2 = hash_diff_2

    def do(self) -> HashDiffReportDTO | None:
        if self.user_request is UserRequest.HASH:
            match self.__get_hash_status():
                case -1:
                    self.__create_hash()
                case 0:
                    self.__continue_hash()
                case 1:
                    self.__create_hash(is_hash_overwrite=True)
            return None
        elif self.user_request is UserRequest.DIFF:
            hash_1 = self.hash_diff_1
            hash_2 = self.hash_diff_2

            hash_1_dict = {dto.file: dto.crc for dto in hash_1}
            hash_2_dict = {dto.file: dto.crc for dto in hash_2}

            changes = [
                dto
                for dto in hash_2
                if dto.file in hash_1_dict and hash_1_dict[dto.file] != dto.crc
            ]
            missing_1 = [
                dto_1 for dto_1 in hash_1 if dto_1.file not in hash_2_dict
            ]
            missing_2 = [
                dto_2 for dto_2 in hash_2 if dto_2.file not in hash_1_dict
            ]

            return HashDiffReportDTO(
                changes=changes, missing_1=missing_1, missing_2=missing_2
            )
        else:
            description = f"Unsupported request: {self.user_request!s}"
            raise ValueError(description)

    def __create_hash(self, is_hash_overwrite: bool = False) -> None:
        if is_hash_overwrite:
            Prompt.overwrite_hash_confirm()

        self.hash_file_location.write_text("{}")

        all_locations = self.seek(self.location)
        self.__write_locations(all_locations)
        self.__write_hash(self.location, all_locations)

    def __continue_hash(self) -> None:
        offset_position = ""

        original_hashes = FileImporter.get_hash(self.hash_file_location)

        for hash_dto in original_hashes:
            if not hash_dto.crc:
                offset_position = hash_dto.file
                break

        filtered_locations = self.seek(self.location, offset_position)
        self.__write_hash(
            self.location, filtered_locations, len(original_hashes)
        )

    def __write_locations(self, str_relative_locations: list[str]) -> None:
        hashes = [HashDTO(file=x, crc=0) for x in str_relative_locations]
        FileImporter.save_hash(self.hash_file_location, hashes)

    def __write_hash(
        self,
        parent_location: Path,
        str_relative_locations: list[str],
        total_count: int = 0,
    ) -> None:
        monitor = KeyboardMonitor()
        try:
            monitor.start()
            play_icon, pause_icon = (
                ("▶", "⏸")
                if sys.stdout.encoding.lower().startswith("utf")
                else (">", "||")
            )

            pause_description = "\n*Press p to pause/resume"
            quit_description = "*Press q to quit"
            CrcutilLogger.get_console_logger().info(pause_description)
            CrcutilLogger.get_console_logger().info(quit_description)

            length = (
                total_count if total_count else len(str_relative_locations)
            )
            with alive_bar(length, dual_line=True) as bar:
                if total_count:
                    offset_count = total_count - len(str_relative_locations)
                    for _ in range(offset_count):
                        bar()

                for str_relative_location in str_relative_locations:
                    while monitor.is_paused:
                        bar.text = f"{pause_icon} PAUSED"
                    while monitor.is_quit:
                        sys.exit(0)

                    bar.text = f"{play_icon} {str_relative_location}"

                    relative_location = Path(str_relative_location)
                    abs_location = (
                        parent_location / relative_location
                    ).resolve()

                    crc = self.__get_crc_hash(abs_location, parent_location)
                    hashes = FileImporter.get_hash(self.hash_file_location)
                    hashes.append(HashDTO(file=str_relative_location, crc=crc))

                    FileImporter.save_hash(self.hash_file_location, hashes)

                    bar()
        except KeyboardInterrupt:
            monitor.stop()

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
        sorted_normalized = [str(x) for x in sorted_normalized if x != Path()]

        if not offset_position:
            return sorted_normalized
        else:
            is_collect = False
            remaining = []
            for item in sorted_normalized:
                # Only flip once
                if item == offset_position and not is_collect:
                    is_collect = not is_collect
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
                if not dto.crc:
                    return 0

            status = 1

        return status

    def __get_crc_hash(self, location: Path, parent_location: Path) -> int:
        crc = 0
        crc = (
            zlib.crc32(
                self.__get_crc_from_path(location, parent_location), crc
            )
            & 0xFFFFFFFF
        )
        crc = zlib.crc32(self.__get_crc_from_attr(location), crc) & 0xFFFFFFFF

        if location.is_file():
            crc = (
                zlib.crc32(self.__get_crc_from_file_contents(location), crc)
                & 0xFFFFFFFF
            )

        return crc

    def __get_crc_from_path(
        self, location: Path, parent_location: Path
    ) -> bytes:
        return str(location.relative_to(parent_location)).encode("utf-8")

    def __get_crc_from_attr(self, location: Path) -> bytes:
        stat = location.stat()
        if location.is_dir():
            return f"{stat.st_mode}".encode()
        else:
            return f"{stat.st_size}:{stat.st_mode}".encode()

    def __get_crc_from_file_contents(self, location: Path) -> bytes:
        file_crc = 0
        with location.open("rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                file_crc = zlib.crc32(chunk, file_crc) & 0xFFFFFFFF
        return file_crc.to_bytes(4, "little", signed=False)

    def __get_missing_hash_dto(
        self, hash_1: list[HashDTO], hash_2: list[HashDTO]
    ) -> tuple[list[HashDTO], list[HashDTO]]:
        hash_1_dict = {dto.file: dto.crc for dto in hash_1}
        hash_2_dict = {dto.file: dto.crc for dto in hash_2}

        missing_1 = [
            dto_1 for dto_1 in hash_1 if not hash_2_dict.get(dto_1.file)
        ]
        missing_2 = [
            dto_2 for dto_2 in hash_2 if not hash_1_dict.get(dto_2.file)
        ]
        return missing_1, missing_2
