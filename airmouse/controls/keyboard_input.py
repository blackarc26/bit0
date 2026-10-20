from abc import ABC, abstractmethod
from typing import Mapping, Set

from .commands import Command


class KeyboardInput(ABC):
    """Dispatches key presses/releases to Commands by key name.

    Subclasses only capture raw key events (pynput, Tk, ...) and call
    handle_press / handle_release. Key auto-repeat is ignored: a command is
    pressed once until released.
    """

    def __init__(self, bindings: Mapping[str, Command]):
        self._bindings = dict(bindings)
        self._down: Set[str] = set()

    @abstractmethod
    def start(self) -> None:
        ...

    @abstractmethod
    def stop(self) -> None:
        ...

    def handle_press(self, name) -> None:
        command = self._bindings.get(name)
        if command is None or name in self._down:
            return
        self._down.add(name)
        self._run(command.press)

    def handle_release(self, name) -> None:
        command = self._bindings.get(name)
        if command is None or name not in self._down:
            return
        self._down.discard(name)
        self._run(command.release)

    @staticmethod
    def _run(action) -> None:
        try:
            action()
        except Exception as error:
            print("Input error:", error)
