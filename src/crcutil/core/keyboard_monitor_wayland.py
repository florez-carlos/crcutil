import threading

from evdev import InputDevice, list_devices

from crcutil.core.keyboard_monitor import KeyboardMonitor
from crcutil.exception.device_error import DeviceError

LEFT_ALT = 56
RIGHT_ALT = 100
P = 25
Q = 16


class KeyboardMonitorWayland(KeyboardMonitor):
    def __init__(self) -> None:
        self.is_paused = False
        self.is_quit = False
        self.pause_description = "\n*Press alt+p to pause/resume"
        self.quit_description = "*Press alt+q to quit"
        self.keyboard = None
        devices = [InputDevice(path) for path in list_devices()]
        for _, dev in enumerate(devices):
            if "keyboard" in dev.name.lower():
                self.keyboard = dev
                break
        if self.keyboard is None:
            description = "Failed to attach Wayland Keyboard"
            raise DeviceError(description)
        self._thread = None
        self._lock = threading.Lock()

    def start(self) -> None:
        with self._lock:
            self.is_paused = False
            self.is_quit = False
        self._thread = threading.Thread(target=self.listen, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        with self._lock:
            self.is_paused = False
            self.is_quit = True
        if (
            self._thread
            and self._thread.is_alive()
            and threading.current_thread() != self._thread
        ):
            self._thread.join(timeout=1.0)
        with self._lock:
            if self.keyboard is not None:
                self.keyboard.close()
                self.keyboard = None

    def get_pause_message(self) -> str:
        return self.pause_description

    def get_quit_message(self) -> str:
        return self.quit_description

    def is_listen_paused(self) -> bool:
        with self._lock:
            return self.is_paused

    def is_listen_quit(self) -> bool:
        with self._lock:
            return self.is_quit

    def __get_keyboard(self) -> InputDevice:
        with self._lock:
            return self.keyboard

    def listen(self) -> None:
        keyboard = self.__get_keyboard()
        if keyboard:
            try:
                while True:
                    if self.is_listen_quit():
                        break

                    try:
                        keys = keyboard.active_keys()
                    except OSError:
                        continue

                    if (P in keys and LEFT_ALT in keys) or (
                        P in keys and RIGHT_ALT in keys
                    ):
                        with self._lock:
                            self.is_paused = not self.is_paused
                    if (Q in keys and LEFT_ALT in keys) or (
                        Q in keys and RIGHT_ALT in keys
                    ):
                        with self._lock:
                            self.is_quit = True
                        break
            finally:
                if keyboard:
                    keyboard.close()
