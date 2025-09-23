import concurrent.futures
import zlib
from collections.abc import Callable
from pathlib import Path


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
        self.executor.shutdown(wait=False)

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
        checksum = (
            zlib.crc32(self.__get_checksum_from_attr(self.location), checksum)
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
        return str(location.relative_to(root_location)).encode("utf-8")

    def __get_checksum_from_attr(self, location: Path) -> bytes:
        """
        Helper method to __get_checksum().

        Args:
            location (pathlib.Path): The path to evaluate

        Returns:
            bytes: of the str representation
            of st_mode (file type/permission)
            and additionally st_size if file is NOT a dir.

            Example:
            - location: a.py (file)
            Returns -> b'111:111'
        """
        stat = location.stat()
        if location.is_dir():
            return f"{stat.st_mode}".encode()
        else:
            return f"{stat.st_size}:{stat.st_mode}".encode()

    def __get_checksum_from_file_contents(self, location: Path) -> bytes:
        """
        Helper method to __get_checksum()
        Returns bytes from the str representation
        of the file's CRC32 checksum.

        The checksum is calculated by reading the file in 4KB chunks
        and updating the CRC32 value incrementally. The result is
        masked to ensure it's treated as an unsigned 32-bit integer.

        Args:
            location (pathlib.Path): The path to evaluate

        Returns:
            bytes: 4-byte little-endian representation of the CRC32 checksum
        """
        file_checksum = 0
        with location.open("rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                file_checksum = zlib.crc32(chunk, file_checksum) & 0xFFFFFFFF
        return file_checksum.to_bytes(4, "little", signed=False)
