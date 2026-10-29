"""Terminal version of the gyro calibration (the GUI wizard is nicer:
python -m airmouse.tools.calibrate_gui).

Run from the project folder, with the air-mouse app CLOSED (it owns the port):

    python -m airmouse.tools.axis_probe
"""

import time

from ..calibration.analysis import (
    AXIS_NAMES, MIN_ANGLE_DEG, describe, mean_rate, stroke_rotation,
)
from ..calibration.recorder import Recorder
from ..calibration.steps import DEFAULT_STEPS
from ..config import AppConfig
from ..motion.axes import fit_axes, norm
from ..profile import save_gyro_axes
from ..sensor import CsvSampleParser, SerialSensorSource


def countdown(text: str) -> None:
    print(f"\n{text}")
    for n in (3, 2, 1):
        print(f"  {n}...", flush=True)
        time.sleep(1)
    print("  GO!", flush=True)


def main() -> None:
    config = AppConfig()
    lsb = config.gyro.lsb_per_dps

    recorder = Recorder()
    source = SerialSensorSource(config.serial, CsvSampleParser(config.serial))
    source.subscribe(recorder.on_sample)
    source.start()

    print(f"Connecting to {config.serial.port} ...")
    deadline = time.time() + 15
    while time.time() < deadline and recorder.total < 20:
        time.sleep(0.2)
    if recorder.total < 20:
        print("No data. Close the air-mouse app / Serial Monitor and check the port.")
        source.stop(wait=True)
        return

    bias = (0.0, 0.0, 0.0)
    results = {}
    for step in DEFAULT_STEPS:
        while True:
            if step.countdown:
                countdown(f"{step.title}: {step.instruction}")
            else:
                print(f"\n{step.instruction}")
            recorder.take()
            time.sleep(step.duration_s)
            rows = recorder.take()

            if step.measure == "bias":
                bias = mean_rate(rows, lsb)
                print("  idle bias:", "  ".join(f"{v:+.2f}" for v in bias), "dps")
            elif step.measure == "rotation":
                rotation = stroke_rotation(rows, bias, lsb)
                print("  measured:", describe(rotation))
                if norm(rotation) < MIN_ANGLE_DEG:
                    print(f"  Too small (<{MIN_ANGLE_DEG:.0f}°). A gyro cannot feel sliding "
                          f"the device sideways, only rotating it. Try again.")
                    continue
                results[step.key] = rotation
            break

    source.stop(wait=True)

    try:
        h_weights, v_weights = fit_axes(results["right"], results["up"])
    except ValueError as error:
        print(f"\nCould not separate the motions: {error}.")
        return

    save_gyro_axes(config.gyro_profile_path, h_weights, v_weights)
    print(f"\nSaved {config.gyro_profile_path}")
    print("  horizontal:", "  ".join(f"{n} {w:+.2f}" for n, w in zip(AXIS_NAMES, h_weights)))
    print("  vertical:  ", "  ".join(f"{n} {w:+.2f}" for n, w in zip(AXIS_NAMES, v_weights)))


if __name__ == "__main__":
    main()
