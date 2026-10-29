"""Composition root: the only place that picks concrete implementations."""

import sys
import threading
import tkinter as tk

from .app import AirMouseApp
from .bindings import default_bindings
from .config import AppConfig
from .controls import KeyboardInput, PynputKeyboardInput, TkKeyboardInput
from .cursor import CursorController
from .cursor.pyautogui_driver import PyAutoGuiDriver
from .motion import create_mapper
from .profile import apply_gyro_profile, load_gyro_axes
from .sensor import CsvSampleParser, SerialSensorSource
from .strokes import StrokeRecorder
from .ui import ControlPanel, TrailOverlay, Whiteboard


def _create_keyboard(backend: str, root: tk.Tk, bindings) -> KeyboardInput:
    if backend == "auto":
        # pynput's listener aborts the process on macOS, so use Tk there.
        backend = "tk" if sys.platform == "darwin" else "pynput"

    if backend == "tk":
        return TkKeyboardInput(root, bindings)
    if backend == "pynput":
        return PynputKeyboardInput(bindings)
    raise ValueError(f"Unknown keyboard backend '{backend}'. Known: auto, tk, pynput")


def build_app(config: AppConfig) -> AirMouseApp:
    calibrated = load_gyro_axes(config.gyro_profile_path) is not None
    config = apply_gyro_profile(config)

    root = tk.Tk()
    panel = ControlPanel(root)

    source = SerialSensorSource(config.serial, CsvSampleParser(config.serial))
    mapper = create_mapper(config.motion_mode, config)
    cursor = CursorController(PyAutoGuiDriver(), config.cursor)
    recorder = StrokeRecorder(config.strokes)

    tick_hooks = []
    if config.overlay.enabled:
        overlay = TrailOverlay(root, config.overlay)
        recorder.add_listener(overlay)
        tick_hooks.append(overlay.tick)

    if config.whiteboard.enabled:
        whiteboard = Whiteboard(root, config.whiteboard)
        recorder.add_listener(whiteboard)
        tick_hooks.append(whiteboard.tick)

    move_gate = threading.Event()
    bindings = default_bindings(
        move_gate=move_gate, cursor=cursor, mapper=mapper, recorder=recorder
    )
    keyboard_input = _create_keyboard(config.keyboard_backend, root, bindings)

    return AirMouseApp(
        root=root,
        mode_name=f"{config.motion_mode} ({'calibrated' if calibrated else 'DEFAULT AXES'})",
        update_ms=config.update_ms,
        max_dt_s=config.max_dt_s,
        source=source,
        mapper=mapper,
        cursor=cursor,
        recorder=recorder,
        keyboard_input=keyboard_input,
        panel=panel,
        move_gate=move_gate,
        tick_hooks=tick_hooks,
    )
