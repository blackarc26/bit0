import threading
import time

import serial

from ..config import SerialConfig
from .base import SensorSource
from .parser import SampleParser


class SerialSensorSource(SensorSource):
    """Reads lines from a serial port on a background thread."""

    def __init__(self, config: SerialConfig, parser: SampleParser):
        super().__init__()
        self._config = config
        self._parser = parser
        self._stop_event = threading.Event()
        self._thread = None
        self._connected = False

    @property
    def connected(self) -> bool:
        return self._connected

    def start(self) -> None:
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self, wait: bool = False) -> None:
        self._stop_event.set()
        if wait and self._thread is not None:
            # Lets the port close before something else opens it.
            self._thread.join(timeout=self._config.read_timeout_s + 1.0)

    def _run(self) -> None:
        cfg = self._config
        try:
            with serial.Serial(
                cfg.port, cfg.baud_rate, timeout=cfg.read_timeout_s
            ) as port:
                self._stop_event.wait(cfg.startup_delay_s)
                port.reset_input_buffer()

                self._connected = True
                print("Connected to", cfg.port)

                while not self._stop_event.is_set():
                    line = port.readline().decode("utf-8", errors="ignore").strip()
                    if not line:
                        continue

                    sample = self._parser.parse(line, time.monotonic())
                    if sample is not None:
                        self._publish(sample)

        except (serial.SerialException, OSError) as error:
            print("Serial connection error:", error)

        finally:
            self._connected = False
