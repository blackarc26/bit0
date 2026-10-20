import tkinter as tk
from typing import Callable, Dict, Sequence

from ...config import WhiteboardConfig
from ...strokes import StrokeListener
from .toolbar import Toolbar
from .tools import DEFAULT_TOOLS, INK_TAG, BrushStyle, Tool

ToolFactory = Callable[[tk.Canvas, BrushStyle], Tool]

HINT = "Hold SPACE to move the pointer   ·   hold E to press (draw / click)   ·   C clears"


class Whiteboard(StrokeListener):
    """A small Excalidraw-style test surface.

    It uses ordinary Tk mouse events. The air mouse moves the real cursor
    and E presses the real left button, so no extra wiring is needed.
    """

    def __init__(
        self,
        root: tk.Tk,
        config: WhiteboardConfig,
        tool_factories: Sequence[ToolFactory] = DEFAULT_TOOLS,
    ):
        self._cfg = config
        self._clear_requested = False

        self._window = tk.Toplevel(root)
        self._window.title("Air Mouse Whiteboard")
        self._window.geometry(f"{config.width}x{config.height}+{config.x}+{config.y}")
        self._window.configure(bg="#ffffff")

        self._style = BrushStyle(config.colours[0], config.widths[1])
        self._canvas = tk.Canvas(
            self._window, bg=config.background, highlightthickness=0
        )

        self._tools: Dict[str, Tool] = {}
        for factory in tool_factories:
            tool = factory(self._canvas, self._style)
            self._tools[tool.label] = tool

        self._toolbar = Toolbar(
            self._window,
            tool_labels=list(self._tools),
            colours=config.colours,
            widths=config.widths,
            on_tool=self._select_tool,
            on_colour=self._set_colour,
            on_width=self._set_width,
            on_clear=self.clear,
        )
        self._toolbar.pack(fill="x")
        tk.Frame(self._window, height=1, bg="#dee2e6").pack(fill="x")

        tk.Label(
            self._window, text=HINT, font=("Helvetica", 11),
            fg="#868e96", bg="#ffffff", pady=6,
        ).pack(side="bottom", fill="x")

        self._canvas.pack(fill="both", expand=True)

        self._select_tool(next(iter(self._tools)))
        self._set_colour(self._style.colour)
        self._set_width(self._style.width)

        self._canvas.bind("<ButtonPress-1>", lambda e: self._active.press(e.x, e.y))
        self._canvas.bind("<B1-Motion>", lambda e: self._active.drag(e.x, e.y))
        self._canvas.bind("<ButtonRelease-1>", lambda e: self._active.release(e.x, e.y))

    # ---- selection ----

    def _select_tool(self, name: str) -> None:
        self._active = self._tools[name]
        self._canvas.config(cursor=self._active.cursor)
        self._toolbar.show_tool(name)

    def _set_colour(self, colour: str) -> None:
        self._style.colour = colour
        self._toolbar.show_colour(colour)

    def _set_width(self, width: int) -> None:
        self._style.width = width
        self._toolbar.show_width(width)

    # ---- actions ----

    def clear(self) -> None:
        self._canvas.delete(INK_TAG)

    # ---- StrokeListener: the C key may arrive on another thread ----

    def on_clear(self) -> None:
        self._clear_requested = True

    # ---- UI-thread hook ----

    def tick(self) -> None:
        if self._clear_requested:
            self._clear_requested = False
            self.clear()
