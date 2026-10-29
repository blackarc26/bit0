import tkinter as tk
from typing import Callable

ACCENT = "#4c6ef5"
NEUTRAL_BG = "#f1f3f5"
NEUTRAL_FG = "#343a40"
DISABLED_FG = "#adb5bd"


class FlatButton(tk.Label):
    """Flat button that looks the same on every OS (native Tk buttons
    ignore their colours on macOS)."""

    def __init__(self, parent, text: str, command: Callable[[], None], primary: bool = False):
        super().__init__(
            parent, text=text, font=("Helvetica", 14, "bold"),
            padx=24, pady=10, cursor="hand2",
        )
        self._command = command
        self._primary = primary
        self._enabled = True
        self.bind("<ButtonPress-1>", self._on_click)
        self._paint()

    def set_enabled(self, enabled: bool) -> None:
        self._enabled = enabled
        self._paint()

    def _on_click(self, _event) -> None:
        if self._enabled:
            self._command()

    def _paint(self) -> None:
        if not self._enabled:
            self.config(bg=NEUTRAL_BG, fg=DISABLED_FG, cursor="arrow")
        elif self._primary:
            self.config(bg=ACCENT, fg="#ffffff", cursor="hand2")
        else:
            self.config(bg=NEUTRAL_BG, fg=NEUTRAL_FG, cursor="hand2")
