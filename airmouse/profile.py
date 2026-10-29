"""Per-device gyro axis profile, written by the calibration wizard."""

import json
from dataclasses import replace
from pathlib import Path
from typing import Optional, Sequence

from .config import AppConfig

# Anchored to the project folder, so the wizard and the app always agree on
# the file no matter which directory they are started from.
PROJECT_ROOT = Path(__file__).resolve().parent.parent


def resolve_profile_path(path: str) -> Path:
    p = Path(path)
    return p if p.is_absolute() else PROJECT_ROOT / p


def save_gyro_axes(path: str, h_weights: Sequence[float], v_weights: Sequence[float]) -> Path:
    file = resolve_profile_path(path)
    data = {"h_weights": list(h_weights), "v_weights": list(v_weights)}
    file.write_text(json.dumps(data, indent=2) + "\n")
    return file


def load_gyro_axes(path: str) -> Optional[dict]:
    file = resolve_profile_path(path)
    if not file.exists():
        return None
    try:
        data = json.loads(file.read_text())
        return {
            "h_weights": tuple(float(x) for x in data["h_weights"]),
            "v_weights": tuple(float(x) for x in data["v_weights"]),
        }
    except (ValueError, KeyError, TypeError) as error:
        print(f"Ignoring unreadable {file}: {error}")
        return None


def apply_gyro_profile(config: AppConfig) -> AppConfig:
    """Return `config` with the saved axis profile applied, if there is one."""
    axes = load_gyro_axes(config.gyro_profile_path)
    if axes is None:
        print("NO CALIBRATION FOUND: using default gyro axes. "
              "Run: python main.py --calibrate")
        return config

    fmt = lambda w: "(" + ", ".join(f"{x:+.2f}" for x in w) + ")"
    print(f"Loaded gyro axes from {resolve_profile_path(config.gyro_profile_path)}")
    print(f"  horizontal {fmt(axes['h_weights'])}   vertical {fmt(axes['v_weights'])}")
    return replace(config, gyro=replace(config.gyro, **axes))
