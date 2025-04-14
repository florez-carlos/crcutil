import json
import sys

from jsonschema.exceptions import ValidationError

from crcutil.core.crc import Crc
from crcutil.core.prompt import Prompt
from crcutil.exception.bootstrap_error import BootstrapError
from crcutil.exception.corrupt_hash_error import CorruptHashError
from crcutil.exception.unexpected_argument_error import UnexpectedArgumentError
from crcutil.exception.user_error import UserError
from crcutil.util.crcutil_logger import CrcutilLogger
from crcutil.util.file_importer import FileImporter


def main() -> None:
    try:
        bootstrap_paths_dto = FileImporter.bootstrap()

        log_dir = bootstrap_paths_dto.log_dir
        hash_file_location = bootstrap_paths_dto.hash_file
        report_file_location = bootstrap_paths_dto.report_file

        log_config_file_path = (
            FileImporter.get_project_root()
            / "crcutil"
            / "config"
            / "log_config.yaml"
        )

        log_config = FileImporter.get_logging_config(log_config_file_path)

        CrcutilLogger(log_dir, log_config)

        instructions_dto = Prompt.get_user_instructions_dto()
        location = instructions_dto.location
        user_request = instructions_dto.request
        hash_diff_files = instructions_dto.hash_diff_files
        hash_diff_dtos = []
        if hash_diff_files:
            hash_diff_dtos = [
                FileImporter.get_hash(x) for x in hash_diff_files
            ]
        output = instructions_dto.output

        if output:
            hash_file_location = output
            report_file_location = output

        crc_obj = Crc(
            location=location,
            hash_file_location=hash_file_location,
            user_request=user_request,
            hash_diff_1=hash_diff_dtos[0] if hash_diff_dtos else [],
            hash_diff_2=hash_diff_dtos[1] if hash_diff_dtos else [],
        )
        hash_diff_report = crc_obj.do()
        if hash_diff_report:
            FileImporter.save_hash_diff_report(
                report_file_location, hash_diff_report
            )

        sys.exit(0)

    except SystemExit as e:
        if e.code == 0:
            description = "Successful System Exit"
            CrcutilLogger.get_logger().debug(description)
        else:
            description = "\n=====Unexpected Error=====\n" f"{e!s}"
            CrcutilLogger.get_logger().exception(description)
            raise

    except UnexpectedArgumentError as e:
        sys.tracebacklimit = 0
        description = (
            "\n=====User Argument Error=====\n"
            "These arguments are unrecognized: \n"
        )
        for argument in e.args[0]:
            description += "-> " + argument + "\n"
        CrcutilLogger.get_logger().error(description)
        sys.exit(1)

    except UserError as e:
        sys.tracebacklimit = 0
        description = "\n=====User Error=====\n" f"{e!s}"
        CrcutilLogger.get_logger().error(description)

    except CorruptHashError as e:
        sys.tracebacklimit = 0
        description = "\n=====Corrupt Hash Error=====\n" f"{e!s}"
        CrcutilLogger.get_logger().error(description)

    except json.decoder.JSONDecodeError as e:
        sys.tracebacklimit = 0
        description = "\n=====Corrupt Hash Error=====\n" f"{e!s}"
        CrcutilLogger.get_logger().error(description)

    except ValidationError as e:
        sys.tracebacklimit = 0
        description = "\n=====Invalid Schema Error=====\n" f"{e!s}"
        CrcutilLogger.get_logger().error(description)

    # No regular logger can be expected to be initialized
    except BootstrapError as e:
        description = "\n=====Program Initialization Error=====\n" f"{e!s}"
        e.args = (description,)
        raise

    except Exception as e:  # noqa: BLE001
        description = "\n=====Unexpected Error=====\n" f"{e!s}"
        CrcutilLogger.get_logger().exception(description)


if __name__ == "__main__":
    main()
