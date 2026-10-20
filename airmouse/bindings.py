"""Default key map. Edit here to rebind keys or add commands."""

import threading
from typing import Dict

from .controls import ActionCommand, ButtonCommand, Command, HoldFlagCommand
from .cursor import CursorController
from .motion import MotionMapper
from .strokes import StrokeRecorder


def default_bindings(
    *,
    move_gate: threading.Event,
    cursor: CursorController,
    mapper: MotionMapper,
    recorder: StrokeRecorder,
) -> Dict[str, Command]:
    return {
        "space": HoldFlagCommand(move_gate),
        "e": ButtonCommand(
            cursor, "left",
            on_down=[recorder.pen_down], on_up=[recorder.pen_up],
        ),
        "q": ButtonCommand(cursor, "right"),
        "r": ActionCommand(mapper.recalibrate),
        "c": ActionCommand(recorder.clear),
    }
