import os
import platform

from crcutil.core.keyboard_monitor import KeyboardMonitor
from crcutil.exception.device_error import DeviceError
from crcutil.util.static import Static


class KeyboardMonitorFactory(Static):
    @staticmethod
    def get() -> KeyboardMonitor:
        """
        Gets a KeyboardMonitor compatible with the current system/session

        Returns:
            KeyboardMonitor: An appropriate monitor to the system/session
        Raises:
            DeviceError: If not a graphical session or system not Windows/Linux
        """
        system = platform.system()

        if system == "Windows":
            from crcutil.core.keyboard_monitor_windows import (  # noqa:PLC0415
                KeyboardMonitorWindows,
            )

            return KeyboardMonitorWindows()

        elif system == "Darwin":
            import ctypes  # noqa:PLC0415

            app_services = ctypes.cdll.LoadLibrary(
                "/System/Library/Frameworks/ApplicationServices.framework/ApplicationServices"
            )
            accesibility_access = app_services.AXIsProcessTrusted() == 1
            if not accesibility_access:
                description = (
                    "Terminal does not have accesibility access. "
                    "To enable playback controls on MacOS: "
                    "https://github.com/florez-carlos/"
                    "crcutil#macos"
                )
                raise DeviceError(description)

            from crcutil.core.keyboard_monitor_darwin import (  # noqa:PLC0415
                KeyboardMonitorDarwin,
            )

            return KeyboardMonitorDarwin()
        elif system == "Linux":
            import getpass  # noqa:PLC0415
            import grp  # noqa:PLC0415
            import pwd  # noqa:PLC0415

            session = os.getenv("XDG_SESSION_TYPE") or ""

            if session.startswith("wayland"):
                username = getpass.getuser()
                user = pwd.getpwnam(username)
                groups = [
                    g.gr_name
                    for g in grp.getgrall()
                    if username in g.gr_mem or g.gr_gid == user.pw_gid
                ]
                if "input" not in groups:
                    description = (
                        "user not assigned to input group. "
                        "To enable playback controls on wayland: "
                        "https://github.com/florez-carlos/"
                        "crcutil#linux-wayland"
                    )
                    raise DeviceError(description)

                from crcutil.core.keyboard_monitor_wayland import (  # noqa:PLC0415
                    KeyboardMonitorWayland,
                )

                return KeyboardMonitorWayland()
            if session.startswith("x11"):
                from crcutil.core.keyboard_monitor_x11 import (  # noqa:PLC0415
                    KeyboardMonitorX11,
                )

                return KeyboardMonitorX11()
            else:
                description = f"Not a graphical session: {session}"
                raise DeviceError(description)

        else:
            description = f"Unsupported system: {system}"
            raise DeviceError(description)
