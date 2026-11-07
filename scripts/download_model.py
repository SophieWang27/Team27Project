"""Download an official MediaPipe Pose Landmarker model bundle."""

import argparse
from pathlib import Path
from urllib.request import urlopen


MODEL_URLS = {
    "lite": "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task",
    "full": "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_full/float16/1/pose_landmarker_full.task",
}


def download(url: str, output_path: Path) -> None:
    """Stream the model to disk so it does not need to fit in memory."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = output_path.with_suffix(output_path.suffix + ".part")
    try:
        with urlopen(url, timeout=60) as response, temporary_path.open("wb") as target:
            while chunk := response.read(1024 * 1024):
                target.write(chunk)
        temporary_path.replace(output_path)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()


def main() -> None:
    parser = argparse.ArgumentParser(description="Download a MediaPipe Pose Landmarker .task model.")
    parser.add_argument("--variant", choices=MODEL_URLS, default="lite", help="lite is the recommended first model.")
    args = parser.parse_args()
    filename = f"pose_landmarker_{args.variant}.task"
    output_path = Path(__file__).resolve().parents[1] / "models" / filename
    print(f"Downloading {args.variant} model to {output_path} ...")
    download(MODEL_URLS[args.variant], output_path)
    print(f"Saved {output_path} ({output_path.stat().st_size:,} bytes).")


if __name__ == "__main__":
    main()
