import concurrent.futures
import zlib
from collections.abc import Callable
from pathlib import Path

from crcutil.util.crcutil_logger import CrcutilLogger

CHUNK_SIZE = 4096 * 1024


class Checksum:
    def __init__(self, location: Path, root_location: Path) -> None:
        self.location = location
        self.root_location = root_location
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        self.future = None

    def get_future(
        self, callback: Callable | None = None
    ) -> concurrent.futures.Future:
        """
        This is the only public method
        Returns a Future that contains a Checksum (int)

        Args:
            callback (Callable): Callable to be injected to the Future

        Returns:
            A concurrent.futures.Future that holds a Checksum (int)
        """
        if not self.future:
            self.future = self.executor.submit(self.__get_checksum)

        if callback:
            self.future.add_done_callback(lambda f: callback(f.result()))

        return self.future

    def shutdown(self) -> None:
        self.executor.shutdown(wait=False, cancel_futures=True)

    def __get_checksum(self) -> int:
        """
        Generates a checksum

        Returns:
            Checksum calculated from the attributes of self.location.
        """
        checksum = 0
        checksum = (
            zlib.crc32(
                self.__get_checksum_from_path(
                    self.location, self.root_location
                ),
                checksum,
            )
            & 0xFFFFFFFF
        )

        if self.location.is_file():
            checksum = (
                zlib.crc32(
                    self.__get_checksum_from_file_contents(self.location),
                    checksum,
                )
                & 0xFFFFFFFF
            )

        return checksum

    def __get_checksum_from_path(
        self, location: Path, root_location: Path
    ) -> bytes:
        """
        Helper method to __get_checksum().

        Args:
            location (pathlib.Path): The path to evaluate
            root_location (pathlib.Path): The root path of location

        Returns:
            bytes: str representation of location
                   relative to the root location.

            Example:
            - root_location: a
            - location: a/b/c
            Returns -> b'b/c'
        """
        return str(location.relative_to(root_location).as_posix()).encode(
            "utf-8"
        )

    def __get_checksum_from_file_contents(self, location: Path) -> bytes:
        """
        Helper method to __get_checksum()
        Returns bytes from the str representation
        of the file's CRC32 checksum.

        The checksum is calculated by reading the file in 4KB chunks
        and updating the CRC32 value incrementally. The result is
        masked to ensure it's treated as an unsigned 32-bit integer.

        Text files with dos line endings are normalized to unix

        Args:
            location (pathlib.Path): The path to evaluate

        Returns:
            bytes: 4-byte little-endian representation of the CRC32 checksum
        """
        file_checksum = 0
        is_text_file = self.__is_likely_text_file(location)

        if is_text_file:
            try:
                with location.open("r", encoding="utf-8") as f:
                    content = f.read().replace("\r\n", "\n")
                content_bytes = content.encode("utf-8")
                file_checksum = zlib.crc32(content_bytes) & 0xFFFFFFFF
                return file_checksum.to_bytes(4, "little", signed=False)
            except UnicodeDecodeError:
                description = (
                    f"Understood as text file: {location!s} "
                    "but encountered decoding error. Proceeding w/ binary"
                )
                CrcutilLogger.get_logger().debug(description)

        with location.open("rb") as f:
            for chunk in iter(lambda: f.read(CHUNK_SIZE), b""):
                file_checksum = zlib.crc32(chunk, file_checksum) & 0xFFFFFFFF

        return file_checksum.to_bytes(4, "little", signed=False)

    def __is_likely_text_file(self, location: Path) -> bool:
        """
        Check if a file is likely to be text by sampling the beginning.
        """
        # Known text extensions to consider for line ending normalization
        text_extensions = {
            ".txt",
            ".md",
            ".rst",
            ".html",
            ".htm",
            ".xml",
            ".json",
            ".yaml",
            ".yml",
            ".csv",
            ".tsv",
            ".ini",
            ".cfg",
            ".conf",
            ".py",
            ".js",
            ".java",
            ".c",
            ".cpp",
            ".h",
            ".hpp",
            ".php",
            ".rb",
            ".go",
            ".rs",
            ".ts",
            ".css",
            ".scss",
            ".sql",
            ".sh",
            ".bash",
            ".zsh",
            ".ps1",
            ".bat",
            ".cmd",
            ".log",
        }
        extension = location.suffix.lower()
        # Only read a sample
        with location.open("rb") as f:
            sample = f.read(8192)

        # Empty file, treat as empty text
        if not sample and extension in text_extensions:
            return True

        # Null byte presence, likely a binary file
        if b"\0" in sample and extension not in text_extensions:
            return False

        ascii_lower_range = 32
        ascii_upper_range = 126
        tab = 9
        line_feed = 10
        carriage_return = 13
        printable_count = sum(
            1
            for byte in sample
            if ascii_lower_range <= byte <= ascii_upper_range
            or byte in (tab, line_feed, carriage_return)
        )
        printable_character_treshold = 0.8
        return (printable_count / len(sample)) > printable_character_treshold
