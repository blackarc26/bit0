import math
import time
import tkinter as tk
from dataclasses import replace
from typing import Sequence, Tuple

from ..config import AppConfig
from ..motion.axes import dot, fit_axes, norm
from ..profile import resolve_profile_path, save_gyro_axes
from ..sensor import CsvSampleParser, SensorSource, SerialSensorSource
from ..ui.widgets import FlatButton
from . import animations
from .analysis import AXIS_NAMES, MIN_ANGLE_DEG, describe, mean_rate, stroke_rotation
from .recorder import Recorder
from .steps import DEFAULT_STEPS, Step
from .test_pad import TestPad

TICK_MS = 33
BG = "#ffffff"
INK = "#343a40"
MUTED = "#868e96"
GOOD = "#2f9e44"
BAD = "#e03131"
WARN = "#e8590c"
ACCENT = "#4c6ef5"

BAR_RANGE_DPS = 120.0
OVERLAP_WARN_DEG = 35.0     # allowed deviation from a perfect 90° between right and up

# phases
INTRO, COUNTDOWN, CAPTURE, TEST = "intro", "countdown", "capture", "test"


class CalibrationWizard:
    """Guided gyro calibration with animated prompts and a writing pad.

    Pure UI orchestration: measuring is in analysis.py, the prompts are
    data in steps.py, the drawings are in animations.py, and the final
    writing pad (test_pad.py) runs the app's real motion pipeline.
    """

    def __init__(
        self,
        root: tk.Tk,
        config: AppConfig,
        source: SensorSource,
        recorder: Recorder,
        steps: Sequence[Step] = DEFAULT_STEPS,
        countdown_s: float = 3.0,
    ):
        self._root = root
        self._config = config
        self._source = source
        self._recorder = recorder
        self._steps = tuple(steps)
        self._countdown_s = countdown_s
        self._lsb = config.gyro.lsb_per_dps

        self._phase = INTRO
        self._phase_start = time.monotonic()
        self._step_index = 0
        self._bias: Tuple[float, float, float] = (0.0, 0.0, 0.0)
        self._results = {}
        self._weights = None
        self._pad = None
        self._alive = True
        self.saved = False

        self._build_ui()
        root.protocol("WM_DELETE_WINDOW", self.close)
        self._tick()

    # ------------------------------------------------------------ layout

    def _build_ui(self) -> None:
        root = self._root
        root.title("Gyro Calibration")
        root.geometry("660x740+60+30")
        root.configure(bg=BG)
        root.resizable(False, False)

        tk.Label(root, text="Gyro calibration", font=("Helvetica", 22, "bold"),
                 fg=INK, bg=BG).pack(pady=(16, 0))
        self._step_label = tk.Label(root, text="", font=("Helvetica", 12), fg=MUTED, bg=BG)
        self._step_label.pack(pady=(2, 6))

        self._stage = tk.Canvas(root, width=animations.W, height=animations.H,
                                bg="#f8f9fa", highlightthickness=0)
        self._stage.pack()

        self._instruction = tk.Label(root, text="", font=("Helvetica", 15), fg=INK, bg=BG,
                                     wraplength=600, justify="center")
        self._instruction.pack(pady=(12, 2))
        self._message = tk.Label(root, text="", font=("Helvetica", 13, "bold"), fg=MUTED,
                                 bg=BG, wraplength=600)
        self._message.pack(pady=(0, 6))

        self._bars_frame = tk.Frame(root, bg=BG)
        self._bars_frame.pack()
        tk.Label(self._bars_frame, text=f"Live gyro  (bars show ±{BAR_RANGE_DPS:.0f} °/s)",
                 font=("Helvetica", 11), fg=MUTED, bg=BG).pack()
        self._bars = tk.Canvas(self._bars_frame, width=animations.W, height=96, bg=BG,
                               highlightthickness=0)
        self._bars.pack(pady=(2, 8))

        self._buttons = tk.Frame(root, bg=BG)
        self._buttons.pack(pady=6)
        self._primary = FlatButton(self._buttons, "Start", self._on_primary, primary=True)
        self._primary.pack(side="left", padx=6)
        self._clear_btn = FlatButton(self._buttons, "Clear", lambda: self._pad and self._pad.clear())
        self._flip_h_btn = FlatButton(self._buttons, "Flip ↔", self._flip_h)
        self._flip_v_btn = FlatButton(self._buttons, "Flip ↕", self._flip_v)
        self._redo_btn = FlatButton(self._buttons, "Redo", self._restart)

    # ------------------------------------------------------------ flow

    def _set_phase(self, phase: str) -> None:
        self._phase = phase
        self._phase_start = time.monotonic()

    @property
    def _step(self) -> Step:
        return self._steps[self._step_index]

    def _on_primary(self) -> None:
        if self._phase == INTRO:
            self._step_index = 0
            self._results.clear()
            self._begin_step()
        elif self._phase == TEST:
            self.close() if self.saved else self._save()

    def _restart(self) -> None:
        self._leave_test()
        self._message.config(text="")
        self._primary.config(text="Start")
        self._primary.set_enabled(True)
        self.saved = False
        self._set_phase(INTRO)

    def _begin_step(self) -> None:
        self._primary.set_enabled(False)
        self._primary.config(text="Calibrating...")
        if self._step.countdown:
            self._set_phase(COUNTDOWN)
        else:
            self._recorder.take()
            self._set_phase(CAPTURE)

    def _advance(self) -> None:
        self._step_index += 1
        if self._step_index >= len(self._steps):
            self._fit()
        else:
            self._begin_step()

    def _retry_step(self, message: str) -> None:
        self._message.config(text=message, fg=BAD)
        self._begin_step()

    def _finish_capture(self) -> None:
        step = self._step
        rows = self._recorder.take()

        if len(rows) < 20:
            self._retry_step("No sensor data. Is the device connected and the app closed?")
            return

        if step.measure == "bias":
            self._bias = mean_rate(rows, self._lsb)
            self._message.config(text="Idle reading captured.", fg=GOOD)
        elif step.measure == "rotation":
            rotation = stroke_rotation(rows, self._bias, self._lsb)
            text = f"Measured: {describe(rotation)}"
            if norm(rotation) < MIN_ANGLE_DEG:
                self._retry_step(
                    f"{text}  - too small. Rotate or aim the device, a gyro cannot "
                    f"feel sliding it sideways. Try again."
                )
                return
            self._results[step.key] = rotation
            self._message.config(text=text + "   ✓", fg=GOOD)
        self._advance()

    def _fit(self) -> None:
        right, up = self._results["right"], self._results["up"]
        try:
            self._weights = fit_axes(right, up)
        except ValueError as error:
            self._message.config(
                text=f"{error}. Make 'up' clearly different from 'right'.", fg=BAD
            )
            self._step_index = next(
                i for i, s in enumerate(self._steps) if s.measure == "rotation"
            )
            self._results.clear()
            self._begin_step()
            return

        cosine = dot(right, up) / (norm(right) * norm(up))
        angle = math.degrees(math.acos(max(-1.0, min(1.0, cosine))))
        if abs(angle - 90.0) > OVERLAP_WARN_DEG:
            note = (f"Your 'right' and 'up' motions overlap ({angle:.0f}° apart, ideal 90°). "
                    f"Diagonal drift is likely. Redo with cleaner motions if the pad feels off.")
            self._message.config(text=note, fg=WARN)
        else:
            self._message.config(text="Axes found. Now try writing on the pad.", fg=GOOD)

        self._enter_test()

    # ------------------------------------------------------------ test pad

    def _enter_test(self) -> None:
        h_weights, v_weights = self._weights
        fitted = replace(self._config.gyro, h_weights=h_weights, v_weights=v_weights)

        self._bars_frame.pack_forget()
        self._stage.config(height=TestPad.HEIGHT)
        self._pad = TestPad(self._root, self._stage, self._config, fitted, self._source)

        self._primary.config(text="Save calibration")
        self._primary.set_enabled(True)
        for button in (self._flip_h_btn, self._flip_v_btn, self._clear_btn, self._redo_btn):
            button.pack(side="left", padx=6)
        self._set_phase(TEST)

    def _leave_test(self) -> None:
        if self._pad is not None:
            self._pad.close()
            self._pad = None
        for button in (self._flip_h_btn, self._flip_v_btn, self._clear_btn, self._redo_btn):
            button.pack_forget()
        self._stage.config(height=animations.H)
        self._bars_frame.pack(before=self._buttons)

    def _flip_h(self) -> None:
        if self._pad:
            self._pad.toggle_flip_h()
            self._message.config(text="Left/right reversed. Check the pad again.", fg=WARN)

    def _flip_v(self) -> None:
        if self._pad:
            self._pad.toggle_flip_v()
            self._message.config(text="Up/down reversed. Check the pad again.", fg=WARN)

    def _save(self) -> None:
        h, v = self._weights
        if self._pad.flip_h < 0:
            h = tuple(-x for x in h)
        if self._pad.flip_v < 0:
            v = tuple(-x for x in v)
        file = save_gyro_axes(self._config.gyro_profile_path, h, v)
        self.saved = True
        self._message.config(text=f"Saved to {file}. Keep testing, or close.", fg=GOOD)
        self._primary.config(text="Close")

    def close(self) -> None:
        if not self._alive:
            return
        self._alive = False
        if self._pad is not None:
            self._pad.close()
        self._source.stop(wait=True)
        try:
            self._root.destroy()
        except tk.TclError:
            pass

    # ------------------------------------------------------------ per frame

    def _tick(self) -> None:
        if not self._alive:
            return

        now = time.monotonic()
        elapsed = now - self._phase_start

        if self._phase == INTRO:
            self._update_intro()
        elif self._phase == COUNTDOWN and elapsed >= self._countdown_s:
            self._recorder.take()
            self._set_phase(CAPTURE)
        elif self._phase == CAPTURE and elapsed >= self._step.duration_s:
            self._finish_capture()

        self._draw_stage(now)
        if self._phase != TEST:
            self._draw_bars()
        self._update_labels()
        self._root.after(TICK_MS, self._tick)

    def _update_intro(self) -> None:
        ready = self._recorder.total >= 20
        self._primary.set_enabled(ready)
        if not ready:
            self._message.config(
                text=f"Connecting to {self._config.serial.port} ...", fg=MUTED)
        elif self._message.cget("text").startswith("Connecting"):
            self._message.config(text="Sensor connected.", fg=GOOD)

    def _update_labels(self) -> None:
        if self._phase in (COUNTDOWN, CAPTURE):
            step = self._step
            self._step_label.config(
                text=f"Step {self._step_index + 1} of {len(self._steps)}  ·  {step.title}")
            go = "GO!  " if self._phase == CAPTURE and step.countdown else ""
            self._instruction.config(text=go + step.instruction)
        elif self._phase == INTRO:
            self._step_label.config(text="Teaches the app which way your device moves")
            self._instruction.config(
                text="Hold the device the way you will when writing. Press Start, "
                     "then copy the motions shown on screen.")
        else:
            self._step_label.config(text="Last step  ·  write something to check it")
            self._instruction.config(
                text="Hold SPACE and move like you will when writing; hold E to draw. "
                     "Wrong direction? Press Flip. Happy? Save.")

    # ------------------------------------------------------------ drawing

    def _draw_stage(self, now: float) -> None:
        if self._phase == TEST:
            self._pad.update()
            return

        canvas = self._stage
        canvas.delete("all")
        kind = self._step.kind if self._phase in (COUNTDOWN, CAPTURE) else "still"
        phase = self._phase if self._phase in (COUNTDOWN, CAPTURE) else INTRO
        animations.draw(canvas, kind, now - self._phase_start, phase)

        if self._phase == COUNTDOWN:
            remaining = max(self._countdown_s - (now - self._phase_start), 0)
            canvas.create_text(60, 50, text=str(int(remaining) + 1), fill=ACCENT,
                               font=("Helvetica", 54, "bold"))
        elif self._phase == CAPTURE:
            fraction = min((now - self._phase_start) / self._step.duration_s, 1.0)
            canvas.create_rectangle(40, animations.H - 8, 40 + 520 * fraction,
                                    animations.H - 2, fill=GOOD, outline="")

    def _draw_bars(self) -> None:
        canvas = self._bars
        canvas.delete("all")
        row = self._recorder.latest
        rates = (0.0, 0.0, 0.0)
        if row is not None:
            rates = tuple(row[i + 1] / self._lsb - self._bias[i] for i in range(3))

        centre = animations.W / 2 + 20
        canvas.create_line(centre, 4, centre, 92, fill="#dee2e6", width=2)
        for i, (name, rate) in enumerate(zip(AXIS_NAMES, rates)):
            y = 20 + i * 28
            length = max(-1.0, min(1.0, rate / BAR_RANGE_DPS)) * 230
            canvas.create_text(40, y, text=name, font=("Helvetica", 12, "bold"), fill=INK)
            canvas.create_rectangle(
                centre, y - 9, centre + length, y + 9,
                fill=ACCENT if abs(rate) < 40 else GOOD, outline="")
            canvas.create_text(animations.W - 30, y, text=f"{rate:+.0f}",
                               font=("Helvetica", 11), fill=MUTED)


# ---------------------------------------------------------------- entry point

def run_calibration(config: AppConfig) -> bool:
    """Open the wizard on its own window. Returns True if a profile was saved."""
    recorder = Recorder()
    source = SerialSensorSource(config.serial, CsvSampleParser(config.serial))
    source.subscribe(recorder.on_sample)
    source.start()

    root = tk.Tk()
    wizard = CalibrationWizard(root, config, source, recorder)
    root.mainloop()
    return wizard.saved
