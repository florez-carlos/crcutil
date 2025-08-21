import concurrent.futures
import zlib
from collections.abc import Callable
from pathlib import Path


class Checksum:
    def __init__(self, location: Path, parent_location: Path) -> None:
        self.location = location
        self.parent_location = parent_location
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        self.future = None

    def get_future(
        self, callback: Callable | None = None
    ) -> concurrent.futures.Future:
        if not self.future:
            self.future = self.executor.submit(self.__get_checksum)

        if callback:
            self.future.add_done_callback(lambda f: callback(f.result()))

        return self.future

    def shutdown(self) -> None:
        self.executor.shutdown(wait=False)

    def __get_checksum(self) -> int:
        checksum = 0
        checksum = (
            zlib.crc32(
                self.__get_checksum_from_path(
                    self.location, self.parent_location
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
        self, location: Path, parent_location: Path
    ) -> bytes:
        return str(location.relative_to(parent_location)).encode("utf-8")

    def __get_checksum_from_attr(self, location: Path) -> bytes:
        stat = location.stat()
        if location.is_dir():
            return f"{stat.st_mode}".encode()
        else:
            return f"{stat.st_size}:{stat.st_mode}".encode()

    def __get_checksum_from_file_contents(self, location: Path) -> bytes:
        file_checksum = 0
        with location.open("rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                file_checksum = zlib.crc32(chunk, file_checksum) & 0xFFFFFFFF
        return file_checksum.to_bytes(4, "little", signed=False)
