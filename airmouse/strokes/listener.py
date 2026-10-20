from typing import List, Optional, Tuple

Point = Tuple[int, int]
Stroke = List[Point]


class StrokeListener:
    """Observer of a StrokeRecorder. Override only what you need.

    on_point runs on the UI thread. on_stroke_end and on_clear may run on
    the keyboard thread, so do not touch UI widgets from them directly.
    """

    def on_point(self, previous: Optional[Point], point: Point) -> None:
        pass

    def on_stroke_end(self, stroke: Stroke) -> None:
        pass

    def on_clear(self) -> None:
        pass
