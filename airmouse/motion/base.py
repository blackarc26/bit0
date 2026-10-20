from abc import ABC, abstractmethod
from typing import Tuple

from ..sensor.sample import Sample


class MotionMapper(ABC):
    """Converts sensor samples into cursor movement in pixels.

    on_sample() is called from the sensor thread; step() from the UI thread.
    """

    @abstractmethod
    def on_sample(self, sample: Sample) -> None:
        ...

    @abstractmethod
    def step(self, dt: float, enabled: bool) -> Tuple[float, float]:
        """Return (dx, dy) in pixels to move now. (0, 0) when disabled."""

    @property
    def ready(self) -> bool:
        """False while the mapper cannot produce movement (e.g. calibrating)."""
        return True

    def recalibrate(self) -> None:
        """Re-zero the mapper. No-op unless the mapper needs it."""
