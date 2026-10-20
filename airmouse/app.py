import threading
import time
import tkinter as tk
from typing import Callable, Sequence

from .cursor import CursorController, CursorFailSafe
from .controls import KeyboardInput
from .motion import MotionMapper
from .sensor import SensorSource
from .strokes import StrokeRecorder
from .ui import ControlPanel, PanelState


class AirMouseApp:
    """Runs the main loop. Receives every collaborator; builds none of them."""

    def __init__(
        self,
        *,
        root: tk.Tk,
        mode_name: str,
        update_ms: int,
        max_dt_s: float,
        source: SensorSource,
        mapper: MotionMapper,
        cursor: CursorController,
        recorder: StrokeRecorder,
        keyboard_input: KeyboardInput,
        panel: ControlPanel,
        move_gate: threading.Event,
        tick_hooks: Sequence[Callable[[], None]] = (),
    ):
        self._root = root
        self._mode_name = mode_name
        self._update_ms = update_ms
        self._max_dt_s = max_dt_s
        self._source = source
        self._mapper = mapper
        self._cursor = cursor
        self._recorder = recorder
        self._keyboard = keyboard_input
        self._panel = panel
        self._move_gate = move_gate
        self._tick_hooks = tuple(tick_hooks)

        self._running = True
        self._last_time = time.monotonic()
        self._last_state = None

        source.subscribe(mapper.on_sample)
        root.protocol("WM_DELETE_WINDOW", self.shutdown)

    def run(self) -> None:
        self._source.start()
        self._keyboard.start()
        self._tick()
        self._root.mainloop()

    def shutdown(self) -> None:
        if not self._running:
            return
        self._running = False
        self._move_gate.clear()

        self._keyboard.stop()
        self._source.stop()
        self._cursor.release_all()

        try:
            self._root.destroy()
        except tk.TclError:
            pass

    def _tick(self) -> None:
        if not self._running:
            return

        now = time.monotonic()
        dt = min(now - self._last_time, self._max_dt_s)
        self._last_time = now

        enabled = self._move_gate.is_set()
        dx, dy = self._mapper.step(dt, enabled)

        try:
            if enabled and self._source.connected and self._mapper.ready:
                self._cursor.move(dx, dy)
            if self._recorder.active:
                self._recorder.record(self._cursor.position())
        except CursorFailSafe:
            self.shutdown()
            return

        for hook in self._tick_hooks:
            hook()

        state = PanelState(
            connected=self._source.connected,
            ready=self._mapper.ready,
            move_enabled=enabled,
            mode=self._mode_name,
            stroke_count=len(self._recorder.strokes),
        )
        if state != self._last_state:
            self._last_state = state
            self._panel.render(state)

        # Tk only repaints when its event queue is empty. A steady stream of
        # pointer events would starve it, so repaint explicitly every tick.
        self._root.update_idletasks()

        self._root.after(self._update_ms, self._tick)
