"""Small vector helpers for mapping the 3 gyro axes onto cursor directions."""

import math
from typing import Sequence, Tuple

Vec3 = Tuple[float, float, float]


def dot(a: Sequence[float], b: Sequence[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def norm(a: Sequence[float]) -> float:
    return math.sqrt(dot(a, a))


def unit(a: Sequence[float]) -> Vec3:
    n = norm(a)
    if n == 0:
        raise ValueError("zero-length vector")
    return tuple(x / n for x in a)  # type: ignore[return-value]


def fit_axes(right: Sequence[float], up: Sequence[float]) -> Tuple[Vec3, Vec3]:
    """From the net rotation measured for a 'right' swing and an 'up' swing,
    return (h_weights, v_weights): orthonormal directions such that
    dot(h_weights, gyro) is positive moving right, dot(v_weights, gyro)
    positive moving up. Raises ValueError if the two motions are the same
    rotation axis (cannot separate horizontal from vertical).
    """
    h = unit(right)
    along = dot(up, h)
    v_raw = tuple(u - along * hc for u, hc in zip(up, h))
    if norm(v_raw) < 0.25 * norm(up):
        raise ValueError("'right' and 'up' motions rotate about the same axis")
    return h, unit(v_raw)
