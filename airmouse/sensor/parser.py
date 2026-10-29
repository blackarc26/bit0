from abc import ABC, abstractmethod
from typing import Optional

from ..config import SerialConfig
from .sample import Sample


class SampleParser(ABC):
    """Turns one line of device output into a Sample (or None if invalid)."""

    @abstractmethod
    def parse(self, line: str, t: float) -> Optional[Sample]:
        ...


class CsvSampleParser(SampleParser):
    """Parses "ax,ay,az,gx,gy,gz" or "ax,ay,az,gx,gy,gz,micros".

    The optional 7th field is the device's own micros() clock. When present
    it replaces the host time, which is jittery over USB serial, so the
    integration uses the true spacing between samples.
    """

    VALUE_COUNT = 6
    WRAP = 2 ** 32          # micros() is an unsigned 32-bit counter

    def __init__(self, config: SerialConfig):
        self._threshold = config.raw_accel_threshold
        self._lsb_per_g = config.accel_lsb_per_g
        self._last_us: Optional[int] = None
        self._wraps = 0

    def _device_seconds(self, micros: int) -> float:
        if self._last_us is not None and micros < self._last_us - self.WRAP // 2:
            self._wraps += 1
        self._last_us = micros
        return (micros + self._wraps * self.WRAP) / 1e6

    def parse(self, line: str, t: float) -> Optional[Sample]:
        parts = line.split(",")
        if len(parts) not in (self.VALUE_COUNT, self.VALUE_COUNT + 1):
            return None

        try:
            numbers = [float(p) for p in parts]
        except ValueError:
            return None

        values = numbers[: self.VALUE_COUNT]
        if len(numbers) == self.VALUE_COUNT + 1:
            t = self._device_seconds(int(numbers[-1]))

        # Raw MPU6050 accelerometer counts -> g.
        if max(abs(v) for v in values[:3]) > self._threshold:
            values[:3] = [v / self._lsb_per_g for v in values[:3]]

        return Sample(values=tuple(values), t=t)
