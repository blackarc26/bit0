from typing import Set, Tuple

from ..config import CursorConfig
from .base import CursorDriver


class CursorController:
    """Axis inversion and sub-pixel accumulation on top of a CursorDriver."""

    def __init__(self, driver: CursorDriver, config: CursorConfig):
        self._driver = driver
        self._cfg = config
        self._remainder_x = 0.0
        self._remainder_y = 0.0
        self._held: Set[str] = set()

    def move(self, dx: float, dy: float) -> None:
        if self._cfg.invert_x:
            dx = -dx
        if self._cfg.invert_y:
            dy = -dy

        self._remainder_x += dx
        self._remainder_y += dy

        ix = int(self._remainder_x)
        iy = int(self._remainder_y)
        self._remainder_x -= ix
        self._remainder_y -= iy

        if ix or iy:
            self._driver.move_rel(ix, iy)

    def position(self) -> Tuple[int, int]:
        return self._driver.position()

    def button_down(self, button: str) -> None:
        self._held.add(button)
        self._driver.button_down(button)

    def button_up(self, button: str) -> None:
        self._held.discard(button)
        self._driver.button_up(button)

    def release_all(self) -> None:
        """Never leave a mouse button stuck down."""
        for button in list(self._held):
            try:
                self.button_up(button)
            except Exception:
                pass
