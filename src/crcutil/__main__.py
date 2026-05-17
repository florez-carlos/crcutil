import json
import sys

from jsonschema.exceptions import ValidationError

from crcutil.core.checksum_manager import ChecksumManager
from crcutil.core.prompt import Prompt
from crcutil.exception.bootstrap_error import BootstrapError
from crcutil.exception.corrupt_crc_error import CorruptCrcError
from crcutil.exception.unexpected_argument_error import UnexpectedArgumentError
from crcutil.exception.user_error import UserError
from crcutil.util.crcutil_logger import CrcutilLogger
from crcutil.util.file_importer import FileImporter
from crcutil.util.icons import Icons


def main() -> None:
    try:
        bootstrap_paths_dto = FileImporter.bootstrap()

        log_dir = bootstrap_paths_dto.log_dir
        log_config_file_location = bootstrap_paths_dto.log_config_file
        crc_file_location = bootstrap_paths_dto.crc_file
        report_file_location = bootstrap_paths_dto.report_file

        log_config = FileImporter.get_logging_config(log_config_file_location)

        CrcutilLogger(log_dir, log_config)

        instructions_dto = Prompt.get_user_instructions_dto()
        location = instructions_dto.location
        user_request = instructions_dto.request
        is_fast = instructions_dto.is_fast
        crc_diff_files = instructions_dto.crc_diff_files
        checksums_diffs = []
        if crc_diff_files:
            checksums_diffs = [
                FileImporter.get_checksums(x) for x in crc_diff_files
            ]
        output = instructions_dto.output

        if output:
            crc_file_location = output
            report_file_location = output

        manager = ChecksumManager(
            location=location,
            crc_file_location=crc_file_location,
            user_request=user_request,
            is_fast=is_fast,
            checksums_diff_1=checksums_diffs[0] if checksums_diffs else [],
            checksums_diff_2=checksums_diffs[1] if checksums_diffs else [],
        )
        crc_diff_report = manager.do()
        if crc_diff_report:
            FileImporter.save_crc_diff_report(
                report_file_location, crc_diff_report
            )

        sys.exit(0)

    except SystemExit as e:
        if e.code == 0:
            description = "Successful System Exit"
            CrcutilLogger.get_logger().debug(description)
        else:
            description = (
                f"\n{Icons.BANNER_LEFT}Unexpected Error"
                f"{Icons.BANNER_RIGHT}\n{e!s}"
            )
            CrcutilLogger.get_logger().exception(description)
            raise

    except UnexpectedArgumentError as e:
        sys.tracebacklimit = 0
        description = (
            f"\n{Icons.BANNER_LEFT}User Argument Error{Icons.BANNER_RIGHT}\n"
            f"These arguments are unrecognized: \n"
        )
        for argument in e.args[0]:
            description += "-> " + argument + "\n"
        CrcutilLogger.get_logger().error(description)
        sys.exit(1)

    except UserError as e:
        sys.tracebacklimit = 0
        description = (
            f"\n{Icons.BANNER_LEFT}User Error{Icons.BANNER_RIGHT}\n{e!s}"
        )
        CrcutilLogger.get_logger().error(description)

    except (CorruptCrcError, json.decoder.JSONDecodeError) as e:
        sys.tracebacklimit = 0
        description = (
            f"\n{Icons.BANNER_LEFT}Corrupt crc Error"
            f"{Icons.BANNER_RIGHT}\n{e!s}"
        )
        CrcutilLogger.get_logger().error(description)

    except ValidationError as e:
        sys.tracebacklimit = 0
        description = (
            f"\n{Icons.BANNER_LEFT}Invalid Schema Error"
            f"{Icons.BANNER_RIGHT}\n{e!s}"
        )
        CrcutilLogger.get_logger().error(description)

    # No regular logger can be expected to be initialized
    except BootstrapError as e:
        sys.tracebacklimit = 0
        description = (
            f"\n{Icons.BANNER_LEFT}Program Initialization Error"
            f"{Icons.BANNER_RIGHT}\n{e!s}"
        )
        e.args = (description,)
        raise

    except Exception as e:  # noqa: BLE001
        description = (
            f"\n{Icons.BANNER_LEFT}Unexpected Error{Icons.BANNER_RIGHT}\n{e!s}"
        )
        CrcutilLogger.get_logger().exception(description)


if __name__ == "__main__":
    main()
