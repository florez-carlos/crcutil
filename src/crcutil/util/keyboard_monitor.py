from __future__ import annotations

from abc import ABC, abstractmethod


class KeyboardMonitor(ABC):
    @abstractmethod
    def start(self) -> None:
        pass

    @abstractmethod
    def stop(self) -> None:
        pass

    @abstractmethod
    def get_pause_message(self) -> str:
        pass

    @abstractmethod
    def get_quit_message(self) -> str:
        pass

    @abstractmethod
    def is_listen_quit(self) -> bool:
        pass

    @abstractmethod
    def is_listen_paused(self) -> bool:
        pass
