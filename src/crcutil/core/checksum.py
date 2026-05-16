import codecs
import concurrent.futures
import zlib
from collections.abc import Callable
from pathlib import Path
from typing import ClassVar

from crcutil.util.crcutil_logger import CrcutilLogger


class Checksum:
    CHUNK_SIZE = 4096 * 1024

    TEXT_EXTENSIONS: ClassVar[set[str]] = {
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
        checksum = self.__get_checksum_from_path(
            self.location, self.root_location
        )

        if self.location.is_file():
            checksum = self.__get_checksum_from_file_contents(
                self.location, checksum
            )
        return checksum

    def __get_checksum_from_path(
        self, location: Path, root_location: Path
    ) -> int:
        """
        Helper method to __get_checksum().

        Args:
            location (pathlib.Path): The path to evaluate
            root_location (pathlib.Path): The root path of location

        Returns:
            int: CRC32 checksum from the str representation of location
                   relative to the root location.

            Example:
            - root_location: a
            - location: a/b/c
            Returns -> checksum from b'b/c'
        """
        return (
            zlib.crc32(
                str(location.relative_to(root_location).as_posix()).encode(
                    "utf-8"
                )
            )
            & 0xFFFFFFFF
        )

    def __get_checksum_from_file_contents(
        self, location: Path, initial: int = 0
    ) -> int:
        """
        Helper method to __get_checksum()
        Returns bytes from the str representation
        of the file's CRC32 checksum.

        The checksum is calculated by reading the file
        and updating the CRC32 value incrementally. The result is
        masked to ensure it's treated as an unsigned 32-bit integer.

        Text files with dos line endings are normalized to unix

        Args:
            location (pathlib.Path): The path to evaluate

        Returns:
            int: CRC32 checksum
        """
        file_checksum = initial
        with location.open("rb") as f:
            sample = f.read(8192)
            is_text = self.__is_likely_text_file(
                sample, location.suffix.lower()
            )

            if is_text:
                try:
                    f.seek(0)
                    decoder = codecs.getincrementaldecoder("utf-8")()
                    leftover = b""

                    for chunk in iter(lambda: f.read(self.CHUNK_SIZE), b""):
                        data = leftover + chunk
                        leftover = data[-1:]
                        data = data[:-1]
                        text = decoder.decode(data)
                        text = text.replace("\r\n", "\n")
                        file_checksum = (
                            zlib.crc32(text.encode("utf-8"), file_checksum)
                            & 0xFFFFFFFF
                        )

                    tail = decoder.decode(leftover, final=True)
                    tail = tail.replace("\r\n", "\n")
                    return (
                        zlib.crc32(tail.encode("utf-8"), file_checksum)
                        & 0xFFFFFFFF
                    )

                except UnicodeDecodeError:
                    description = (
                        f"Understood as text file: {location!s} "
                        "but encountered decoding error. Proceeding w/ binary"
                    )
                    CrcutilLogger.get_logger().debug(description)
                    file_checksum = initial
                    f.seek(0)
            else:
                f.seek(0)

            for chunk in iter(lambda: f.read(self.CHUNK_SIZE), b""):
                file_checksum = zlib.crc32(chunk, file_checksum) & 0xFFFFFFFF

            return file_checksum

    def __is_likely_text_file(self, sample: bytes, extension: str) -> bool:
        """
        Check if a file is likely to be text by sampling the beginning.
        """
        # Empty file, treat as empty text
        # Does not enter here if file not in text_extensions
        if not sample and extension in self.TEXT_EXTENSIONS:
            return True

        # Null byte presence, likely a binary file
        if b"\0" in sample and extension not in self.TEXT_EXTENSIONS:
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
        printable_character_threshold = 0.8
        if printable_count <= 0:
            return False
        return (printable_count / len(sample)) > printable_character_threshold
