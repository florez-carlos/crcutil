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

EXPECTED_LOCATION_LENGHT_HASH = 1
EXPECTED_LOCATION_LENGHT_DIFF = 2


class Prompt(Static):
    WARNING = (
        "⚠️ " if sys.stdout.encoding.lower().startswith("utf") else "[WARNING]"
    )

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
            nargs="*",
            help=(
                "Path to hash, or if requesting diff, "
                "then path of both hash files to diff"
            ),
            default=[],
        )

        parser.add_argument(
            "-o",
            "--output",
            metavar="output",
            type=pathlib.Path,
            nargs="?",
            help=(
                "Path to store the hash or diff file"
                "if none specified, then it's saved at the default location"
            ),
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

        request = args.request
        if not request:
            description = "Expected a request but none supplied, see -h"
            raise UserError(description)
        request = UserRequest.get_user_request_from_str(request)

        location = args.location
        location_1 = pathlib.Path()
        location_2 = pathlib.Path()
        hash_diff_files = []
        if args.location:
            if (
                len(args.location) == EXPECTED_LOCATION_LENGHT_HASH
                and request is UserRequest.HASH
            ):
                location_1 = FileImporter.get_path_from_str(
                    args.location[0]
                ).resolve()
            elif (
                len(args.location) == EXPECTED_LOCATION_LENGHT_DIFF
                and request is UserRequest.DIFF
            ):
                location_1 = FileImporter.get_path_from_str(
                    args.location[0]
                ).resolve()
                location_2 = FileImporter.get_path_from_str(
                    args.location[1]
                ).resolve()
                hash_diff_files = [location_1, location_2]
            elif (
                len(args.location) != EXPECTED_LOCATION_LENGHT_DIFF
                and request is UserRequest.DIFF
            ):
                description = (
                    f"Expected 2 Hash files but got: "
                    f"{len(args.location)}\n"
                    f"Example: crcutil diff -l path_to_hash_1 path_to_hash_2"
                )
                raise UserError(description)
        elif not args.location and request is UserRequest.DIFF:
            description = (
                "Expected 2 Hash files but got: 0\n"
                "Example: crcutil diff -l path_to_hash_1 path_to_hash_2"
            )
            raise UserError(description)
        else:
            description = (
                "Expected a location but none supplied\n"
                "Example: crcutil hash -l path_to_hash"
            )
            raise UserError(description)

        output = args.output

        if output:
            output = args.output.resolve()
            if output.is_dir():
                if request is UserRequest.HASH:
                    output = output / "hash.json"
                elif request is UserRequest.DIFF:
                    output = output / "diff.json"
                else:
                    description = (
                        "Specified an output but "
                        f"request is not supported: {request.value}"
                    )
                    raise UserError(description)

        debug = (
            "Received a User Request:\n"
            f"Request: {request.value if request else None}\n"
            f"Location: {location!s}\n"
            f"Output: {output!s}\n"
        )
        CrcutilLogger.get_logger().debug(debug)

        return UserInstructionsDTO(
            request=request,
            location=location_1,
            hash_diff_files=hash_diff_files,
            output=output,
        )

    @staticmethod
    def overwrite_hash_confirm() -> None:
        confirmation = (
            input(
                f"{Prompt.WARNING} Hash file already exists, "
                "OVERWRITE? (y/n): "
            )
            .strip()
            .lower()
        )
        if confirmation != "y":
            debug = "Overwrite of hash file cancelled by user"
            CrcutilLogger.get_logger().debug(debug)
            sys.exit(0)

    @staticmethod
    def continue_hash_confirm() -> bool:
        confirmation = (
            input(
                f"{Prompt.WARNING} Incomplete Hash file already exists, "
                "RESUME? (y/n): "
            )
            .strip()
            .lower()
        )
        if confirmation != "y":
            debug = "Resume of hash file cancelled by user"
            CrcutilLogger.get_logger().debug(debug)
            return False
        else:
            return True
