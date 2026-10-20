"""All tunable settings. Pure data: no behaviour lives here."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class SerialConfig:
    port: str = "/dev/cu.usbserial-110"
    baud_rate: int = 115200
    startup_delay_s: float = 2.0
    read_timeout_s: float = 1.0
    # Raw MPU6050 accelerometer counts are converted to g when any of the
    # first three values exceeds this threshold.
    raw_accel_threshold: float = 10.0
    accel_lsb_per_g: float = 16384.0


@dataclass(frozen=True)
class GyroConfig:
    # Indices into the line "ax,ay,az,gx,gy,gz".
    h_index: int = 5               # gz (yaw)   -> cursor left/right
    v_index: int = 4               # gy (pitch) -> cursor up/down
    invert_h: bool = False
    invert_v: bool = False
    # 1.0 when firmware sends deg/s; 131.0 for raw MPU6050 counts (+-250 dps).
    lsb_per_dps: float = 1.0
    pixels_per_degree: float = 18.0
    deadzone_dps: float = 1.0
    smoothing: float = 0.35        # 0 = raw, towards 1 = smoother but laggier
    # While the device is nearly still, the bias keeps adapting so slow
    # sensor drift cannot make the cursor float.
    still_threshold_dps: float = 2.0
    bias_adapt: float = 0.005
    calibration_samples: int = 200
    max_sample_dt_s: float = 0.05


@dataclass(frozen=True)
class TiltConfig:
    accel_x_index: int = 0
    accel_y_index: int = 1
    sensitivity_x: float = 12000
    sensitivity_y: float = 12000
    deadzone: float = 0.025
    filter_strength: float = 0.08
    velocity_damping: float = 0.96
    max_speed: float = 2500


@dataclass(frozen=True)
class CursorConfig:
    invert_x: bool = False
    invert_y: bool = True


@dataclass(frozen=True)
class StrokeConfig:
    min_points: int = 3


@dataclass(frozen=True)
class OverlayConfig:
    enabled: bool = False          # off while the test whiteboard is in use
    colour: str = "#ff3355"
    width: int = 4
    fade_after_s: float = 2.0
    transparent_colour: str = "#010101"


@dataclass(frozen=True)
class WhiteboardConfig:
    enabled: bool = True
    width: int = 900
    height: int = 640
    x: int = 520          # sits to the right of the control panel
    y: int = 60
    background: str = "#fafafa"
    colours: tuple = ("#1e1e1e", "#e03131", "#2f9e44", "#1971c2", "#f08c00")
    widths: tuple = (2, 4, 8)


@dataclass(frozen=True)
class AppConfig:
    motion_mode: str = "gyro"      # any name registered in airmouse.motion
    update_ms: int = 10
    max_dt_s: float = 0.05
    # "auto" = Tk on macOS (pynput aborts there), pynput elsewhere.
    # "tk" only sees keys while the app's own windows have focus.
    keyboard_backend: str = "auto"

    serial: SerialConfig = field(default_factory=SerialConfig)
    gyro: GyroConfig = field(default_factory=GyroConfig)
    tilt: TiltConfig = field(default_factory=TiltConfig)
    cursor: CursorConfig = field(default_factory=CursorConfig)
    strokes: StrokeConfig = field(default_factory=StrokeConfig)
    overlay: OverlayConfig = field(default_factory=OverlayConfig)
    whiteboard: WhiteboardConfig = field(default_factory=WhiteboardConfig)
