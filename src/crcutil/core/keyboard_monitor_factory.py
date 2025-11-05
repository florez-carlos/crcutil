import os
import platform

from crcutil.core.keyboard_monitor import KeyboardMonitor
from crcutil.exception.device_error import DeviceError
from crcutil.util.static import Static


class KeyboardMonitorFactory(Static):
    @staticmethod
    def get() -> KeyboardMonitor:
        system = platform.system()

        if system == "Windows":
            from crcutil.core.keyboard_monitor_windows import (  # noqa:PLC0415
                KeyboardMonitorWindows,
            )

            return KeyboardMonitorWindows()
        elif system == "Linux":
            session = os.getenv("XDG_SESSION_TYPE") or ""

            if session.startswith("wayland"):
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
                description = f"Could not determine Linux session: {session}"
                raise DeviceError(description)

        else:
            description = f"Could not determine system: {system}"
            raise DeviceError(description)
