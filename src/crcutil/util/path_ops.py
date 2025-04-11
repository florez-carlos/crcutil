from __future__ import annotations

import errno
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

from crcutil.util.crcutil_logger import CrcutilLogger
from crcutil.util.static import Static

WIN_PERMISSION_ERROR = 5


class PathOps(Static):
    WARNING = (
        "⚠️ " if sys.stdout.encoding.lower().startswith("utf") else "[WARNING]"
    )

    @staticmethod
    def walk(path: Path, supress_warnings: bool = False) -> list[Path]:
        """
        Recursively collects all file/dirs in a given path
        Logs a Console Warning for every path it cannot open

        Args:
            path (pathlib.Path): The parent directory to traverse
            supress_warnings (bool): Supress Console Warnings

        Returns:
            [Path] All file/dir in the tree
        """

        description = (
            f"{PathOps.WARNING} Lack permissions to evaluate: {path!s}"
        )
        items = []
        try:
            if path.is_file():
                items.append(path)
            elif path.is_dir():
                items.append(path)
                for child in path.iterdir():
                    sub_items = PathOps.walk(child)
                    items.extend(sub_items)

        except PermissionError:
            if not supress_warnings:
                CrcutilLogger.get_console_logger().warning(description)
        except OSError as e:
            if (
                hasattr(e, "winerror") and e.winerror == WIN_PERMISSION_ERROR  # pyright: ignore [reportAttributeAccessIssue]
            ):
                if not supress_warnings:
                    CrcutilLogger.get_console_logger().warning(description)
                debug = "Windows Permission Denied"
                CrcutilLogger.get_logger().debug(debug)
            elif e.errno in (errno.EACCES, errno.EPERM):
                if not supress_warnings:
                    CrcutilLogger.get_console_logger().warning(description)
                debug = "POSIX permission denied"
                CrcutilLogger.get_logger().debug(debug)
            else:
                description = (
                    f"{PathOps.WARNING} Unexpected error, "
                    f"can't evaluate: {path!s}"
                )
                if not supress_warnings:
                    CrcutilLogger.get_console_logger().warning(description)
                debug = f"Unexpected OS Error: {e}"
                CrcutilLogger.get_logger().debug(debug)
        return items
