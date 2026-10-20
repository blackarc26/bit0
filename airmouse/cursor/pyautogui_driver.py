import sys
from typing import Set, Tuple

import pyautogui

from .base import CursorDriver, CursorFailSafe


class PyAutoGuiDriver(CursorDriver):
    def __init__(self) -> None:
        pyautogui.FAILSAFE = True   # slam the mouse into a corner to stop
        pyautogui.PAUSE = 0
        if sys.platform == "darwin":
            pyautogui.DARWIN_CATCH_UP_TIME = 0   # default sleeps 10 ms per move
        self._held: Set[str] = set()

    def move_rel(self, dx: int, dy: int) -> None:
        try:
            if self._held and sys.platform == "darwin":
                self._drag_rel(dx, dy)
            else:
                pyautogui.moveRel(dx, dy, duration=0)
        except pyautogui.FailSafeException as error:
            raise CursorFailSafe() from error

    def _drag_rel(self, dx: int, dy: int) -> None:
        """macOS only turns motion into a drag (what apps draw with) if the
        event type is 'dragged'; moveRel always sends 'moved'."""
        x, y = pyautogui.position()
        width, height = pyautogui.size()
        target_x = min(max(x + dx, 0), width - 1)
        target_y = min(max(y + dy, 0), height - 1)
        pyautogui.failSafeCheck()
        pyautogui.platformModule._dragTo(target_x, target_y, next(iter(self._held)))

    def position(self) -> Tuple[int, int]:
        x, y = pyautogui.position()
        return x, y

    def button_down(self, button: str) -> None:
        self._held.add(button)
        pyautogui.mouseDown(button=button)

    def button_up(self, button: str) -> None:
        self._held.discard(button)
        pyautogui.mouseUp(button=button)
