"""Visual gyro calibration wizard.

    python -m airmouse.tools.calibrate_gui

Close the air-mouse app first: only one program can use the serial port.
"""

from ..calibration import run_calibration
from ..config import AppConfig

if __name__ == "__main__":
    saved = run_calibration(AppConfig())
    print("Calibration saved." if saved else "Calibration not saved.")
