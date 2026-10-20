import tkinter as tk
from dataclasses import dataclass

BG = "#181818"
GREEN = "#00dd88"
AMBER = "#ffaa44"
RED = "#ff6666"

HELP_TEXT = (
    "HOLD SPACE = Move cursor (rotate wrist)\n"
    "E = Left click / pen down     Q = Right click\n"
    "R = Recalibrate gyro (hold still)     C = Clear board\n"
    "Release SPACE = Stop cursor"
)


@dataclass(frozen=True)
class PanelState:
    connected: bool
    ready: bool
    move_enabled: bool
    mode: str
    stroke_count: int


class ControlPanel:
    """Status window. Knows nothing about sensors or the cursor."""

    def __init__(self, root: tk.Tk):
        root.title("MPU6050 Air Mouse")
        root.geometry("480x320+20+60")
        root.configure(bg=BG)
        root.resizable(False, False)

        tk.Label(
            root, text="MPU6050 AIR MOUSE",
            font=("Arial", 21, "bold"), fg="white", bg=BG,
        ).pack(pady=(18, 12))

        self._status = self._label(root, "CONNECTING...", ("Arial", 11, "bold"), AMBER, 4)
        self._move = self._label(root, "", ("Arial", 11, "bold"), AMBER, 8)
        self._info = self._label(root, "Waiting for sensor...", ("Consolas", 10), "white", 6)

        tk.Label(
            root, text=HELP_TEXT, font=("Arial", 11),
            fg="#cccccc", bg=BG, justify="center",
        ).pack(pady=12)

    @staticmethod
    def _label(root, text, font, fg, pady) -> tk.Label:
        label = tk.Label(root, text=text, font=font, fg=fg, bg=BG)
        label.pack(pady=pady)
        return label

    def render(self, state: PanelState) -> None:
        if not state.connected:
            self._status.config(text="NOT CONNECTED", fg=RED)
        elif not state.ready:
            self._status.config(text="CALIBRATING - HOLD STILL", fg=AMBER)
        else:
            self._status.config(text="CONNECTED", fg=GREEN)

        if state.move_enabled:
            self._move.config(text="SPACE HELD - MOVEMENT ENABLED", fg=GREEN)
        else:
            self._move.config(text="SPACE RELEASED - CURSOR LOCKED", fg=AMBER)

        self._info.config(text=f"Mode: {state.mode}   Strokes: {state.stroke_count}")
