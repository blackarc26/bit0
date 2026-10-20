import threading
from typing import Optional, Tuple

from ..config import AppConfig, TiltConfig
from ..sensor.sample import Sample
from .base import MotionMapper
from .registry import register_mapper


class TiltMapper(MotionMapper):
    """Original v1 behaviour: accelerometer tilt drives a damped velocity."""

    def __init__(self, config: TiltConfig):
        self._cfg = config
        self._lock = threading.Lock()
        self._ax = 0.0
        self._ay = 0.0
        self._baseline_x: Optional[float] = None
        self._baseline_y: Optional[float] = None
        self._vx = 0.0
        self._vy = 0.0

    def on_sample(self, sample: Sample) -> None:
        with self._lock:
            self._ax = sample.values[self._cfg.accel_x_index]
            self._ay = sample.values[self._cfg.accel_y_index]

    def step(self, dt: float, enabled: bool) -> Tuple[float, float]:
        cfg = self._cfg

        with self._lock:
            ax, ay = self._ax, self._ay

        if self._baseline_x is None:
            self._baseline_x, self._baseline_y = ax, ay

        # Slowly follow the sensor's resting orientation.
        self._baseline_x += cfg.filter_strength * (ax - self._baseline_x)
        self._baseline_y += cfg.filter_strength * (ay - self._baseline_y)

        if not enabled:
            self._vx = self._vy = 0.0
            return 0.0, 0.0

        move_x = ax - self._baseline_x
        move_y = ay - self._baseline_y

        if abs(move_x) < cfg.deadzone:
            move_x = 0.0
        if abs(move_y) < cfg.deadzone:
            move_y = 0.0

        self._vx += move_x * cfg.sensitivity_x * dt
        self._vy += move_y * cfg.sensitivity_y * dt

        damping = cfg.velocity_damping ** (dt * 60)
        self._vx = self._clamp(self._vx * damping)
        self._vy = self._clamp(self._vy * damping)

        return self._vx * dt, self._vy * dt

    def _clamp(self, value: float) -> float:
        limit = self._cfg.max_speed
        return max(-limit, min(limit, value))


@register_mapper("tilt")
def _build(config: AppConfig) -> TiltMapper:
    return TiltMapper(config.tilt)
