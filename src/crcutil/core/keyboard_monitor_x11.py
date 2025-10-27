from __future__ import annotations

import os

from pynput import keyboard
from Xlib import X, display

from crcutil.core.keyboard_monitor import KeyboardMonitor
from crcutil.util.crcutil_logger import CrcutilLogger


class KeyboardMonitorX11(KeyboardMonitor):
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

    def is_terminal_focused(self) -> bool:
        try:
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
                    "kitty",
                )
            )

        except Exception as e:  # noqa: BLE001
            message = f"Could not probe for window focus: {e!s}"
            CrcutilLogger.get_logger().debug(message)
            return False
