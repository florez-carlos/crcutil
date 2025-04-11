from __future__ import annotations

import errno
import os
import sys
import threading
import time
import zlib
from pathlib import Path

from alive_progress import alive_bar

from crcutil.core.prompt import Prompt
from crcutil.dto.hash_diff_report_dto import HashDiffReportDTO
from crcutil.dto.hash_dto import HashDTO
from crcutil.enums.user_request import UserRequest
from crcutil.exception.corrupt_hash_error import CorruptHashError
from crcutil.util.crcutil_logger import CrcutilLogger
from crcutil.util.file_importer import FileImporter
from crcutil.util.keyboard_monitor import KeyboardMonitor

WIN_PERMISSION_ERROR = 5


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
        self.crc_thread = None
        self.crc_thread_stop = threading.Event()

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

            # Shared data between threads
            results_queue = []  # List to store calculated CRCs
            lock = threading.Lock()  # Lock for thread safety
            current_file = {"name": ""}  # Current file being processed

            # Reset the stop event
            self.crc_thread_stop = threading.Event()

            # Start the CRC worker thread
            self.crc_thread = threading.Thread(
                target=self.__crc_worker,
                args=(
                    parent_location,
                    str_relative_locations,
                    results_queue,
                    lock,
                    current_file,
                ),
            )
            self.crc_thread.daemon = True
            self.crc_thread.start()

            with alive_bar(length, dual_line=True) as bar:
                if total_count:
                    offset_count = total_count - len(str_relative_locations)
                    for _ in range(offset_count):
                        bar()

                # Track processed files
                processed_files = set()

                # Main loop
                # Process results as they come in while monitoring keyboard
                while len(processed_files) < len(str_relative_locations):
                    # Check keyboard state
                    if monitor.get_quit_status():
                        self.crc_thread_stop.set()
                        if self.crc_thread.is_alive():
                            self.crc_thread.join(timeout=1.0)
                        sys.exit(0)

                    # Handle pause state
                    if monitor.get_pause_status():
                        self.crc_thread_stop.set()
                        bar.text = f"{pause_icon} PAUSED"
                    else:
                        # If previously paused and thread is stopped, restart
                        if (
                            self.crc_thread_stop.is_set()
                            and not self.crc_thread.is_alive()
                        ):
                            # Clear the stop event
                            self.crc_thread_stop.clear()

                            # Start new CRC worker thread with remaining files
                            remaining_files = [
                                loc
                                for loc in str_relative_locations
                                if loc not in processed_files
                            ]
                            self.crc_thread = threading.Thread(
                                target=self.__crc_worker,
                                args=(
                                    parent_location,
                                    remaining_files,
                                    results_queue,
                                    lock,
                                    current_file,
                                ),
                            )
                            self.crc_thread.daemon = True
                            self.crc_thread.start()

                        # Show current file being processed
                        with lock:
                            current = current_file["name"]
                        if current:
                            bar.text = f"{play_icon} {current}"

                    # Only process results if NOT paused
                    if not monitor.get_pause_status():
                        # Check for completed CRC calculations
                        completed_results = []
                        with lock:
                            if results_queue:
                                completed_results = results_queue.copy()
                                results_queue.clear()

                        # Process completed results
                        for str_relative_location, crc in completed_results:
                            if str_relative_location not in processed_files:
                                # Update hash file
                                hashes = FileImporter.get_hash(
                                    self.hash_file_location
                                )
                                hashes.append(
                                    HashDTO(
                                        file=str_relative_location, crc=crc
                                    )
                                )
                                FileImporter.save_hash(
                                    self.hash_file_location, hashes
                                )

                                # Update progress
                                processed_files.add(str_relative_location)
                                bar()

                    # Short sleep to avoid CPU spinning
                    time.sleep(0.05)

                # Wait for the CRC thread to finish if it hasn't already
                self.crc_thread_stop.set()
                if self.crc_thread.is_alive():
                    self.crc_thread.join(timeout=1.0)

        except KeyboardInterrupt:
            # Handle Ctrl+C
            self.crc_thread_stop.set()
            if self.crc_thread and self.crc_thread.is_alive():
                self.crc_thread.join(timeout=1.0)
            monitor.stop()
        finally:
            # Ensure cleanup
            monitor.stop()
            self.crc_thread_stop.set()
            if self.crc_thread and self.crc_thread.is_alive():
                self.crc_thread.join(timeout=1.0)

    def __walk(self, path: Path) -> list[Path]:
        """
        Recursively collects all file/dirs in a given path
        Logs a Console Warning for every path it cannot open

        Args:
            path (pathlib.Path): The parent directory to traverse

        Returns:
            [Path] All file/dir in the tree
        """

        description = (
            f"{Prompt.WARNING} Lack permissions to evaluate: {path!s}"
        )
        items = []
        try:
            if path.is_file():
                items.append(path)
            elif path.is_dir():
                items.append(path)
                for child in path.iterdir():
                    sub_items = self.__walk(child)
                    items.extend(sub_items)

        except PermissionError:
            CrcutilLogger.get_console_logger().warning(description)
        except OSError as e:
            if (
                hasattr(e, "winerror") and e.winerror == WIN_PERMISSION_ERROR  # pyright: ignore [reportAttributeAccessIssue]
            ):
                CrcutilLogger.get_console_logger().warning(description)
                debug = "Windows Permission Denied"
                CrcutilLogger.get_logger().debug(debug)
            elif e.errno in (errno.EACCES, errno.EPERM):
                CrcutilLogger.get_console_logger().warning(description)
                debug = "POSIX permission denied"
                CrcutilLogger.get_logger().debug(debug)
            else:
                description = (
                    f"{Prompt.WARNING} Unexpected error, "
                    f"can't evaluate: {path!s}"
                )
                CrcutilLogger.get_console_logger().warning(description)
                debug = f"Unexpected OS Error: {e}"
                CrcutilLogger.get_logger().debug(debug)
        return items

    def seek(
        self,
        initial_position: Path,
        pending_crcs: list[str] | None = None,
    ) -> list[str]:
        if pending_crcs is None:
            pending_crcs = []
        raw = self.__walk(initial_position)
        normalized = [x.relative_to(initial_position) for x in raw]
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

    def __crc_worker(
        self,
        parent_location: Path,
        str_relative_locations: list[str],
        results_queue: list,
        lock: threading.Lock,
        current_file: dict,
    ) -> None:
        """Worker function that runs in a separate thread to calculate CRCs"""
        try:
            for str_relative_location in str_relative_locations:
                # Check if we should stop
                if self.crc_thread_stop.is_set():
                    return

                # Update the current file being processed
                with lock:
                    current_file["name"] = str_relative_location

                # Calculate CRC
                relative_location = Path(str_relative_location)
                abs_location = (parent_location / relative_location).resolve()
                crc = self.__get_crc_hash(abs_location, parent_location)
                time.sleep(6)

                # Add the result to the queue
                with lock:
                    results_queue.append((str_relative_location, crc))

        except Exception as e:  # noqa: BLE001
            CrcutilLogger.get_logger().error(f"Error in CRC thread: {e}")

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
