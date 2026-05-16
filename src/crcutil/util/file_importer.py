from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from crcutil.dto.checksum_dto import ChecksumDTO
    from crcutil.dto.crc_diff_report_dto import CrcDiffReportDTO


import ctypes.wintypes
import platform
from datetime import UTC, datetime, timedelta
from pathlib import Path

import msgspec
import toml

from crcutil.dto.bootstrap_paths_dto import BootstrapPathsDTO
from crcutil.exception.bootstrap_error import BootstrapError
from crcutil.serializer.checksum_serializer import ChecksumSerializer
from crcutil.serializer.crc_diff_report_serializer import (
    CrcDiffReportSerializer,
)

if platform.system() == "Windows":
    import win32evtlog  # pyright: ignore # noqa: PGH003
    import win32evtlogutil  # pyright: ignore # noqa: PGH003

import yaml

from crcutil.util.static import Static


class FileImporter(Static):
    JSON_ENCODER = msgspec.json.Encoder()
    JSON_DECODER = msgspec.json.Decoder(dict[str, str])
    encoding = "utf-8"

    @staticmethod
    def get_path_from_str(
        path_candidate: str,
        is_dir_expected: bool = False,
        is_file_expected: bool = False,
    ) -> Path:
        """
        Get pathlib.Path from a str

        Args:
            path_candidate (str): The likely Path
            is_dir_expected (bool): Is the path expected to be a dir?
            is_file_expected (bool): Is the path expected to be a file?

        Returns:
            A pathlib.Path

        Raises:
            ValueError: If path_candidate is not supplied or path doesn't exist
            or path does not meet is_dir_expected/is_file_expected condition
        """
        if not path_candidate:
            description = "Expected a path candidate but none supplied "
            raise ValueError(description)

        path = Path(path_candidate)

        if not path.exists():
            description = f"Path candidate ({path_candidate}) does not exist"
            raise ValueError(description)

        if is_dir_expected and not path.is_dir():
            description = (
                f"Expected a dir for ({path_candidate}) but this is not a dir"
            )
            raise ValueError(description)

        if is_file_expected and not path.is_file():
            description = (
                f"Expected a file for ({path_candidate}) but path not a file"
                f"candidate is not a file {path_candidate}"
            )
            raise ValueError(description)

        return path

    @staticmethod
    def get_logging_config(logging_config_path: Path) -> dict:
        with logging_config_path.open(
            "r", errors="strict", encoding=FileImporter.encoding
        ) as file:
            return yaml.safe_load(file)

    @staticmethod
    def get_project_root() -> Path:
        """
        Gets the root of this project

        Returns:
            pathlib.Path: The project's root
        """
        return Path(__file__).parent.parent.parent

    @staticmethod
    def get_pyproject() -> dict:
        """
        Gets the project's pyproject.toml file

        Returns:
            pathlib.Path: The project's pyproject.toml file
        """
        return toml.load(
            FileImporter.get_project_root().parent / "pyproject.toml"
        )

    @staticmethod
    def get_project_version() -> str:
        """
        Gets the project's semantic version
        or *UNKNOWN VERSION* if failure to determine

        Returns:
            str: The project's semantic version
        """
        try:
            crcutil_version = version("crcutil")

        except PackageNotFoundError:
            pyproject = FileImporter.get_pyproject()
            crcutil_version = (
                pyproject["project"]["version"] or "*UNKNOWN VERSION*"
            )

        return crcutil_version

    @staticmethod
    def stage_checksums(
        crc_path: Path, checksum_dto: list[ChecksumDTO]
    ) -> None:
        """
        Saves the provided checksums to a CRC file

        Args:
            crc_path (pathlib.Path): CRC file to save checksums to
            checksum_dto (list[ChecksumDTO]): The checksums to save

        Returns:
            None: This method does not return a value.
        """
        with crc_path.open("wb") as file:
            crc_data = ChecksumSerializer.to_json(checksum_dto)
            encoded = msgspec.json.format(
                FileImporter.JSON_ENCODER.encode(crc_data), indent=4
            )
            file.write(encoded)

    @staticmethod
    def get_checksum_offset(crc_path: Path) -> dict[str, int]:
        """
        Returns a dict of Paths and the position of their
        corresponding checksum in the crc file

        Args:
            crc_path (pathlib.Path): The crc file

        Returns:
            dict[str, int]: path and position of the checksum in the crc file
        """

        offset: dict[str, int] = {}

        with crc_path.open("rb") as file:
            # Tracks the byte offset of the start of the current line
            pos = 0

            # Read one line at a time.
            # The walrus operator (:=) assigns and checks in one step
            while line := file.readline():
                # Removes leading/trailing whitespace,
                # newline and trailing comma
                stripped = line.strip().rstrip(b",")

                # Skip lines that aren't key-value pairs (e.g. {, })
                # pos is updated before skipping
                # to stay accurate for the next line
                if b'": ' not in stripped:
                    pos = file.tell()
                    continue

                # Find the byte index of ":  within the stripped line
                # This lands on the closing " of the key
                # — e.g. for "file1": "0000000000",
                # sep_idx points at the " after file1
                sep = b'": '
                sep_idx = stripped.index(sep)

                # Slice out just the key.
                # stripped[:sep_idx] would be "file1 (missing closing quote)
                # +1 includes that closing ", giving us "file1"
                path_bytes = stripped[: sep_idx + 1]

                try:
                    path = msgspec.json.decode(path_bytes.strip())
                except msgspec.DecodeError:
                    pos = file.tell()
                    continue

                # Find where the value "0000000000" starts within the raw line
                # Value begins after the key + `: "`
                value_start_in_line = line.index(b'": ') + len(b'": "')
                idx = pos + value_start_in_line

                pos = file.tell()
                offset[path] = idx

        return offset

    @staticmethod
    def save_crc_diff_report(
        report_path: Path, crc_diff_report_dto: CrcDiffReportDTO
    ) -> None:
        """
        Saves a CRC diff file

        Args:
            report_path (pathlib.Path): diff file
            crc_diff_report_dto (list[CrcDiffReportDTO]): diff report

        Returns:
            None: This method does not return a value.
        """
        with report_path.open("wb") as file:
            crc_data = CrcDiffReportSerializer.to_json(crc_diff_report_dto)
            encoded = msgspec.json.format(
                FileImporter.JSON_ENCODER.encode(crc_data), indent=4
            )
            file.write(encoded)

    @staticmethod
    def get_checksums(crc_path: Path) -> list[ChecksumDTO]:
        """
        Loads checksums from a CRC file

        Args:
            crc_path (pathlib.Path): CRC file to load checksums from

        Returns:
            list[ChecksumDTO]: Checksums loaded from the CRC file
        """
        with crc_path.open("rb") as file:
            data = FileImporter.JSON_DECODER.decode(file.read())
            return ChecksumSerializer.to_dto(data)

    @staticmethod
    def bootstrap() -> BootstrapPathsDTO:
        """
        Initializes the config/logging module
        Logs any errors to syslog

        Returns:
            BootstrapPathsDTO: Contains config/logging paths

        Raises:
            BootstrapError: If unable to setup config/logging module
            OSError: If OS other than Windows/Linux detected
        """
        system = platform.system()
        home_folder = Path()
        try:
            if system == "Windows":
                csidl_personal = 5
                shgfp_type_current = 0

                buf = ctypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH)
                ctypes.windll.shell32.SHGetFolderPathW(  # pyright: ignore # noqa: PGH003
                    None, csidl_personal, None, shgfp_type_current, buf
                )
                home_folder = buf.value or ""
                if not home_folder:
                    description = "Could not locate Documents folder"
                    raise FileNotFoundError(description)  # noqa: TRY301
            elif system == "Linux":
                home_folder = Path.home() / ".local/state"
            elif system == "Darwin":
                home_folder = Path.home() / "Library/Application Support"
            else:
                description = f"Unsupported OS: {system}"
                raise OSError(description)  # noqa: TRY301

            crcutil_dir = Path(home_folder) / "crcutil"
            log_dir = crcutil_dir / "log"
            crc_file = Path().cwd() / "crc.json"
            report_file = Path().cwd() / "diff.json"

            if crc_file.exists():
                crc_file = Path().cwd() / "crc2.json"

            log_config_file = (
                FileImporter.get_project_root()
                / "crcutil"
                / "config"
                / "log_config.yaml"
            )

            crcutil_dir.mkdir(exist_ok=True)
            log_dir.mkdir(exist_ok=True)

            # Delete logs older than 30 days
            for log_file in log_dir.iterdir():
                if not log_file.is_file():
                    continue

                log_date = datetime.fromtimestamp(
                    log_file.stat().st_ctime, tz=UTC
                )

                log_limit_date = datetime.now(tz=UTC) - timedelta(days=30)

                if log_date > log_limit_date:
                    log_file.unlink()

            return BootstrapPathsDTO(
                log_dir=log_dir,
                log_config_file=log_config_file,
                crc_file=crc_file,
                report_file=report_file,
            )

        except Exception as e:
            description = e.args[0] if e.args and len(e.args) >= 0 else ""
            if system == "Windows":
                win32evtlogutil.ReportEvent(  # pyright: ignore # noqa: PGH003
                    "plexutil",
                    eventID=1,
                    eventType=win32evtlog.EVENTLOG_ERROR_TYPE,  # pyright: ignore # noqa: PGH003
                    strings=[description],
                )
            elif system == "Linux":
                import syslog  # noqa: PLC0415

                syslog.syslog(syslog.LOG_ERR, f"[CRCUTIL]: {description}")

            if e.args and len(e.args) >= 0:
                raise BootstrapError(e.args[0]) from e
            else:
                description = "Unknown initialization error"
                raise BootstrapError(description) from e
