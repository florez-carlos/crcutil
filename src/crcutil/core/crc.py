from __future__ import annotations

import os
import sys
from pathlib import Path
from time import sleep

from alive_progress import alive_bar

from crcutil.core.checksum import Checksum
from crcutil.core.prompt import Prompt
from crcutil.dto.hash_diff_report_dto import HashDiffReportDTO
from crcutil.dto.hash_dto import HashDTO
from crcutil.enums.user_request import UserRequest
from crcutil.exception.corrupt_hash_error import CorruptHashError
from crcutil.util.crcutil_logger import CrcutilLogger
from crcutil.util.file_importer import FileImporter
from crcutil.util.keyboard_monitor import KeyboardMonitor
from crcutil.util.path_ops import PathOps


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
        self.monitor = KeyboardMonitor()

    def do(self) -> HashDiffReportDTO | None:
        """
        Performs a Hash/Diff

        Returns:
            HashDiffReportDTO | None: If request is Diff, None if Hash
        Raises:
            ValueError: If request other than diff or hash
        """
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

        description = f"Creating Hash: {self.location}"
        CrcutilLogger.get_logger().debug(description)

        all_locations = self.seek(self.location)
        self.__write_locations(all_locations)
        self.__write_hash(self.location, all_locations)

    def __continue_hash(self) -> None:
        if not Prompt.continue_hash_confirm():
            Prompt.overwrite_hash_confirm()
            self.__create_hash()
            return

        original_hashes = FileImporter.get_hash(self.hash_file_location)

        description = (
            f"Resuming existing Hash: {self.hash_file_location} "
            f"with location: {self.location}"
        )
        CrcutilLogger.get_logger().debug(description)

        pending_crcs = [
            hash_dto.file for hash_dto in original_hashes if not hash_dto.crc
        ]

        all_locations = self.seek(self.location)
        for hash_dto in original_hashes:
            if hash_dto.file not in all_locations:
                description = (
                    "An element in the Hash does not exist "
                    f"in the supplied location: {hash_dto.file}\n"
                    f"Cannot continue"
                )
                raise CorruptHashError(description)

        original_hashes_str = [x.file for x in original_hashes]
        for location in all_locations:
            if location not in original_hashes_str:
                description = (
                    "An element in the supplied location does not exist "
                    f"in the Hash: {location}\n"
                    f"Cannot continue"
                )
                raise CorruptHashError(description)

        filtered_locations = self.seek(self.location, pending_crcs)
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
        try:
            play_icon, pause_icon, cancel_icon = (
                ("▶", "⏸", "✖")
                if sys.stdout.encoding.lower().startswith("utf")
                else (">", "||", "X")
            )

            pause_description = "\n*Press p to pause/resume"
            quit_description = "*Press q to quit"
            CrcutilLogger.get_console_logger().info(pause_description)
            CrcutilLogger.get_console_logger().info(quit_description)

            self.monitor.start()
            length = (
                total_count if total_count else len(str_relative_locations)
            )
            with alive_bar(length, dual_line=True) as bar:
                if total_count:
                    offset_count = total_count - len(str_relative_locations)
                    for _ in range(offset_count):
                        bar()

                for str_relative_location in str_relative_locations:
                    abs_location = (
                        parent_location / Path(str_relative_location)
                    ).resolve()

                    checksum = Checksum(
                        location=abs_location, parent_location=parent_location
                    )

                    try:
                        future = checksum.get_future()

                        while True:
                            if self.monitor.is_paused:
                                bar.text = f"{pause_icon} PAUSED"
                                sleep(0.500)

                            if not self.monitor.is_paused:
                                bar.text = (
                                    f"{play_icon} {str_relative_location}"
                                )
                                sleep(0.500)
                                if future.done():
                                    hashes = FileImporter.get_hash(
                                        self.hash_file_location
                                    )
                                    hashes.append(
                                        HashDTO(
                                            file=str_relative_location,
                                            crc=future.result(timeout=0.00),
                                        )
                                    )
                                    FileImporter.save_hash(
                                        self.hash_file_location, hashes
                                    )
                                    bar()
                                    break

                            if self.monitor.is_quit:
                                CrcutilLogger.get_console_logger().info(
                                    f"{cancel_icon} Quitting..."
                                )
                                sys.exit(0)

                    finally:
                        checksum.shutdown()

        except KeyboardInterrupt:
            # Handle Ctrl+C
            self.monitor.stop()
        finally:
            self.monitor.stop()

    def seek(
        self,
        initial_position: Path,
        pending_crcs: list[str] | None = None,
    ) -> list[str]:
        if pending_crcs is None:
            pending_crcs = []
        raw = PathOps.walk(initial_position)
        system_files = ["desktop.ini", "Thumbs.db", ".DS_Store"]
        filtered = [x for x in raw if x.name not in system_files]
        normalized = [x.relative_to(initial_position) for x in filtered]
        sorted_normalized = sorted(normalized, key=lambda path: path.name)
        sorted_normalized = [
            os.fsdecode(x) for x in sorted_normalized if x != Path()
        ]

        if not pending_crcs:
            return sorted_normalized
        else:
            return [x for x in sorted_normalized if x in pending_crcs]

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
