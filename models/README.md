# Pose model

Place the MediaPipe Pose Landmarker model bundle here. The project downloader saves the lite model as `pose_landmarker_lite.task`:

```bash
python scripts/download_model.py --variant lite
```

The `.task` model is intentionally ignored by Git. It is an inference model used by `src/pose_estimator.py`; it is not the UI-PRMD exercise dataset.
