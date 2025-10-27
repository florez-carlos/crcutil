from __future__ import annotations

import platform

from pynput import keyboard

from crcutil.core.keyboard_monitor import KeyboardMonitor
from crcutil.util.crcutil_logger import CrcutilLogger


class KeyboardMonitorWindows(KeyboardMonitor):
    def __init__(self) -> None:
        self.is_paused = False
        self.is_quit = False
        self.listener = None
        self.pause_description = "\n*Press p to pause/resume"
        self.quit_description = "*Press q to quit"

    def start(self) -> None:
        self.is_paused = False
        self.is_quit = False
        self.listener = keyboard.Listener(on_press=self.__on_press)
        self.listener.start()

    def stop(self) -> None:
        self.is_paused = False
        self.is_quit = True
        if self.listener:
            self.listener.stop()

    def get_pause_message(self) -> str:
        return self.pause_description

    def get_quit_message(self) -> str:
        return self.quit_description

    def is_listen_quit(self) -> bool:
        return self.is_quit

    def is_listen_paused(self) -> bool:
        return self.is_paused

    def __on_press(self, key: keyboard.Key | keyboard.KeyCode | None) -> None:
        try:
            if self.is_terminal_focused():
                if key == keyboard.KeyCode.from_char("p"):
                    self.is_paused = not self.is_paused
                if key == keyboard.KeyCode.from_char("q"):
                    self.stop()
        except AttributeError:
            pass

    def _is_windows_window_title(self, title_candidates: list[str]) -> bool:
        try:
            if platform.system() == "Windows":
                import ctypes  # noqa: PLC0415
                from ctypes import (  # noqa: PLC0415
                    windll,  # pyright: ignore[reportAttributeAccessIssue]
                )

                hwnd = windll.user32.GetForegroundWindow()
                length = windll.user32.GetWindowTextLengthW(hwnd)
                buff = ctypes.create_unicode_buffer(length + 1)
                windll.user32.GetWindowTextW(hwnd, buff, length + 1)
                for title_candidate in title_candidates:
                    if buff.value.lower().strip().startswith(title_candidate):
                        return True

        except Exception as e:  # noqa: BLE001
            message = f"Could not probe for window focus: {e!s}"
            CrcutilLogger.get_logger().debug(message)
            return False

        return False

    def is_cmd_focused(self) -> bool:
        window_labels = ["command prompt"]
        return self._is_windows_window_title(title_candidates=window_labels)

    def is_powershell_focused(self) -> bool:
        window_labels = ["windows powershell", "powershell"]
        return self._is_windows_window_title(title_candidates=window_labels)

    def is_terminal_focused(self) -> bool:
        try:
            return self.is_cmd_focused() or self.is_powershell_focused()

        except Exception as e:  # noqa: BLE001
            message = f"Could not probe for window focus: {e!s}"
            CrcutilLogger.get_logger().debug(message)
            return False
