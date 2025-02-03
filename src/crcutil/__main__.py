import sys
from pathlib import Path

from jsonschema.exceptions import ValidationError

from crcutil.core.crc import crc
from crcutil.core.prompt import Prompt
from crcutil.exception.bootstrap_error import BootstrapError
from crcutil.exception.unexpected_argument_error import UnexpectedArgumentError
from crcutil.exception.user_error import UserError
from crcutil.util.crcutil_logger import CrcutilLogger
from crcutil.util.file_importer import FileImporter


def __walk(location: Path):
    for item in location.iterdir():
        if item.is_dir():
            __walk(item)


def main() -> None:
    try:
        bootstrap_paths_dto = FileImporter.bootstrap()

        log_dir = bootstrap_paths_dto.log_dir
        hash_file_location = bootstrap_paths_dto.hash_file

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
        crc_obj = crc(
            location=location,
            hash_file_location=hash_file_location,
            user_request=user_request,
        )
        crc_obj.do()

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
