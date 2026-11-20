"""Application entry point: video stream -> pose -> exercise rules -> display."""

import argparse
import time

import cv2

from src.config import load_settings
from src.exercise_modes import COUNT_LABELS, MODE_LABELS, MODE_ORDER, create_tracker
from src.pose_estimator import PoseEstimator
from src.serial_display import SerialDisplay


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


def _draw_status(
    frame,
    mode: str,
    completed: int,
    status: str,
    feedback: str,
    fps: float,
    depth_fraction: float | None,
    target_depth: float,
) -> None:
    color = (60, 220, 90) if status == "GOOD" else (30, 200, 255)
    cv2.rectangle(frame, (8, 8), (620, 190), (20, 20, 20), -1)
    cv2.putText(frame, f"Exercise: {MODE_LABELS[mode]}", (20, 34), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (245, 245, 245), 2)
    cv2.putText(frame, f"{COUNT_LABELS[mode]}: {completed}", (20, 64), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
    cv2.putText(frame, f"State: {status}", (20, 92), cv2.FONT_HERSHEY_SIMPLEX, 0.58, color, 2)
    cv2.putText(frame, feedback[:72], (20, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (245, 245, 245), 1)
    if mode == "deep_squat":
        depth_text = (
            f"Peak depth: {depth_fraction * 100:.1f}% / target {target_depth * 100:.1f}%"
            if depth_fraction is not None
            else f"Peak depth: waiting for descent / target {target_depth * 100:.1f}%"
        )
        cv2.putText(frame, depth_text, (20, 146), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (245, 245, 245), 1)
    cv2.putText(frame, "Keys 1-6: choose | N: next | Q: quit", (20, 168), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (220, 220, 220), 1)
    cv2.putText(frame, f"Processing: {fps:.1f} FPS", (20, 186), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (220, 220, 220), 1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Track one person's exercise repetitions and holds.")
    parser.add_argument("--source", help="Override CAMERA_SOURCE (camera index, video file, or MJPEG URL).")
    parser.add_argument("--headless", action="store_true", help="Run without opening an OpenCV preview window.")
    parser.add_argument(
        "--stats-interval",
        type=float,
        default=5.0,
        help="Seconds between terminal performance summaries (default: 5).",
    )
    args = parser.parse_args()
    if args.stats_interval <= 0:
        parser.error("--stats-interval must be greater than 0")

    settings = load_settings()
    source = args.source or settings.camera_source
    capture = cv2.VideoCapture(_video_source(source))
    if not capture.isOpened():
        capture.release()
        raise RuntimeError(f"Could not open video source: {source}")
    capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    trackers = {mode: create_tracker(mode, settings) for mode in MODE_ORDER}
    current_mode = MODE_ORDER[0]
    display = SerialDisplay(settings.serial_port, settings.baud_rate)
    estimator = None
    stats_frames = 0
    stats_pose_seconds = 0.0
    processing_fps = 0.0
    print("Camera ready. Keys 1-6 choose an exercise; N cycles to the next one; Q quits.")
    print("Start with a steady side view for squat, plank, curl, carry, and good morning.")

    try:
        estimator = PoseEstimator(settings.model_path)
        stats_started = time.perf_counter()
        while True:
            if display.poll_mode_change():
                mode_index = MODE_ORDER.index(current_mode)
                current_mode = MODE_ORDER[(mode_index + 1) % len(MODE_ORDER)]
                trackers[current_mode].reset_tracking()
                print(f"Selected {MODE_LABELS[current_mode]} using the hardware button.")

            ok, frame = capture.read()
            if not ok:
                print("Video frame unavailable; stopping the stream loop.")
                break

            pose_started = time.perf_counter()
            landmarks = estimator.detect(frame)
            pose_seconds = time.perf_counter() - pose_started
            stats_frames += 1
            stats_pose_seconds += pose_seconds

            stats_elapsed = time.perf_counter() - stats_started
            processing_fps = stats_frames / stats_elapsed
            if stats_elapsed >= args.stats_interval:
                average_pose_ms = stats_pose_seconds * 1000 / stats_frames
                height, width = frame.shape[:2]
                print(
                    f"Performance: {processing_fps:.1f} FPS; "
                    f"pose inference {average_pose_ms:.1f} ms/frame; "
                    f"camera frame {width}x{height}"
                )
                stats_started = time.perf_counter()
                stats_frames = 0
                stats_pose_seconds = 0.0
            tracker = trackers[current_mode]
            snapshot = tracker.no_pose() if landmarks is None else tracker.update(landmarks, settings.min_visibility)

            display.send(current_mode, snapshot.reps, snapshot.status, snapshot.feedback)
            if not args.headless:
                _draw_pose(frame, landmarks)
                _draw_status(
                    frame,
                    current_mode,
                    snapshot.reps,
                    snapshot.status,
                    snapshot.feedback,
                    processing_fps,
                    snapshot.depth_fraction,
                    settings.min_squat_depth,
                )
                cv2.putText(frame, "Q: quit", (20, frame.shape[0] - 16), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)
                cv2.imshow("Team 27 Exercise Tracker", frame)
                key = cv2.waitKey(1) & 0xFF
                if key in (ord("q"), ord("Q")):
                    break
                selection_requested = False
                if ord("1") <= key <= ord("6"):
                    selected_mode = MODE_ORDER[key - ord("1")]
                    selection_requested = True
                elif key in (ord("n"), ord("N")):
                    mode_index = MODE_ORDER.index(current_mode)
                    selected_mode = MODE_ORDER[(mode_index + 1) % len(MODE_ORDER)]
                    selection_requested = True
                else:
                    selected_mode = current_mode
                if selection_requested:
                    current_mode = selected_mode
                    trackers[current_mode].reset_tracking()
                    print(f"Selected {MODE_LABELS[current_mode]}; completed count kept, setup restarted.")
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
