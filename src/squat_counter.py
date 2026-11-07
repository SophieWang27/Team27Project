"""Measure simple 2D deep-squat repetitions and give rule-based feedback."""

from collections import deque
from dataclasses import dataclass
from statistics import mean


# MediaPipe Pose landmark indices: nose, hips, and ankles.
NOSE = 0
LEFT_HIP = 23
RIGHT_HIP = 24
LEFT_ANKLE = 27
RIGHT_ANKLE = 28


@dataclass(frozen=True)
class Measurement:
    """Image-normalized vertical points used by the squat rule."""

    nose_y: float
    hip_y: float
    ankle_y: float
    stature: float


@dataclass(frozen=True)
class RepStatus:
    """State shown on the preview and sent to the Arduino."""

    reps: int
    status: str
    feedback: str
    phase: str
    depth_fraction: float | None = None


def _visible_y(landmarks, indices: tuple[int, ...], min_visibility: float) -> float | None:
    values = []
    for index in indices:
        landmark = landmarks[index]
        visibility = getattr(landmark, "visibility", None)
        if visibility is None or visibility >= min_visibility:
            values.append(float(landmark.y))
    return mean(values) if values else None


def measure_pose(landmarks, min_visibility: float) -> Measurement | None:
    """Extract nose, hip-center, ankle-center, and apparent standing height."""
    nose_y = _visible_y(landmarks, (NOSE,), min_visibility)
    hip_y = _visible_y(landmarks, (LEFT_HIP, RIGHT_HIP), min_visibility)
    ankle_y = _visible_y(landmarks, (LEFT_ANKLE, RIGHT_ANKLE), min_visibility)
    if nose_y is None or hip_y is None or ankle_y is None:
        return None

    stature = abs(ankle_y - nose_y)
    if stature < 0.1:
        return None
    return Measurement(nose_y=nose_y, hip_y=hip_y, ankle_y=ankle_y, stature=stature)


class SquatCounter:
    """Calibrate a standing pose, then count only repetitions passing all rules."""

    def __init__(
        self,
        calibration_frames: int = 30,
        min_depth: float = 0.291,
        max_hip_drift: float = 0.005,
        max_head_drift: float = 0.00169,
        start_fraction: float = 0.05,
        return_fraction: float = 0.08,
    ) -> None:
        self.calibration_frames = max(1, calibration_frames)
        self.min_depth = min_depth
        self.max_hip_drift = max_hip_drift
        self.max_head_drift = max_head_drift
        self.start_fraction = start_fraction
        self.return_fraction = return_fraction
        self._calibration: deque[Measurement] = deque(maxlen=self.calibration_frames)
        self._baseline: Measurement | None = None
        self._descending = False
        self._peak_depth = 0.0
        self._reps = 0
        self._last_outcome = RepStatus(0, "CALIBRATING", "Stand upright and hold still", "CALIBRATING")

    def update(self, measurement: Measurement) -> RepStatus:
        """Update the repetition state machine with one visible pose."""
        if self._baseline is None:
            self._calibration.append(measurement)
            if len(self._calibration) < self.calibration_frames:
                return RepStatus(self._reps, "CALIBRATING", "Stand upright and hold still", "CALIBRATING")
            self._baseline = Measurement(
                nose_y=mean(item.nose_y for item in self._calibration),
                hip_y=mean(item.hip_y for item in self._calibration),
                ankle_y=mean(item.ankle_y for item in self._calibration),
                stature=mean(item.stature for item in self._calibration),
            )
            self._last_outcome = RepStatus(self._reps, "READY", "Reference set; begin squat", "READY")
            return self._last_outcome

        displacement = (measurement.hip_y - self._baseline.hip_y) / self._baseline.stature
        if not self._descending:
            if displacement >= self.start_fraction:
                self._descending = True
                self._peak_depth = displacement
                return RepStatus(self._reps, "DESCENDING", "Lower with control", "DESCENDING")
            return self._last_outcome

        self._peak_depth = max(self._peak_depth, displacement)
        if displacement > self.return_fraction:
            return RepStatus(self._reps, "DESCENDING", "Return to standing", "DESCENDING", self._peak_depth)

        hip_drift = abs(measurement.hip_y - self._baseline.hip_y) / self._baseline.stature
        head_drift = abs(measurement.nose_y - self._baseline.nose_y) / self._baseline.stature
        depth = self._peak_depth
        self._descending = False

        if depth < self.min_depth:
            self._last_outcome = RepStatus(self._reps, "DEPTH", "Squat deeper", "READY", depth)
        elif hip_drift > self.max_hip_drift:
            self._last_outcome = RepStatus(self._reps, "HIPS", "Return to your starting position", "READY", depth)
        elif head_drift > self.max_head_drift:
            self._last_outcome = RepStatus(self._reps, "HEAD", "Finish upright", "READY", depth)
        else:
            self._reps += 1
            self._last_outcome = RepStatus(self._reps, "GOOD", "Good repetition", "READY", depth)
        self._peak_depth = 0.0
        return self._last_outcome

    def no_pose(self) -> RepStatus:
        """Pause feedback and discard a partly observed repetition."""
        if self._descending:
            self._descending = False
            self._peak_depth = 0.0
        status = "NO_POSE" if self._baseline is not None else "CALIBRATING"
        message = "Move fully into camera view" if self._baseline is not None else "Stand upright in camera view"
        return RepStatus(self._reps, status, message, "READY" if self._baseline else "CALIBRATING")
