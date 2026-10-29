import math
from typing import Sequence, Tuple

from .recorder import Row

MIN_ANGLE_DEG = 12.0
MIN_LOBE_DPS = 8.0        # a stroke must turn at least this fast to count
LOBE_FRACTION = 0.15      # ...and stay above this fraction of its peak speed
MAX_STEP_DT_S = 0.05
AXIS_NAMES = ("gx", "gy", "gz")

Vec3 = Tuple[float, float, float]


def mean_rate(rows: Sequence[Row], lsb_per_dps: float) -> Vec3:
    """Average gyro reading (deg/s) per axis: the sensor's idle bias."""
    n = max(len(rows), 1)
    return tuple(sum(r[i] for r in rows) / n / lsb_per_dps for i in (1, 2, 3))  # type: ignore[return-value]


def net_rotation(rows: Sequence[Row], bias: Vec3, lsb_per_dps: float) -> Vec3:
    """Integrate bias-corrected rate over time -> net rotation in degrees."""
    total = [0.0, 0.0, 0.0]
    for prev, cur in zip(rows, rows[1:]):
        dt = min(cur[0] - prev[0], MAX_STEP_DT_S)
        for i in range(3):
            total[i] += (cur[i + 1] / lsb_per_dps - bias[i]) * dt
    return tuple(total)  # type: ignore[return-value]


def stroke_rotation(rows: Sequence[Row], bias: Vec3, lsb_per_dps: float) -> Vec3:
    """Rotation (degrees per axis) of the main stroke only.

    Finds the fastest moment, then integrates just the stretch around it that
    keeps turning the same way. A slow return swing or hand wobble afterwards
    therefore cannot cancel or reverse the result, which a plain sum can.
    """
    samples = []
    for prev, cur in zip(rows, rows[1:]):
        dt = min(cur[0] - prev[0], MAX_STEP_DT_S)
        rate = tuple(cur[i + 1] / lsb_per_dps - bias[i] for i in range(3))
        samples.append((rate, dt))
    if not samples:
        return (0.0, 0.0, 0.0)

    peak_index = max(range(len(samples)), key=lambda i: sum(x * x for x in samples[i][0]))
    peak = samples[peak_index][0]
    peak_speed = math.sqrt(sum(x * x for x in peak))
    if peak_speed == 0:
        return (0.0, 0.0, 0.0)
    direction = tuple(x / peak_speed for x in peak)

    floor = max(MIN_LOBE_DPS, LOBE_FRACTION * peak_speed)

    def along(i: int) -> float:
        return sum(a * b for a, b in zip(samples[i][0], direction))

    first = peak_index
    while first > 0 and along(first - 1) > floor:
        first -= 1
    last = peak_index
    while last < len(samples) - 1 and along(last + 1) > floor:
        last += 1

    total = [0.0, 0.0, 0.0]
    for i in range(first, last + 1):
        rate, dt = samples[i]
        for k in range(3):
            total[k] += rate[k] * dt
    return tuple(total)  # type: ignore[return-value]


def describe(vec: Sequence[float]) -> str:
    return "  ".join(f"{n} {v:+.0f}°" for n, v in zip(AXIS_NAMES, vec))
