from abc import ABC
from dataclasses import dataclass
from tkinter import Canvas
from typing import List, Optional

INK_TAG = "ink"


@dataclass
class BrushStyle:
    """Shared, mutable: the toolbar edits it, tools read it."""

    colour: str
    width: int


class Tool(ABC):
    """A whiteboard tool. Override the pointer events you need.

    To add a tool: subclass this, give it a `label` and `cursor`, and add
    the class to the tools passed to Whiteboard.
    """

    label = "Tool"
    cursor = "arrow"

    def __init__(self, canvas: Canvas, style: BrushStyle):
        self._canvas = canvas
        self._style = style

    def press(self, x: float, y: float) -> None:
        pass

    def drag(self, x: float, y: float) -> None:
        pass

    def release(self, x: float, y: float) -> None:
        pass


class PenTool(Tool):
    label = "Pen"
    cursor = "pencil"

    def __init__(self, canvas: Canvas, style: BrushStyle):
        super().__init__(canvas, style)
        self._item: Optional[int] = None
        self._points: List[float] = []

    def press(self, x: float, y: float) -> None:
        self._points = [x, y, x, y]
        self._item = self._canvas.create_line(
            *self._points,
            fill=self._style.colour, width=self._style.width,
            capstyle="round", joinstyle="round", smooth=True,
            tags=INK_TAG,
        )

    def drag(self, x: float, y: float) -> None:
        if self._item is None:
            return
        self._points += [x, y]
        self._canvas.coords(self._item, *self._points)

    def release(self, x: float, y: float) -> None:
        self._item = None


class EraserTool(Tool):
    label = "Eraser"
    cursor = "circle"

    def _erase(self, x: float, y: float) -> None:
        r = max(12, self._style.width * 4)
        for item in self._canvas.find_overlapping(x - r, y - r, x + r, y + r):
            if INK_TAG in self._canvas.gettags(item):
                self._canvas.delete(item)

    def press(self, x: float, y: float) -> None:
        self._erase(x, y)

    def drag(self, x: float, y: float) -> None:
        self._erase(x, y)


class MoveTool(Tool):
    label = "Move"
    cursor = "fleur"
    GRAB_RADIUS = 14

    def __init__(self, canvas: Canvas, style: BrushStyle):
        super().__init__(canvas, style)
        self._item: Optional[int] = None
        self._last = (0.0, 0.0)

    def press(self, x: float, y: float) -> None:
        r = self.GRAB_RADIUS
        hits = [
            item for item in self._canvas.find_overlapping(x - r, y - r, x + r, y + r)
            if INK_TAG in self._canvas.gettags(item)
        ]
        # Topmost item under the pointer.
        self._item = hits[-1] if hits else None
        self._last = (x, y)

    def drag(self, x: float, y: float) -> None:
        if self._item is None:
            return
        self._canvas.move(self._item, x - self._last[0], y - self._last[1])
        self._last = (x, y)

    def release(self, x: float, y: float) -> None:
        self._item = None


DEFAULT_TOOLS = (PenTool, EraserTool, MoveTool)
