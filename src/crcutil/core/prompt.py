from __future__ import annotations

import argparse
import pathlib
import sys
from argparse import RawTextHelpFormatter
from importlib.metadata import PackageNotFoundError, version

from crcutil.dto.user_instructions_dto import UserInstructionsDTO
from crcutil.enums.user_request import UserRequest
from crcutil.exception.unexpected_argument_error import (
    UnexpectedArgumentError,
)
from crcutil.exception.user_error import UserError
from crcutil.util.crcutil_logger import CrcutilLogger
from crcutil.util.file_importer import FileImporter
from crcutil.util.static import Static


class Prompt(Static):
    @staticmethod
    def get_user_instructions_dto() -> UserInstructionsDTO:
        parser = argparse.ArgumentParser(
            description="crcutil", formatter_class=RawTextHelpFormatter
        )

        request_help_str = "Supported Requests: \n"

        for request in list(UserRequest):
            request_help_str += "-> " + request.value + "\n"

        parser.add_argument(
            "request",
            metavar="Request",
            type=str,
            nargs="?",
            help=request_help_str,
        )

        parser.add_argument(
            "-l",
            "--location",
            metavar="location",
            type=pathlib.Path,
            nargs="+",
            help=("Path to "),
            default=None,
        )

        parser.add_argument(
            "-hl",
            "--hash_location",
            metavar="hash_location",
            type=pathlib.Path,
            nargs="+",
            help=("Path to the Save Manifest file"),
            default=None,
        )

        parser.add_argument(
            "-v",
            "--version",
            action="store_true",
            help=("Displays version"),
        )

        args, unknown = parser.parse_known_args()

        if unknown:
            raise UnexpectedArgumentError(unknown)

        request = args.request
        save_manifest = args.save_manifest
        is_version = args.version

        if is_version:
            crcutil_version = ""

            try:
                crcutil_version = version("crcutil")

            except PackageNotFoundError:
                pyproject = FileImporter.get_pyproject()
                crcutil_version = pyproject["project"]["version"]

            CrcutilLogger.get_logger().info(crcutil_version)
            sys.exit(0)

        if not request:
            description = "Expected a request but none supplied, see -h"
            raise UserError(description)
        if not save_manifest:
            description = "Expected a save_manifest but none supplied, see -h"
            raise UserError(description)

        request = UserRequest.get_user_request_from_str(request)
        save_manifest = save_manifest[0]

        if request is UserRequest.INJECT:
            warning = (
                "⚠️"
                if sys.stdout.encoding.lower().startswith("utf")
                else "[WARNING]"
            )
            confirmation = (
                input(
                    f"{warning} Injection will overwrite hot saves with cold, "
                    "continue? (y/n): "
                )
                .strip()
                .lower()
            )
            if confirmation != "y":
                debug = "Injection cancelled by user"
                CrcutilLogger.get_logger().debug(debug)
                sys.exit(0)

        debug = (
            "Received a User Request:\n"
            f"Request: {request.value if request else None}\n"
            f"Save Manifest: {save_manifest!s}\n"
        )
        CrcutilLogger.get_logger().debug(debug)

        return UserInstructionsDTO(request=request, location=pathlib.Path())

    # TODO:
    @staticmethod
    def overwrite_hash_confirm() -> None:
        pass
