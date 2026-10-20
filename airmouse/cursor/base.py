from abc import ABC, abstractmethod
from typing import Tuple


class CursorFailSafe(Exception):
    """Raised by a driver when the user triggers its emergency stop."""


class CursorDriver(ABC):
    """Low-level OS pointer access. Swap implementations per platform."""

    @abstractmethod
    def move_rel(self, dx: int, dy: int) -> None:
        ...

    @abstractmethod
    def position(self) -> Tuple[int, int]:
        ...

    @abstractmethod
    def button_down(self, button: str) -> None:
        ...

    @abstractmethod
    def button_up(self, button: str) -> None:
        ...
