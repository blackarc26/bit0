import threading
from typing import List, Optional, Tuple

from ..sensor import Sample

Row = Tuple[float, float, float, float]   # (t, gx, gy, gz)


class Recorder:
    """Collects gyro rows from the sensor thread for the calibration code."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._rows: List[Row] = []
        self._latest: Optional[Row] = None
        self._total = 0

    def on_sample(self, sample: Sample) -> None:
        row = (sample.t, *sample.values[3:6])
        with self._lock:
            self._rows.append(row)
            self._latest = row
            self._total += 1

    def take(self) -> List[Row]:
        """Return and clear the rows collected since the last take()."""
        with self._lock:
            rows, self._rows = self._rows, []
        return rows

    @property
    def latest(self) -> Optional[Row]:
        with self._lock:
            return self._latest

    @property
    def total(self) -> int:
        """Samples received since start (never reset)."""
        with self._lock:
            return self._total
