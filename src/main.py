"""Application entry point: video stream -> pose -> squat rules -> display."""

import argparse
from pathlib import Path

import cv2

from src.config import load_settings
from src.pose_estimator import PoseEstimator
from src.serial_display import SerialDisplay
from src.squat_counter import SquatCounter, measure_pose


# A compact set of links is enough to show that the detector found a full body.
SKELETON_LINKS = (
    (11, 13), (13, 15), (12, 14), (14, 16),
    (11, 23), (12, 24), (23, 25), (25, 27), (24, 26), (26, 28),
)


def _video_source(source: str):
    """Convert a numeric camera selector into an integer for OpenCV."""
    return int(source) if source.isdigit() else source


def _draw_pose(frame, landmarks) -> None:
    if landmarks is None:
        return
    height, width = frame.shape[:2]
    for start, end in SKELETON_LINKS:
        a, b = landmarks[start], landmarks[end]
        if (getattr(a, "visibility", 1.0) or 0.0) < 0.3 or (getattr(b, "visibility", 1.0) or 0.0) < 0.3:
            continue
        p1 = (int(a.x * width), int(a.y * height))
        p2 = (int(b.x * width), int(b.y * height))
        cv2.line(frame, p1, p2, (70, 220, 100), 2)
        cv2.circle(frame, p1, 4, (40, 180, 255), -1)
        cv2.circle(frame, p2, 4, (40, 180, 255), -1)


def _draw_status(frame, reps: int, status: str, feedback: str) -> None:
    color = (60, 220, 90) if status == "GOOD" else (30, 200, 255)
    cv2.rectangle(frame, (8, 8), (410, 112), (20, 20, 20), -1)
    cv2.putText(frame, f"Valid reps: {reps}", (20, 38), cv2.FONT_HERSHEY_SIMPLEX, 0.75, color, 2)
    cv2.putText(frame, f"State: {status}", (20, 68), cv2.FONT_HERSHEY_SIMPLEX, 0.62, color, 2)
    cv2.putText(frame, feedback[:42], (20, 96), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (245, 245, 245), 1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Track one person's deep-squat repetitions.")
    parser.add_argument("--source", help="Override CAMERA_SOURCE (camera index, video file, or MJPEG URL).")
    parser.add_argument("--headless", action="store_true", help="Run without opening an OpenCV preview window.")
    args = parser.parse_args()

    settings = load_settings()
    source = args.source or settings.camera_source
    capture = cv2.VideoCapture(_video_source(source))
    if not capture.isOpened():
        raise RuntimeError(f"Could not open video source: {source}")
    capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    counter = SquatCounter(
        calibration_frames=settings.calibration_frames,
        min_depth=settings.min_squat_depth,
        max_hip_drift=settings.max_hip_drift,
        max_head_drift=settings.max_head_drift,
    )
    display = SerialDisplay(settings.serial_port, settings.baud_rate)
    estimator = None
    print("Camera ready. Use a steady side view and hold an upright stance for calibration.")

    try:
        estimator = PoseEstimator(settings.model_path)
        while True:
            ok, frame = capture.read()
            if not ok:
                print("Video frame unavailable; stopping the stream loop.")
                break

            landmarks = estimator.detect(frame)
            if landmarks is None:
                snapshot = counter.no_pose()
            else:
                measurement = measure_pose(landmarks, settings.min_visibility)
                snapshot = counter.no_pose() if measurement is None else counter.update(measurement)

            display.send(snapshot.reps, snapshot.status, snapshot.feedback)
            if not args.headless:
                _draw_pose(frame, landmarks)
                _draw_status(frame, snapshot.reps, snapshot.status, snapshot.feedback)
                cv2.putText(frame, "Q: quit", (20, frame.shape[0] - 16), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)
                cv2.imshow("Team 27 Exercise Tracker", frame)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
    except KeyboardInterrupt:
        print("Stopping on keyboard interrupt.")
    finally:
        if estimator is not None:
            estimator.close()
        capture.release()
        display.close()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
