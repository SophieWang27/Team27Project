"""Measure simple 2D deep-squat repetitions and give rule-based feedback."""

import os
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
        max_head_drift: float = 0.04,
        start_fraction: float = 0.10,
        smoothing: float = 0.5,
    ) -> None:
        self.calibration_frames = max(1, calibration_frames)
        self.min_depth = min_depth
        self.max_hip_drift = max_hip_drift
        self.max_head_drift = max_head_drift
        # Hysteresis: a rep starts when the hips drop past start_fraction and ends
        # when they come back within max_hip_drift of the standing baseline.
        self.start_fraction = max(start_fraction, max_hip_drift * 2)
        # Exponential moving average to damp MediaPipe's frame-to-frame jitter.
        self.smoothing = min(1.0, max(0.05, smoothing))
        self._smoothed: Measurement | None = None
        self._implausible = 0
        self._calibration: deque[Measurement] = deque(maxlen=self.calibration_frames)
        self._baseline: Measurement | None = None
        self._descending = False
        self._peak_depth = 0.0
        self._reps = 0
        self._last_outcome = RepStatus(0, "CALIBRATING", "Stand upright and hold still", "CALIBRATING")

    @property
    def reps(self) -> int:
        """Number of valid repetitions completed in this session."""
        return self._reps

    def reset_tracking(self) -> None:
        """Recalibrate and clear a partial rep while keeping the completed count."""
        self._calibration.clear()
        self._baseline = None
        self._smoothed = None
        self._implausible = 0
        self._descending = False
        self._peak_depth = 0.0
        self._last_outcome = RepStatus(
            self._reps, "CALIBRATING", "Stand upright and hold still", "CALIBRATING"
        )

    def _smooth(self, m: Measurement) -> Measurement:
        """Blend each new reading with the previous one (noise handling)."""
        prev = self._smoothed
        if prev is None:
            self._smoothed = m
            return m
        a = self.smoothing
        self._smoothed = Measurement(
            nose_y=a * m.nose_y + (1 - a) * prev.nose_y,
            hip_y=a * m.hip_y + (1 - a) * prev.hip_y,
            ankle_y=a * m.ankle_y + (1 - a) * prev.ankle_y,
            stature=a * m.stature + (1 - a) * prev.stature,
        )
        return self._smoothed

    def update(self, measurement: Measurement) -> RepStatus:
        """Update the repetition state machine with one visible pose."""
        measurement = self._smooth(measurement)
        if self._baseline is None:
            self._calibration.append(measurement)
            if len(self._calibration) < self.calibration_frames:
                return RepStatus(self._reps, "CALIBRATING", "Stand upright and hold still", "CALIBRATING")
            # Only accept a reference taken while the person is whole-body, large
            # enough and standing still; otherwise keep sliding the window and wait.
            hips = [m.hip_y for m in self._calibration]
            stats = [m.stature for m in self._calibration]
            still = (max(hips) - min(hips)) < 0.03 and (max(stats) - min(stats)) < 0.05
            if mean(stats) < 0.35 or not still:
                return RepStatus(self._reps, "CALIBRATING", "Stand fully in view, still", "CALIBRATING")
            self._baseline = Measurement(
                nose_y=mean(item.nose_y for item in self._calibration),
                hip_y=mean(item.hip_y for item in self._calibration),
                ankle_y=mean(item.ankle_y for item in self._calibration),
                stature=mean(item.stature for item in self._calibration),
            )
            self._last_outcome = RepStatus(self._reps, "READY", "Reference set; begin squat", "READY")
            return self._last_outcome

        displacement = (measurement.hip_y - self._baseline.hip_y) / self._baseline.stature
        # A real squat never moves the hips more than ~60% of body height. If it
        # persists, the reference is stale (person or camera moved): recalibrate.
        if displacement > 0.6 or displacement < -0.25:
            self._implausible += 1
            if self._implausible >= 15:
                self._implausible = 0
                self.reset_tracking()
                return self._last_outcome
        else:
            self._implausible = 0
        if os.environ.get("SQUAT_DEBUG"):
            self._dbg = getattr(self, "_dbg", 0) + 1
            if self._dbg % 3 == 0:
                print(f"[squat] hip drop {displacement * 100:5.1f}% | need {self.start_fraction * 100:.0f}% to start, "
                      f"{self.min_depth * 100:.1f}% to count | descending={self._descending}")
        if not self._descending:
            if displacement >= self.start_fraction:
                self._descending = True
                self._peak_depth = displacement
                return RepStatus(self._reps, "DESCENDING", "Lower with control", "DESCENDING")
            return self._last_outcome

        self._peak_depth = max(self._peak_depth, displacement)
        if displacement > self.max_hip_drift:
            return RepStatus(self._reps, "DESCENDING", "Return to standing", "DESCENDING", self._peak_depth)

        # Hips are back near the starting height: the repetition is finished.
        head_drift = abs(measurement.nose_y - self._baseline.nose_y) / self._baseline.stature
        depth = self._peak_depth
        self._descending = False
        if os.environ.get("SQUAT_DEBUG"):
            print(f"[squat] REP END: peak depth {depth * 100:.1f}% (need {self.min_depth * 100:.1f}%), "
                  f"head drift {head_drift * 100:.1f}% (max {self.max_head_drift * 100:.1f}%)")

        if depth < self.min_depth:
            self._last_outcome = RepStatus(self._reps, "DEPTH", "Squat deeper", "READY", depth)
        elif head_drift > self.max_head_drift:
            self._last_outcome = RepStatus(self._reps, "HEAD", "Finish upright", "READY", depth)
        else:
            self._reps += 1
            self._last_outcome = RepStatus(self._reps, "GOOD", "Good repetition", "READY", depth)
        self._peak_depth = 0.0
        return self._last_outcome

    def no_pose(self) -> RepStatus:
        """Pause feedback and discard a partly observed repetition."""
        if os.environ.get("SQUAT_DEBUG"):
            print("[squat] NO POSE: head, hips or ankles not visible enough this frame")
        if self._descending:
            self._descending = False
            self._peak_depth = 0.0
        status = "NO_POSE" if self._baseline is not None else "CALIBRATING"
        message = "Move fully into camera view" if self._baseline is not None else "Stand upright in camera view"
        return RepStatus(self._reps, status, message, "READY" if self._baseline else "CALIBRATING")
