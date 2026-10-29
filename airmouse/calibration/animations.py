"""Stage animations for the calibration wizard.

Each animation draws one frame: fn(canvas, t_seconds, phase). To add a new
motion (e.g. "left"), write a function and add it to ANIMATIONS.
"""

import math
from functools import partial
from typing import Callable, Dict

W, H = 600, 300
CX, CY = W / 2, H / 2

ACCENT = "#4c6ef5"
GO = "#2f9e44"
TRACK = "#ced4da"
INK = "#343a40"

Animation = Callable[[object, float, str], None]


def _colour(phase: str) -> str:
    return GO if phase == "capture" else ACCENT


def _ease(x: float) -> float:
    return x * x * (3 - 2 * x)


def _device(canvas, x: float, y: float, colour: str) -> None:
    canvas.create_rectangle(x - 42, y - 24, x + 42, y + 24, fill=colour, outline="")
    canvas.create_oval(x + 22, y - 8, x + 38, y + 8, fill="#ffffff", outline="")
    canvas.create_text(x - 10, y, text="MPU", fill="#ffffff", font=("Helvetica", 12, "bold"))


def _arrow_head(canvas, x: float, y: float, dx: float, dy: float, colour: str) -> None:
    size = 18
    px, py = -dy, dx                      # perpendicular
    canvas.create_polygon(
        x + dx * size, y + dy * size,
        x - dx * 6 + px * size * 0.8, y - dy * 6 + py * size * 0.8,
        x - dx * 6 - px * size * 0.8, y - dy * 6 - py * size * 0.8,
        fill=colour, outline="",
    )


def _swing(canvas, t: float, phase: str, direction, label: str) -> None:
    dx, dy = direction
    colour = _colour(phase)
    half = 150
    start = (CX - dx * half, CY - dy * half)
    end = (CX + dx * half, CY + dy * half)

    canvas.create_line(*start, *end, fill=TRACK, width=5, dash=(8, 8))
    _arrow_head(canvas, end[0] + dx * 22, end[1] + dy * 22, dx, dy, colour)

    # Slide start -> end, hold briefly, repeat.
    progress = _ease(min((t % 2.4) / 1.5, 1.0))
    x = start[0] + (end[0] - start[0]) * progress
    y = start[1] + (end[1] - start[1]) * progress
    _device(canvas, x, y, colour)

    canvas.create_text(CX, H - 24, text=label, fill=colour, font=("Helvetica", 20, "bold"))


def _still(canvas, t: float, phase: str) -> None:
    colour = _colour(phase)
    for k in range(3):
        radius = 40 + (t * 45 + k * 30) % 90
        canvas.create_oval(
            CX - radius, CY - radius, CX + radius, CY + radius,
            outline=TRACK, width=2,
        )
    _device(canvas, CX, CY, colour)
    canvas.create_text(CX, H - 24, text="HOLD STILL", fill=colour,
                       font=("Helvetica", 20, "bold"))


ANIMATIONS: Dict[str, Animation] = {
    "still": _still,
    "right": partial(_swing, direction=(1, 0), label="RIGHT"),
    "up": partial(_swing, direction=(0, -1), label="UP"),
}


def draw(canvas, kind: str, t: float, phase: str) -> None:
    ANIMATIONS.get(kind, _still)(canvas, t, phase)
