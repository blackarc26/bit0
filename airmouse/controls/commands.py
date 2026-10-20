import threading
from typing import Callable, Sequence

from ..cursor import CursorController


class Command:
    """Something a key can trigger. Override press and/or release."""

    def press(self) -> None:
        pass

    def release(self) -> None:
        pass


class HoldFlagCommand(Command):
    """Flag is set while the key is held."""

    def __init__(self, flag: threading.Event):
        self._flag = flag

    def press(self) -> None:
        self._flag.set()

    def release(self) -> None:
        self._flag.clear()


class ButtonCommand(Command):
    """Holds a mouse button while the key is held, with optional hooks."""

    def __init__(
        self,
        cursor: CursorController,
        button: str,
        on_down: Sequence[Callable[[], None]] = (),
        on_up: Sequence[Callable[[], None]] = (),
    ):
        self._cursor = cursor
        self._button = button
        self._on_down = tuple(on_down)
        self._on_up = tuple(on_up)

    def press(self) -> None:
        self._cursor.button_down(self._button)
        for hook in self._on_down:
            hook()
        print(f"{self._button.capitalize()} mouse button held")

    def release(self) -> None:
        self._cursor.button_up(self._button)
        for hook in self._on_up:
            hook()
        print(f"{self._button.capitalize()} mouse button released")


class ActionCommand(Command):
    """Runs a function once when the key is pressed."""

    def __init__(self, action: Callable[[], None]):
        self._action = action

    def press(self) -> None:
        self._action()
