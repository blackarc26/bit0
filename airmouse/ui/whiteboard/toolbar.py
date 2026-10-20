import tkinter as tk
from typing import Callable, Dict, Sequence

BAR_BG = "#ffffff"
BUTTON_BG = "#f1f3f5"
BUTTON_FG = "#343a40"
ACTIVE_BG = "#4c6ef5"
ACTIVE_FG = "#ffffff"
RING = "#4c6ef5"
FONT = ("Helvetica", 14, "bold")
SWATCH = 38


class Toolbar(tk.Frame):
    """Big, flat toolbar drawn from Labels and Canvases.

    Native Tk buttons ignore their colours on macOS, so everything here is
    custom-drawn. Large hit areas keep it usable with a hand-held pointer.
    """

    def __init__(
        self,
        parent,
        tool_labels: Sequence[str],
        colours: Sequence[str],
        widths: Sequence[int],
        on_tool: Callable[[str], None],
        on_colour: Callable[[str], None],
        on_width: Callable[[int], None],
        on_clear: Callable[[], None],
    ):
        super().__init__(parent, bg=BAR_BG)

        self._tool_buttons: Dict[str, tk.Label] = {}
        self._colour_swatches: Dict[str, tk.Canvas] = {}
        self._width_swatches: Dict[int, tk.Canvas] = {}

        for label in tool_labels:
            self._tool_buttons[label] = self._button(
                label, lambda name=label: on_tool(name)
            )

        self._gap()
        for colour in colours:
            swatch = self._swatch(lambda c=colour: on_colour(c))
            swatch.create_oval(7, 7, SWATCH - 7, SWATCH - 7, fill=colour, outline=colour)
            self._colour_swatches[colour] = swatch

        self._gap()
        for width in widths:
            swatch = self._swatch(lambda w=width: on_width(w))
            r = 2 + width
            c = SWATCH / 2
            swatch.create_oval(c - r, c - r, c + r, c + r, fill=BUTTON_FG, outline=BUTTON_FG)
            self._width_swatches[width] = swatch

        clear = self._button("Clear", on_clear, side="right")
        clear.config(bg=BUTTON_BG, fg="#c92a2a")

    # ---- selection highlighting ----

    def show_tool(self, label: str) -> None:
        for name, button in self._tool_buttons.items():
            active = name == label
            button.config(
                bg=ACTIVE_BG if active else BUTTON_BG,
                fg=ACTIVE_FG if active else BUTTON_FG,
            )

    def show_colour(self, colour: str) -> None:
        self._ring(self._colour_swatches, colour)

    def show_width(self, width: int) -> None:
        self._ring(self._width_swatches, width)

    @staticmethod
    def _ring(swatches: dict, selected) -> None:
        for key, swatch in swatches.items():
            swatch.delete("ring")
            if key == selected:
                swatch.create_oval(
                    2, 2, SWATCH - 2, SWATCH - 2,
                    outline=RING, width=3, tags="ring",
                )

    # ---- widget helpers ----

    def _button(self, text: str, command, side: str = "left") -> tk.Label:
        button = tk.Label(
            self, text=text, font=FONT, bg=BUTTON_BG, fg=BUTTON_FG,
            padx=20, pady=12, cursor="hand2",
        )
        button.pack(side=side, padx=(10, 0) if side == "left" else 10, pady=10)
        button.bind("<ButtonPress-1>", lambda e: command())
        return button

    def _swatch(self, command) -> tk.Canvas:
        swatch = tk.Canvas(
            self, width=SWATCH, height=SWATCH, bg=BAR_BG,
            highlightthickness=0, cursor="hand2",
        )
        swatch.pack(side="left", padx=3)
        swatch.bind("<ButtonPress-1>", lambda e: command())
        return swatch

    def _gap(self) -> None:
        tk.Frame(self, width=22, bg=BAR_BG).pack(side="left")
