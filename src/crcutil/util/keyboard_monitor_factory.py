import os
import platform

from crcutil.exception.device_error import DeviceError
from crcutil.util.keyboard_monitor import KeyboardMonitor
from crcutil.util.keyboard_monitor_wayland import KeyboardMonitorWayland
from crcutil.util.keyboard_monitor_windows import KeyboardMonitorWindows
from crcutil.util.keyboard_monitor_x11 import KeyboardMonitorX11
from crcutil.util.static import Static


class KeyboardMonitorFactory(Static):
    @staticmethod
    def get() -> KeyboardMonitor:
        system = platform.system()

        if system == "Windows":
            return KeyboardMonitorWindows()
        elif system == "Linux":
            session = os.getenv("XDG_SESSION_TYPE") or ""

            if session.startswith("wayland"):
                return KeyboardMonitorWayland()
            if session.startswith("x11"):
                return KeyboardMonitorX11()
            else:
                description = f"Could not determine Linux session: {session}"
                raise DeviceError(description)

        else:
            description = f"Could not determine system: {system}"
            raise DeviceError(description)
