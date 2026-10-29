import argparse

from airmouse.config import AppConfig
from airmouse.factory import build_app
from airmouse.profile import load_gyro_axes


def main() -> None:
    parser = argparse.ArgumentParser(description="MPU6050 air mouse")
    parser.add_argument("--calibrate", action="store_true",
                        help="run the gyro calibration wizard before starting")
    args = parser.parse_args()

    config = AppConfig()

    # First run (no saved profile) or explicit request: calibrate first.
    if args.calibrate or load_gyro_axes(config.gyro_profile_path) is None:
        from airmouse.calibration import run_calibration
        run_calibration(config)

    build_app(config).run()


if __name__ == "__main__":
    main()
