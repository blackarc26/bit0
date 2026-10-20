import threading
from typing import List, Tuple

from ..config import AppConfig, GyroConfig
from ..sensor.sample import Sample
from .base import MotionMapper
from .registry import register_mapper


class GyroMapper(MotionMapper):
    """Wrist rotation -> cursor movement (air-mouse / pen style).

    Rotation rate is integrated per sensor sample, so no motion is lost
    between UI ticks. The gyro bias is measured at start-up (and on
    recalibrate()) while the device is held still.
    """

    def __init__(self, config: GyroConfig):
        self._cfg = config
        self._lock = threading.Lock()
        self._reset()

    def _reset(self) -> None:
        self._calibrating = True
        self._cal_buffer: List[Tuple[float, float]] = []
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
        h = sample.values[cfg.h_index] / cfg.lsb_per_dps
        v = sample.values[cfg.v_index] / cfg.lsb_per_dps

        with self._lock:
            dt = 0.0 if self._last_t is None else min(
                sample.t - self._last_t, cfg.max_sample_dt_s
            )
            self._last_t = sample.t

            if self._calibrating:
                self._finish_calibration_if_done(h, v)
                return

            self._track_bias(h, v)
            h -= self._bias[0]
            v -= self._bias[1]

            for i, raw in enumerate((h, v)):
                self._rate[i] += (1 - cfg.smoothing) * (raw - self._rate[i])
                rate = self._rate[i]
                if abs(rate) > cfg.deadzone_dps:
                    self._pending[i] += rate * dt * cfg.pixels_per_degree

    def _track_bias(self, h: float, v: float) -> None:
        """Slowly follow the bias while the device is (nearly) still."""
        cfg = self._cfg
        if (
            abs(h - self._bias[0]) < cfg.still_threshold_dps
            and abs(v - self._bias[1]) < cfg.still_threshold_dps
        ):
            self._bias = (
                self._bias[0] + cfg.bias_adapt * (h - self._bias[0]),
                self._bias[1] + cfg.bias_adapt * (v - self._bias[1]),
            )

    def _finish_calibration_if_done(self, h: float, v: float) -> None:
        self._cal_buffer.append((h, v))
        n = len(self._cal_buffer)
        if n < self._cfg.calibration_samples:
            return

        self._bias = (
            sum(c[0] for c in self._cal_buffer) / n,
            sum(c[1] for c in self._cal_buffer) / n,
        )
        self._calibrating = False
        self._cal_buffer = []
        print(f"Gyro calibrated (bias H {self._bias[0]:+.2f}, V {self._bias[1]:+.2f})")

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
