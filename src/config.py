"""Load user-editable settings from the project's local .env file."""

import json
import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")


def _float_setting(name: str, default: float) -> float:
    value = os.getenv(name)
    return default if value is None or value.strip() == "" else float(value)


def _int_setting(name: str, default: int) -> int:
    value = os.getenv(name)
    return default if value is None or value.strip() == "" else int(value)


def _research_thresholds() -> dict[str, float]:
    """Read the active default values transcribed from the research notes."""
    rules_path = PROJECT_ROOT / "data" / "research_rules.json"
    with rules_path.open("r", encoding="utf-8") as rules_file:
        research_rules = json.load(rules_file)
    return research_rules["deep_squat"]["runtime_thresholds"]


@dataclass(frozen=True)
class Settings:
    """Runtime configuration shared by the video and display code."""

    camera_source: str
    model_path: Path
    serial_port: str | None
    baud_rate: int
    min_visibility: float
    calibration_frames: int
    min_squat_depth: float
    max_hip_drift: float
    max_head_drift: float


def load_settings() -> Settings:
    """Read settings while keeping file paths relative to the project root."""
    thresholds = _research_thresholds()
    raw_port = os.getenv("SERIAL_PORT", "").strip()
    raw_model = os.getenv("MODEL_PATH", "models/pose_landmarker_lite.task")
    model_path = Path(raw_model)
    if not model_path.is_absolute():
        model_path = PROJECT_ROOT / model_path

    return Settings(
        camera_source=os.getenv("CAMERA_SOURCE", "0").strip() or "0",
        model_path=model_path,
        serial_port=raw_port or None,
        baud_rate=_int_setting("BAUD_RATE", 115200),
        min_visibility=_float_setting("MIN_VISIBILITY", 0.45),
        calibration_frames=_int_setting("CALIBRATION_FRAMES", 30),
        min_squat_depth=_float_setting("MIN_SQUAT_DEPTH", thresholds["min_squat_depth"]),
        max_hip_drift=_float_setting("MAX_HIP_DRIFT", thresholds["max_hip_drift"]),
        max_head_drift=_float_setting("MAX_HEAD_DRIFT", thresholds["max_head_drift"]),
    )
