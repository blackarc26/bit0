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
    """Parses "ax,ay,az,gx,gy,gz"."""

    FIELD_COUNT = 6

    def __init__(self, config: SerialConfig):
        self._threshold = config.raw_accel_threshold
        self._lsb_per_g = config.accel_lsb_per_g

    def parse(self, line: str, t: float) -> Optional[Sample]:
        parts = line.split(",")
        if len(parts) != self.FIELD_COUNT:
            return None

        try:
            values = [float(p) for p in parts]
        except ValueError:
            return None

        # Raw MPU6050 accelerometer counts -> g.
        if max(abs(v) for v in values[:3]) > self._threshold:
            values[:3] = [v / self._lsb_per_g for v in values[:3]]

        return Sample(values=tuple(values), t=t)
