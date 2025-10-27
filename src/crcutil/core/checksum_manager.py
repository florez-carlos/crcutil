from __future__ import annotations

import os
import sys
from pathlib import Path
from time import sleep

from alive_progress import alive_bar

from crcutil.core.checksum import Checksum
from crcutil.core.keyboard_monitor_factory import KeyboardMonitorFactory
from crcutil.core.prompt import Prompt
from crcutil.dto.checksum_dto import ChecksumDTO
from crcutil.dto.crc_diff_report_dto import CrcDiffReportDTO
from crcutil.enums.user_request import UserRequest
from crcutil.exception.corrupt_crc_error import CorruptCrcError
from crcutil.exception.device_error import DeviceError
from crcutil.util.crcutil_logger import CrcutilLogger
from crcutil.util.file_importer import FileImporter
from crcutil.util.path_ops import PathOps


class ChecksumManager:
    def __init__(
        self,
        location: Path,
        crc_file_location: Path,
        user_request: UserRequest,
        checksums_diff_1: list[ChecksumDTO],
        checksums_diff_2: list[ChecksumDTO],
    ) -> None:
        self.location = location
        self.crc_file_location = crc_file_location
        self.user_request = user_request
        self.checksums_diff_1 = checksums_diff_1
        self.checksums_diff_2 = checksums_diff_2

    def do(self) -> CrcDiffReportDTO | None:
        """
        Performs a crc/Diff

        Returns:
            CrcDiffReportDTO | None: If request is Diff, None if crc
        Raises:
            ValueError: If request other than diff or crc
        """
        if self.user_request is UserRequest.CRC:
            match self.__get_crc_status():
                case -1:
                    self.__create_crc()
                case 0:
                    self.__continue_crc()
                case 1:
                    self.__create_crc(is_crc_overwrite=True)
            return None
        elif self.user_request is UserRequest.DIFF:
            checksums_1 = self.checksums_diff_1
            checksums_2 = self.checksums_diff_2

            checksums_1_dict = {
                checksum.file: checksum.crc for checksum in checksums_1
            }
            checksums_2_dict = {
                checksum.file: checksum.crc for checksum in checksums_2
            }

            changes = [
                checksum
                for checksum in checksums_2
                if checksum.file in checksums_1_dict
                and checksums_1_dict[checksum.file] != checksum.crc
            ]
            missing_1 = [
                checksum_1
                for checksum_1 in checksums_1
                if checksum_1.file not in checksums_2_dict
            ]
            missing_2 = [
                checksum_2
                for checksum_2 in checksums_2
                if checksum_2.file not in checksums_1_dict
            ]

            return CrcDiffReportDTO(
                changes=changes, missing_1=missing_1, missing_2=missing_2
            )
        else:
            description = f"Unsupported request: {self.user_request!s}"
            raise ValueError(description)

    def __create_crc(self, is_crc_overwrite: bool = False) -> None:
        if is_crc_overwrite:
            Prompt.overwrite_crc_confirm()

        self.crc_file_location.write_text("{}")

        description = f"Creating Crc: {self.location}"
        CrcutilLogger.get_logger().debug(description)

        all_locations = self.seek(self.location)
        self.__write_locations(all_locations)
        self.__write_crc(self.location, all_locations)

    def __continue_crc(self) -> None:
        if not Prompt.continue_crc_confirm():
            Prompt.overwrite_crc_confirm()
            self.__create_crc()
            return

        original_checksums = FileImporter.get_checksums(self.crc_file_location)

        description = (
            f"Resuming existing Crc: {self.crc_file_location} "
            f"with location: {self.location}"
        )
        CrcutilLogger.get_logger().debug(description)

        pending_checksums = [
            checksum_dto.file
            for checksum_dto in original_checksums
            if not checksum_dto.crc
        ]

        all_locations = self.seek(self.location)
        for checksum_dto in original_checksums:
            if checksum_dto.file not in all_locations:
                description = (
                    "An element in the Crc does not exist "
                    f"in the supplied location: {checksum_dto.file}\n"
                    f"Cannot continue"
                )
                raise CorruptCrcError(description)

        original_checksums_str = [x.file for x in original_checksums]
        for location in all_locations:
            if location not in original_checksums_str:
                description = (
                    "An element in the supplied location does not exist "
                    f"in the Crc: {location}\n"
                    f"Cannot continue"
                )
                raise CorruptCrcError(description)

        filtered_locations = self.seek(self.location, pending_checksums)
        self.__write_crc(
            self.location, filtered_locations, len(original_checksums)
        )

    def __write_locations(self, str_relative_locations: list[str]) -> None:
        checksums = [
            ChecksumDTO(file=x, crc=0) for x in str_relative_locations
        ]
        FileImporter.save_checksums(self.crc_file_location, checksums)

    def __write_crc(
        self,
        root_location: Path,
        str_relative_locations: list[str],
        total_count: int = 0,
    ) -> None:
        monitor = None
        try:
            play_icon, pause_icon, cancel_icon = (
                ("▶", "⏸", "✖")
                if sys.stdout.encoding.lower().startswith("utf")
                else (">", "||", "X")
            )

            try:
                monitor = KeyboardMonitorFactory.get()

                CrcutilLogger.get_console_logger().info(
                    monitor.get_pause_message()
                )
                CrcutilLogger.get_console_logger().info(
                    monitor.get_quit_message()
                )

                monitor.start()

            except DeviceError as e:
                description = f"Playback controls disabled: {e}"
                CrcutilLogger.get_console_logger().warning(description)

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
                        root_location / Path(str_relative_location)
                    ).resolve()

                    checksum = Checksum(
                        location=abs_location, root_location=root_location
                    )

                    try:
                        future = checksum.get_future()
                        while True:
                            sleep(0.3)

                            if monitor is not None:
                                if monitor.is_listen_quit():
                                    CrcutilLogger.get_console_logger().info(
                                        f"{cancel_icon} Quitting..."
                                    )
                                    sys.exit(0)

                                if monitor.is_listen_paused():
                                    bar.text = f"{pause_icon} PAUSED"
                                    continue

                                if not monitor.is_listen_paused():
                                    bar.text = (
                                        f"{play_icon} {str_relative_location}"
                                    )
                            else:
                                bar.text = f"{str_relative_location}"

                            if future.done():
                                checksums = FileImporter.get_checksums(
                                    self.crc_file_location
                                )
                                checksums.append(
                                    ChecksumDTO(
                                        file=str_relative_location,
                                        crc=future.result(timeout=0.00),
                                    )
                                )
                                FileImporter.save_checksums(
                                    self.crc_file_location, checksums
                                )
                                bar()
                                break

                    finally:
                        checksum.shutdown()

        finally:
            if monitor:
                monitor.stop()

    def seek(
        self,
        initial_position: Path,
        pending_checksums: list[str] | None = None,
    ) -> list[str]:
        if pending_checksums is None:
            pending_checksums = []

        paths = PathOps.walk(initial_position)

        system_files = ["desktop.ini", "Thumbs.db", ".DS_Store"]
        pending_checksums_set = set(pending_checksums)

        filtered_posix_strs = []
        for path in paths:
            if os.fsdecode(path.name) in system_files:
                continue

            relative_path = path.relative_to(initial_position)

            # Ignore the root dir (.)
            if relative_path == Path():
                continue

            posix_path = relative_path.as_posix()

            if not pending_checksums_set:
                filtered_posix_strs.append(posix_path)
                continue

            if posix_path in pending_checksums_set:
                filtered_posix_strs.append(posix_path)

        return sorted(filtered_posix_strs)

    def __get_crc_status(self) -> int:
        """
        Gets the current status of a crc file:
        Possible values:
        -1) File does not exist
         0) File exists and is incomplete/pending
         1) File exists and is finished

        Returns:
            int: The status of the crc file
        """
        status = -1
        if self.crc_file_location.exists():
            checksums_dto = FileImporter.get_checksums(self.crc_file_location)

            for dto in checksums_dto:
                if not dto.crc:
                    return 0

            status = 1

        return status
