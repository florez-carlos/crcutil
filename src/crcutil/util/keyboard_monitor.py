from __future__ import annotations

import os
import platform

from pynput import keyboard
from Xlib import X, display

from crcutil.util.crcutil_logger import CrcutilLogger


class KeyboardMonitor:
    def __init__(self) -> None:
        self.is_paused = False
        self.is_quit = False
        self.listener = None

    def start(self) -> None:
        self.listener = keyboard.Listener(on_press=self.on_press)
        self.listener.start()

    def stop(self) -> None:
        if self.listener:
            self.listener.stop()
        self.is_quit = True

    def on_press(self, key: keyboard.Key | keyboard.KeyCode | None) -> None:
        try:
            if self.is_terminal_focused():
                if key == keyboard.KeyCode.from_char("p"):
                    self.is_paused = not self.is_paused
                if key == keyboard.KeyCode.from_char("q"):
                    self.stop()
        except AttributeError:
            pass

    def is_terminal_focused(self) -> bool:
        try:
            if platform.system() == "Windows":
                import ctypes
                from ctypes import (
                    windll,  # pyright: ignore[reportAttributeAccessIssue]
                )

                hwnd = windll.user32.GetForegroundWindow()
                length = windll.user32.GetWindowTextLengthW(hwnd)
                buff = ctypes.create_unicode_buffer(length + 1)
                windll.user32.GetWindowTextW(hwnd, buff, length + 1)
                return buff.value.lower().strip().startswith(
                    "command prompt"
                ) or buff.value.lower().strip().startswith(
                    "windows powershell"
                )

            elif platform.system() == "Linux":
                disp = display.Display(os.environ["DISPLAY"])

                root = disp.screen().root
                active_window_id = root.get_full_property(
                    disp.intern_atom("_NET_ACTIVE_WINDOW"), X.AnyPropertyType
                )
                active_window = disp.create_resource_object(
                    "window", active_window_id.value[-1]
                )
                wm_class = active_window.get_wm_class()
                if not wm_class:
                    return True
                name = wm_class[0]
                return name.startswith(
                    (
                        "gnome-terminal",
                        "konsole",
                        "xterm",
                        "urxvt",
                        "alacritty",
                    )
                )

        except Exception as e:  # noqa: BLE001
            message = f"Could not probe for window focus: {e!s}"
            CrcutilLogger.get_logger().debug(message)
            return True

        else:
            return True
