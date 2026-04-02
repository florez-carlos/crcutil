from __future__ import annotations

import platform

from pynput import keyboard

from crcutil.core.keyboard_monitor import KeyboardMonitor
from crcutil.util.crcutil_logger import CrcutilLogger


class KeyboardMonitorDarwin(KeyboardMonitor):
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
            if platform.system() == "Darwin":
                from AppKit import (  # noqa: PLC0415  # pyright: ignore[reportMissingImports]
                    NSWorkspace,
                )

                active_app = NSWorkspace.sharedWorkspace().activeApplication()
                bundle_id: str = active_app.get(
                    "NSApplicationBundleIdentifier", ""
                )
                name: str = active_app.get("NSApplicationName", "")
                return bundle_id.startswith(
                    (
                        "com.apple.Terminal",
                        "com.googlecode.iterm2",
                        "io.alacritty",
                        "net.kovidgoyal.kitty",
                        "com.mitchellh.ghostty",
                    )
                ) or name.lower() in (
                    "terminal",
                    "iterm2",
                    "alacritty",
                    "kitty",
                    "ghostty",
                    "warp",
                    "hyper",
                )
        except Exception as e:  # noqa: BLE001
            message = f"Could not probe for window focus: {e!s}"
            CrcutilLogger.get_logger().debug(message)
            return False
        return False
