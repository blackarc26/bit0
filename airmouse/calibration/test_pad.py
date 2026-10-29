import threading
import tkinter as tk

from ..config import AppConfig, GyroConfig
from ..controls import ActionCommand, HoldFlagCommand, TkKeyboardInput
from ..motion.gyro import GyroMapper
from ..sensor import SensorSource

INK = "#1e1e1e"
ACCENT = "#4c6ef5"
GOOD = "#2f9e44"
MUTED = "#868e96"
BAD = "#e03131"

HINT = "SPACE = move    E = draw    C = clear    R = re-zero"


class TestPad:
    """A writing pad driven by the app's real motion pipeline.

    It runs the same GyroMapper (smoothing, deadzone, drift tracking), the
    same invert rules and the same Space / E / C keys as main.py, so what
    you feel here is exactly what the app will do.
    """

    __test__ = False   # not a pytest test class

    WIDTH = 600
    HEIGHT = 410

    def __init__(
        self,
        root: tk.Tk,
        canvas: tk.Canvas,
        config: AppConfig,
        gyro_config: GyroConfig,
        source: SensorSource,
    ):
        self._canvas = canvas
        self._cursor_cfg = config.cursor
        self._source = source

        self._mapper = GyroMapper(gyro_config)
        source.subscribe(self._mapper.on_sample)

        self._move = threading.Event()
        self._pen = threading.Event()
        self._pen_was_down = False
        self.flip_h = 1.0     # -1 reverses left/right on the pad (baked in on save)
        self.flip_v = 1.0     # -1 reverses up/down
        self._x = self.WIDTH / 2
        self._y = self.HEIGHT / 2

        self._keys = TkKeyboardInput(root, {
            "space": HoldFlagCommand(self._move),
            "e": HoldFlagCommand(self._pen),
            "c": ActionCommand(self.clear),
            "r": ActionCommand(self._mapper.recalibrate),
        })
        self._keys.start()

        canvas.delete("all")

    def clear(self) -> None:
        self._canvas.delete("ink")

    def toggle_flip_h(self) -> None:
        self.flip_h = -self.flip_h

    def toggle_flip_v(self) -> None:
        self.flip_v = -self.flip_v

    def close(self) -> None:
        self._keys.stop()
        self._source.unsubscribe(self._mapper.on_sample)

    def update(self) -> None:
        dx, dy = self._mapper.step(0.0, self._move.is_set())
        if self._cursor_cfg.invert_x:
            dx = -dx
        if self._cursor_cfg.invert_y:
            dy = -dy
        dx *= self.flip_h
        dy *= self.flip_v

        old_x, old_y = self._x, self._y
        self._x = max(8, min(self.WIDTH - 8, self._x + dx))
        self._y = max(8, min(self.HEIGHT - 8, self._y + dy))

        pen_down = self._pen.is_set()
        if pen_down:
            if self._pen_was_down and (old_x, old_y) != (self._x, self._y):
                self._canvas.create_line(
                    old_x, old_y, self._x, self._y, fill=INK, width=4,
                    capstyle="round", tags="ink")
            elif not self._pen_was_down:
                self._canvas.create_oval(
                    self._x - 2, self._y - 2, self._x + 2, self._y + 2,
                    fill=INK, outline=INK, tags="ink")
        self._pen_was_down = pen_down

        self._draw_overlay(pen_down)

    def _draw_overlay(self, pen_down: bool) -> None:
        canvas = self._canvas
        canvas.delete("ui")

        if not self._mapper.ready:
            canvas.create_text(self.WIDTH / 2, 28, tags="ui", fill=BAD,
                               font=("Helvetica", 14, "bold"),
                               text="Zeroing the sensor: hold still for a moment...")
        else:
            canvas.create_text(self.WIDTH / 2, 18, tags="ui", fill=MUTED,
                               font=("Helvetica", 11), text=HINT)

        w, h = self.WIDTH, self.HEIGHT
        for x, y, text in ((w - 46, h / 2, "RIGHT →"), (46, h / 2, "← LEFT"),
                           (w / 2, 44, "↑ UP"), (w / 2, h - 14, "↓ DOWN")):
            canvas.create_text(x, y, text=text, fill="#ced4da", tags="ui",
                               font=("Helvetica", 13, "bold"))

        colour = GOOD if pen_down else ACCENT
        canvas.create_oval(self._x - 8, self._y - 8, self._x + 8, self._y + 8,
                           outline=colour, width=3, tags="ui")
        canvas.create_oval(self._x - 2, self._y - 2, self._x + 2, self._y + 2,
                           fill=colour, outline="", tags="ui")
        canvas.tag_raise("ui")
