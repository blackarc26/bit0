import time
import tkinter as tk
from typing import Optional

from ..config import OverlayConfig
from ..strokes import StrokeListener
from ..strokes.listener import Point, Stroke
from .click_through import make_click_through


class TrailOverlay(StrokeListener):
    """Transparent always-on-top canvas that draws the live pen trail.

    Tk is not thread-safe, so events from other threads only set flags;
    tick() (UI thread) applies them.
    """

    def __init__(self, root: tk.Tk, config: OverlayConfig):
        self._cfg = config
        self._canvas: Optional[tk.Canvas] = None
        self._clear_requested = False
        self._last_stroke_end: Optional[float] = None
        self._build(root)

    def _build(self, root: tk.Tk) -> None:
        cfg = self._cfg
        try:
            window = tk.Toplevel(root)
            window.overrideredirect(True)
            window.attributes("-topmost", True)
            window.attributes("-transparentcolor", cfg.transparent_colour)
            window.geometry(
                f"{root.winfo_screenwidth()}x{root.winfo_screenheight()}+0+0"
            )
            self._canvas = tk.Canvas(
                window, bg=cfg.transparent_colour, highlightthickness=0
            )
            self._canvas.pack(fill="both", expand=True)
            make_click_through(window)
        except tk.TclError as error:
            print("Overlay unavailable:", error)
            self._canvas = None

    # ---- StrokeListener ----

    def on_point(self, previous: Optional[Point], point: Point) -> None:
        if self._canvas is None or previous is None:
            return
        self._canvas.create_line(
            *previous, *point,
            fill=self._cfg.colour, width=self._cfg.width, capstyle="round",
        )

    def on_stroke_end(self, stroke: Stroke) -> None:
        self._last_stroke_end = time.monotonic()

    def on_clear(self) -> None:
        self._clear_requested = True

    # ---- UI-thread hook ----

    def tick(self) -> None:
        if self._canvas is None:
            return

        if self._clear_requested:
            self._clear_requested = False
            self._last_stroke_end = None
            self._canvas.delete("all")

        elif (
            self._last_stroke_end is not None
            and time.monotonic() - self._last_stroke_end > self._cfg.fade_after_s
        ):
            self._last_stroke_end = None
            self._canvas.delete("all")
