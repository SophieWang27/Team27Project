"""Run MediaPipe's pretrained Pose Landmarker on incoming video frames."""

from pathlib import Path
import time

import cv2
import mediapipe as mp


class PoseEstimator:
    """Owns the MediaPipe task and returns normalized pose landmarks."""

    def __init__(self, model_path: Path) -> None:
        if not model_path.is_file():
            raise FileNotFoundError(
                f"Pose model not found at {model_path}. "
                "Run: python scripts/download_model.py --variant lite"
            )

        options = mp.tasks.vision.PoseLandmarkerOptions(
            # Explicit CPU avoids device-specific GPU delegate startup failures and
            # matches the Raspberry Pi Zero 2 W target for the first prototype.
            base_options=mp.tasks.BaseOptions(
                model_asset_path=str(model_path),
                delegate=mp.tasks.BaseOptions.Delegate.CPU,
            ),
            running_mode=mp.tasks.vision.RunningMode.VIDEO,
            num_poses=1,
            min_pose_detection_confidence=0.5,
            min_pose_presence_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        self._landmarker = mp.tasks.vision.PoseLandmarker.create_from_options(options)
        self._last_timestamp_ms = 0

    def detect(self, frame_bgr):
        """Return one list of landmarks, or None when no person was found."""
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
        timestamp_ms = max(time.monotonic_ns() // 1_000_000, self._last_timestamp_ms + 1)
        self._last_timestamp_ms = timestamp_ms
        result = self._landmarker.detect_for_video(image, timestamp_ms)
        if not result.pose_landmarks:
            return None
        return result.pose_landmarks[0]

    def close(self) -> None:
        """Release MediaPipe's native resources."""
        self._landmarker.close()
