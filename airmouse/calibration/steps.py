from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass(frozen=True)
class Step:
    """One stage of the calibration wizard (data only).

    kind     picks the on-screen animation (see animations.py)
    measure  "bias" = average idle reading, "rotation" = net swing angle,
             None = just wait (no measurement)
    """

    key: str
    title: str
    instruction: str
    kind: str
    measure: Optional[str]
    duration_s: float
    countdown: bool = True


DEFAULT_STEPS: Tuple[Step, ...] = (
    Step("still", "Hold still",
         "Hold the device still, the way you hold it when writing.",
         kind="still", measure="bias", duration_s=2.0),
    Step("right", "Swing right",
         "Move the device to the RIGHT the way you will when writing, then hold it there.",
         kind="right", measure="rotation", duration_s=2.5),
    Step("rest", "Return",
         "Bring the device back to the start position and hold still.",
         kind="still", measure=None, duration_s=2.0, countdown=False),
    Step("up", "Swing up",
         "Move the device UP the way you will when writing, then hold it there.",
         kind="up", measure="rotation", duration_s=2.5),
)
