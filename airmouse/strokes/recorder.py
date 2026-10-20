import threading
from typing import List, Optional

from ..config import StrokeConfig
from .listener import Point, Stroke, StrokeListener


class StrokeRecorder:
    """Collects cursor points between pen_down() and pen_up() into strokes.

    The finished strokes are the input for handwriting recognition.
    """

    def __init__(self, config: StrokeConfig):
        self._min_points = config.min_points
        self._lock = threading.Lock()
        self._current: Optional[Stroke] = None
        self._strokes: List[Stroke] = []
        self._listeners: List[StrokeListener] = []

    def add_listener(self, listener: StrokeListener) -> None:
        self._listeners.append(listener)

    @property
    def active(self) -> bool:
        return self._current is not None

    @property
    def strokes(self) -> List[Stroke]:
        with self._lock:
            return list(self._strokes)

    def pen_down(self) -> None:
        with self._lock:
            self._current = []

    def pen_up(self) -> None:
        with self._lock:
            stroke, self._current = self._current, None
            if stroke is None:
                return
            if len(stroke) >= self._min_points:
                self._strokes.append(stroke)
                print(f"Stroke captured ({len(stroke)} points, {len(self._strokes)} total)")

        for listener in self._listeners:
            listener.on_stroke_end(stroke)

    def record(self, point: Point) -> None:
        with self._lock:
            if self._current is None:
                return
            previous = self._current[-1] if self._current else None
            if point == previous:
                return
            self._current.append(point)

        for listener in self._listeners:
            listener.on_point(previous, point)

    def clear(self) -> None:
        with self._lock:
            self._strokes.clear()
        for listener in self._listeners:
            listener.on_clear()
