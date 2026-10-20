from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class Sample:
    """One sensor reading: (ax, ay, az, gx, gy, gz) plus a monotonic timestamp.

    Accelerometer values are in g. Gyro values are in whatever unit the
    firmware sends; motion mappers apply their own scaling.
    """

    values: Tuple[float, ...]
    t: float
