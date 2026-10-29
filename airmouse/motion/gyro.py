import math
import threading
from typing import List, Optional, Tuple

from ..config import AppConfig, GyroConfig
from ..sensor.sample import Sample
from .axes import dot
from .base import MotionMapper
from .registry import register_mapper


class GyroMapper(MotionMapper):
    """Wrist rotation -> cursor movement (air-mouse / pen style).

    Rotation rate is integrated per sensor sample, so no motion is lost
    between UI ticks. The gyro bias is measured while the device is held
    still, at start-up and on recalibrate().
    """

    def __init__(self, config: GyroConfig):
        self._cfg = config
        self._lock = threading.Lock()
        self._reset()

    def _reset(self) -> None:
        self._calibrating = True
        self._cal_buffer: List[Tuple[float, float]] = []
        self._cal_seen = 0
        self._cal_best: Optional[Tuple[float, Tuple[float, float]]] = None
        self._bias = (0.0, 0.0)
        self._rate = [0.0, 0.0]
        self._pending = [0.0, 0.0]
        self._last_t = None

    @property
    def ready(self) -> bool:
        return not self._calibrating

    def recalibrate(self) -> None:
        with self._lock:
            self._reset()
        print("Recalibrating gyro - hold still")

    def on_sample(self, sample: Sample) -> None:
        cfg = self._cfg
        gyro = [g / cfg.lsb_per_dps for g in sample.values[3:6]]
        h = dot(cfg.h_weights, gyro)
        v = dot(cfg.v_weights, gyro)

        with self._lock:
            dt = 0.0 if self._last_t is None else min(
                sample.t - self._last_t, cfg.max_sample_dt_s
            )
            self._last_t = sample.t

            if self._calibrating:
                self._calibrate(h, v)
                return

            self._track_bias(h, v)
            h -= self._bias[0]
            v -= self._bias[1]

            self._rate[0] += (1 - cfg.smoothing) * (h - self._rate[0])
            self._rate[1] += (1 - cfg.smoothing) * (v - self._rate[1])

            # Radial deadzone: judged on the combined speed, so slow diagonal
            # strokes keep their angle instead of snapping to one axis.
            if math.hypot(*self._rate) > cfg.deadzone_dps:
                self._pending[0] += self._rate[0] * dt * cfg.pixels_per_degree
                self._pending[1] += self._rate[1] * dt * cfg.pixels_per_degree

    def _track_bias(self, h: float, v: float) -> None:
        """Slowly follow the bias while the device is (nearly) still."""
        cfg = self._cfg
        if math.hypot(h - self._bias[0], v - self._bias[1]) < cfg.still_threshold_dps:
            self._bias = (
                self._bias[0] + cfg.bias_adapt * (h - self._bias[0]),
                self._bias[1] + cfg.bias_adapt * (v - self._bias[1]),
            )

    def _calibrate(self, h: float, v: float) -> None:
        """Slide a window over the incoming samples and accept the first one
        in which the device really was still. If it never is, fall back to
        the stillest window seen, so calibration cannot get stuck."""
        cfg = self._cfg
        window = cfg.calibration_samples

        self._cal_buffer.append((h, v))
        self._cal_seen += 1
        if len(self._cal_buffer) > window:
            self._cal_buffer.pop(0)
        if len(self._cal_buffer) < window:
            return

        mean_h = sum(c[0] for c in self._cal_buffer) / window
        mean_v = sum(c[1] for c in self._cal_buffer) / window
        spread = max(math.hypot(c[0] - mean_h, c[1] - mean_v) for c in self._cal_buffer)

        if self._cal_best is None or spread < self._cal_best[0]:
            self._cal_best = (spread, (mean_h, mean_v))

        if spread <= cfg.calibration_still_dps:
            self._finish_calibration((mean_h, mean_v), spread)
        elif self._cal_seen >= 5 * window:
            best_spread, best_bias = self._cal_best
            print("Could not hold still long enough; using the stillest moment.")
            self._finish_calibration(best_bias, best_spread)

    def _finish_calibration(self, bias: Tuple[float, float], spread: float) -> None:
        self._bias = bias
        self._calibrating = False
        self._cal_buffer = []
        print(f"Gyro calibrated (bias H {bias[0]:+.2f}, V {bias[1]:+.2f}, "
              f"steadiness {spread:.1f} dps)")

    def step(self, dt: float, enabled: bool) -> Tuple[float, float]:
        with self._lock:
            dx, dy = self._pending
            self._pending = [0.0, 0.0]
            ready = not self._calibrating

        if not (enabled and ready):
            return 0.0, 0.0

        if self._cfg.invert_h:
            dx = -dx
        if self._cfg.invert_v:
            dy = -dy
        return dx, dy


@register_mapper("gyro")
def _build(config: AppConfig) -> GyroMapper:
    return GyroMapper(config.gyro)
