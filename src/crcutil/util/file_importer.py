from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from crcutil.dto.checksum_dto import ChecksumDTO
    from crcutil.dto.crc_diff_report_dto import CrcDiffReportDTO


import ctypes.wintypes
import json
import os
import platform
from pathlib import Path

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
        return toml.load(
            FileImporter.get_project_root().parent / "pyproject.toml"
        )

    @staticmethod
    def save_checksums(
        crc_path: Path, checksum_dto: list[ChecksumDTO]
    ) -> None:
        with crc_path.open(
            "w", errors="strict", encoding=FileImporter.encoding
        ) as file:
            crc_data = ChecksumSerializer.to_json(checksum_dto)
            json.dump(crc_data, file, indent=4, ensure_ascii=False)

    @staticmethod
    def save_crc_diff_report(
        report_path: Path, crc_diff_report_dto: CrcDiffReportDTO
    ) -> None:
        with report_path.open(
            "w", errors="strict", encoding=FileImporter.encoding
        ) as file:
            crc_data = CrcDiffReportSerializer.to_json(crc_diff_report_dto)
            json.dump(crc_data, file, indent=4, ensure_ascii=False)

    @staticmethod
    def get_checksums(crc_path: Path) -> list[ChecksumDTO]:
        with crc_path.open(
            "r", errors="strict", encoding=FileImporter.encoding
        ) as file:
            return ChecksumSerializer.to_dto(json.load(file))

    @staticmethod
    def bootstrap() -> BootstrapPathsDTO:
        try:
            home_folder = Path()
            system = platform.system()

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
                home_folder = os.getenv("HOME") or ""
            else:
                description = f"Unsupported OS: {system}"
                raise OSError(description)  # noqa: TRY301

            crcutil_dir = Path(home_folder) / "crcutil"
            log_dir = crcutil_dir / "log"
            crc_file = crcutil_dir / "crc.json"
            report_file = crcutil_dir / "diff.json"

            crcutil_dir.mkdir(exist_ok=True)
            log_dir.mkdir(exist_ok=True)

            return BootstrapPathsDTO(
                log_dir=log_dir, crc_file=crc_file, report_file=report_file
            )

        except Exception as e:
            if platform.system == "Windows":
                win32evtlogutil.ReportEvent(  # pyright: ignore # noqa: PGH003
                    "plexutil",
                    eventID=1,
                    eventType=win32evtlog.EVENTLOG_ERROR_TYPE,  # pyright: ignore # noqa: PGH003
                    strings=[""],
                )
            if e.args and len(e.args) >= 0:
                raise BootstrapError(e.args[0]) from e

            raise BootstrapError from e
