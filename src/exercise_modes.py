"""Selectable, rule-based exercise trackers for the Team 27 prototype.

The research-page values are used where they are specific enough. The notes do
not fully define every exercise's rep phases, so any extra endpoint or hold
duration in this module is called out as a prototype choice in the project docs.
"""

from __future__ import annotations

import math
import time
from statistics import mean

from src.squat_counter import RepStatus, SquatCounter, measure_pose


MODE_ORDER = (
    "deep_squat",
    "plank",
    "bicep_curl",
    "arm_rainbow",
    "farmers_carry",
    "good_morning",
)

MODE_LABELS = {
    "deep_squat": "Deep squat",
    "plank": "Plank hold",
    "bicep_curl": "Bicep curl",
    "arm_rainbow": "Arm rainbow",
    "farmers_carry": "Farmer's carry",
    "good_morning": "Good morning",
}

COUNT_LABELS = {
    "deep_squat": "Reps",
    "plank": "Completed holds",
    "bicep_curl": "Reps",
    "arm_rainbow": "Reps",
    "farmers_carry": "Completed carries",
    "good_morning": "Reps",
}

# The research notes give posture thresholds for the two timed exercises but no
# duration. Ten seconds is a short, adjustable demo duration, not a research value.
DEMO_HOLD_SECONDS = 10.0


def _visible_point(landmarks, index: int, min_visibility: float):
    if landmarks is None or index >= len(landmarks):
        return None
    landmark = landmarks[index]
    visibility = getattr(landmark, "visibility", 1.0)
    if visibility is not None and visibility < min_visibility:
        return None
    return float(landmark.x), float(landmark.y)


def _visibility(landmarks, index: int) -> float:
    if index >= len(landmarks):
        return 0.0
    value = getattr(landmarks[index], "visibility", 1.0)
    return 1.0 if value is None else float(value)


def _center(points):
    return mean(point[0] for point in points), mean(point[1] for point in points)


def _distance(a, b) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _angle(a, vertex, c) -> float | None:
    """Return the conventional 0-180 degree angle at vertex, or None."""
    va = (a[0] - vertex[0], a[1] - vertex[1])
    vc = (c[0] - vertex[0], c[1] - vertex[1])
    length_a = math.hypot(*va)
    length_c = math.hypot(*vc)
    if length_a < 1e-8 or length_c < 1e-8:
        return None
    cosine = (va[0] * vc[0] + va[1] * vc[1]) / (length_a * length_c)
    return math.degrees(math.acos(max(-1.0, min(1.0, cosine))))


def _best_visible_side(landmarks, sides, min_visibility: float):
    """Choose the best-visible complete side and return its points and score."""
    candidates = []
    for indices in sides:
        score = mean(_visibility(landmarks, index) for index in indices)
        if score < min_visibility:
            continue
        points = [_visible_point(landmarks, index, min_visibility) for index in indices]
        if all(point is not None for point in points):
            candidates.append((score, points))
    return max(candidates, key=lambda item: item[0])[1] if candidates else None


class DeepSquatMode:
    """Adapter that gives the existing research-based squat counter a common API."""

    def __init__(self, settings) -> None:
        self._settings = settings
        self._counter = self._new_counter()

    def _new_counter(self):
        return SquatCounter(
            calibration_frames=self._settings.calibration_frames,
            min_depth=self._settings.min_squat_depth,
            max_hip_drift=self._settings.max_hip_drift,
            max_head_drift=self._settings.max_head_drift,
        )

    def update(self, landmarks, min_visibility: float) -> RepStatus:
        measurement = measure_pose(landmarks, min_visibility)
        return self.no_pose() if measurement is None else self._counter.update(measurement)

    def no_pose(self) -> RepStatus:
        return self._counter.no_pose()

    def reset_tracking(self) -> None:
        self._counter.reset_tracking()


class BicepCurlCounter:
    """Count extended -> flexed -> extended arm cycles using the research endpoints."""

    SIDES = ((11, 13, 15), (12, 14, 16))

    def __init__(self, rule: dict) -> None:
        self.reps = 0
        self._armed = False
        self._curled = False
        angles = rule["angle_degrees"]
        self._extended_angle = angles["cue_go_up_above"]
        self._flexed_angle = angles["cue_go_down_below"]

    def update(self, landmarks, min_visibility: float) -> RepStatus:
        chosen = _best_visible_side(landmarks, self.SIDES, min_visibility)
        if chosen is None:
            return self.no_pose()
        angle = _angle(*chosen)
        if angle is None:
            return self.no_pose()

        # The research page gives >160 degrees as the extended endpoint and
        # <30 degrees as the flexed endpoint. A full repetition returns to >160.
        if angle > self._extended_angle:
            if self._curled:
                self.reps += 1
                self._curled = False
                self._armed = True
                return RepStatus(self.reps, "GOOD", "Curl completed", "READY")
            self._armed = True
            return RepStatus(self.reps, "READY", "Curl up toward your shoulder", "READY")
        if angle < self._flexed_angle and self._armed:
            self._curled = True
            return RepStatus(self.reps, "FLEXED", "Lower your arm with control", "FLEXED")
        if self._curled:
            return RepStatus(self.reps, "RETURN", "Straighten your arm to finish", "RETURN")
        if not self._armed:
            return RepStatus(self.reps, "START", "Start with your arm straight", "START")
        return RepStatus(self.reps, "MOVING", "Curl toward your shoulder", "MOVING")

    def no_pose(self) -> RepStatus:
        self._curled = False
        self._armed = False
        return RepStatus(self.reps, "NO_POSE", "Show one arm from shoulder to wrist", "READY")

    def reset_tracking(self) -> None:
        self._armed = False
        self._curled = False


class PlankHoldCounter:
    """Track a side-view plank angle and count a completed timed hold."""

    SIDES = ((11, 23, 27), (12, 24, 28))

    def __init__(self, rule: dict) -> None:
        self.completed = 0
        self._good_low, self._good_high = rule["prototype_rule"]["good_range_inclusive"]
        self.hold_seconds = rule["prototype_rule"].get("hold_seconds", DEMO_HOLD_SECONDS)
        self._started_at: float | None = None
        self._complete = False

    @property
    def reps(self) -> int:
        return self.completed

    def update(self, landmarks, min_visibility: float) -> RepStatus:
        chosen = _best_visible_side(landmarks, self.SIDES, min_visibility)
        if chosen is None:
            return self.no_pose()
        angle = _angle(*chosen)
        if angle is None:
            return self.no_pose()
        if angle < self._good_low:
            self._started_at = None
            self._complete = False
            return RepStatus(self.completed, "TOO_LOW", "Raise your hips; keep a straight line", "READY")
        if angle > self._good_high:
            self._started_at = None
            self._complete = False
            return RepStatus(self.completed, "TOO_HIGH", "Lower your hips into a straight line", "READY")
        if self._complete:
            return RepStatus(self.completed, "GOOD", "Hold complete; reset your plank", "COMPLETE")

        now = time.monotonic()
        if self._started_at is None:
            self._started_at = now
        elapsed = now - self._started_at
        if elapsed >= self.hold_seconds:
            self.completed += 1
            self._complete = True
            return RepStatus(self.completed, "GOOD", "Plank hold complete", "COMPLETE")
        return RepStatus(self.completed, "HOLDING", f"Hold steady: {elapsed:.0f}/{self.hold_seconds:.0f} sec", "HOLDING")

    def no_pose(self) -> RepStatus:
        self._started_at = None
        self._complete = False
        return RepStatus(self.completed, "NO_POSE", "Show your shoulder, hip, and ankle", "READY")

    def reset_tracking(self) -> None:
        self._started_at = None
        self._complete = False


class ArmRainbowCounter:
    """Prototype arm-raise/lower cycle; its thresholds are not in the research notes."""

    def __init__(self, rule: dict) -> None:
        self.reps = 0
        self._active_side: int | None = None
        self._raised = False
        thresholds = rule["prototype_thresholds"]
        self._raise_fraction = thresholds["wrist_above_shoulder_fraction_of_torso"]
        self._return_fraction = thresholds["wrist_below_shoulder_fraction_of_torso"]
        self._max_lean_fraction = thresholds["maximum_torso_lean_fraction"]

    def update(self, landmarks, min_visibility: float) -> RepStatus:
        left_shoulder = _visible_point(landmarks, 11, min_visibility)
        right_shoulder = _visible_point(landmarks, 12, min_visibility)
        left_hip = _visible_point(landmarks, 23, min_visibility)
        right_hip = _visible_point(landmarks, 24, min_visibility)
        if None in (left_shoulder, right_shoulder, left_hip, right_hip):
            return self.no_pose()
        shoulders = _center((left_shoulder, right_shoulder))
        hips = _center((left_hip, right_hip))
        torso_length = _distance(shoulders, hips)
        if torso_length < 0.05:
            return self.no_pose()
        if abs(shoulders[0] - hips[0]) / torso_length > self._max_lean_fraction:
            return RepStatus(self.reps, "POSTURE", "Stand upright and face the camera", "READY")

        wrists = (
            _visible_point(landmarks, 15, min_visibility),
            _visible_point(landmarks, 16, min_visibility),
        )
        if self._active_side is None:
            candidates = [
                (wrist[1] - shoulder[1], side)
                for side, (wrist, shoulder) in enumerate(zip(wrists, (left_shoulder, right_shoulder)))
                if wrist is not None and wrist[1] >= shoulder[1] + self._return_fraction * torso_length
            ]
            if not candidates:
                return RepStatus(self.reps, "START", "Lower one arm to begin", "READY")
            _, self._active_side = max(candidates)
            self._raised = False

        wrist = wrists[self._active_side]
        shoulder = (left_shoulder, right_shoulder)[self._active_side]
        if wrist is None:
            return self.no_pose()
        if not self._raised and wrist[1] <= shoulder[1] - self._raise_fraction * torso_length:
            self._raised = True
            return RepStatus(self.reps, "RAISED", "Sweep your arm back down", "RAISED")
        if self._raised and wrist[1] >= shoulder[1] + self._return_fraction * torso_length:
            self.reps += 1
            self._active_side = None
            self._raised = False
            return RepStatus(self.reps, "GOOD", "Arm rainbow complete", "READY")
        if self._raised:
            return RepStatus(self.reps, "RETURN", "Bring your arm back down", "RETURN")
        return RepStatus(self.reps, "MOVING", "Raise one arm above your shoulder", "MOVING")

    def no_pose(self) -> RepStatus:
        self._active_side = None
        self._raised = False
        return RepStatus(self.reps, "NO_POSE", "Show your shoulders, hips, and wrists", "READY")

    def reset_tracking(self) -> None:
        self._active_side = None
        self._raised = False


class FarmersCarryCounter:
    """Count a completed upright carry interval; 8 degrees comes from the notes."""

    def __init__(self, rule: dict) -> None:
        self.completed = 0
        self._max_torso_angle = rule["angle_degrees"]["torso_from_vertical_below"]
        self.hold_seconds = rule["prototype_rule"].get("hold_seconds", DEMO_HOLD_SECONDS)
        self._started_at: float | None = None
        self._complete = False

    @property
    def reps(self) -> int:
        return self.completed

    def update(self, landmarks, min_visibility: float) -> RepStatus:
        chosen = _best_visible_side(landmarks, ((11, 23), (12, 24)), min_visibility)
        if chosen is None:
            return self.no_pose()
        shoulder, hip = chosen
        torso_length = _distance(shoulder, hip)
        if torso_length < 0.05:
            return self.no_pose()
        torso_angle = math.degrees(math.atan2(abs(shoulder[0] - hip[0]), abs(shoulder[1] - hip[1])))
        if torso_angle >= self._max_torso_angle:
            self._started_at = None
            self._complete = False
            return RepStatus(
                self.completed,
                "POSTURE",
                f"Stand tall; keep torso under {self._max_torso_angle:g} degrees",
                "READY",
            )
        if self._complete:
            return RepStatus(self.completed, "GOOD", "Carry interval complete; reset", "COMPLETE")
        if self._started_at is None:
            self._started_at = time.monotonic()
        elapsed = time.monotonic() - self._started_at
        if elapsed >= self.hold_seconds:
            self.completed += 1
            self._complete = True
            return RepStatus(self.completed, "GOOD", "Carry interval complete", "COMPLETE")
        return RepStatus(self.completed, "HOLDING", f"Stay tall: {elapsed:.0f}/{self.hold_seconds:.0f} sec", "HOLDING")

    def no_pose(self) -> RepStatus:
        self._started_at = None
        self._complete = False
        return RepStatus(self.completed, "NO_POSE", "Show your shoulders and hips", "READY")

    def reset_tracking(self) -> None:
        self._started_at = None
        self._complete = False


class GoodMorningCounter:
    """Count a straight-legged hip hinge using the notes plus provisional endpoints."""

    SIDES = ((11, 23, 25, 27), (12, 24, 26, 28))

    def __init__(self, rule: dict) -> None:
        self.reps = 0
        self._armed = False
        self._at_hinge = False
        angles = rule["angle_degrees"]
        thresholds = rule["prototype_rep_thresholds"]
        self._min_hip_angle = angles["torso_not_good_below"]
        self._max_leg_deviation = angles["leg_chain_good_below"]
        self._standing_angle = thresholds["standing_hip_angle_at_least"]
        self._hinge_angle = thresholds["hinge_hip_angle_at_most"]

    def update(self, landmarks, min_visibility: float) -> RepStatus:
        chosen = _best_visible_side(landmarks, self.SIDES, min_visibility)
        if chosen is None:
            return self.no_pose()
        shoulder, hip, knee, ankle = chosen
        hip_angle = _angle(shoulder, hip, knee)
        knee_angle = _angle(hip, knee, ankle)
        if hip_angle is None or knee_angle is None:
            return self.no_pose()
        leg_deviation = 180.0 - knee_angle
        if leg_deviation >= self._max_leg_deviation:
            self._at_hinge = False
            return RepStatus(self.reps, "LEGS", "Keep your legs straighter", "READY")
        if hip_angle < self._min_hip_angle:
            self._at_hinge = False
            return RepStatus(
                self.reps,
                "TOO_FAR",
                f"Reduce hinge; stay above {self._min_hip_angle:g} degrees",
                "READY",
            )

        if hip_angle >= self._standing_angle:
            if self._at_hinge:
                self.reps += 1
                self._at_hinge = False
                self._armed = True
                return RepStatus(self.reps, "GOOD", "Good-morning rep complete", "READY")
            self._armed = True
            return RepStatus(self.reps, "READY", "Hinge forward with straight legs", "READY")
        if self._armed and hip_angle <= self._hinge_angle:
            self._at_hinge = True
            return RepStatus(self.reps, "HINGE", "Return to standing", "HINGE")
        if self._at_hinge:
            return RepStatus(self.reps, "RETURN", "Stand tall to finish", "RETURN")
        return RepStatus(self.reps, "MOVING", "Hinge forward with straight legs", "MOVING")

    def no_pose(self) -> RepStatus:
        self._armed = False
        self._at_hinge = False
        return RepStatus(self.reps, "NO_POSE", "Show your shoulder, hip, knee, and ankle", "READY")

    def reset_tracking(self) -> None:
        self._armed = False
        self._at_hinge = False


def create_tracker(mode: str, settings):
    """Build the tracker for one of the menu modes."""
    if mode == "deep_squat":
        return DeepSquatMode(settings)
    if mode == "plank":
        return PlankHoldCounter(settings.research_rules["plank"])
    if mode == "bicep_curl":
        return BicepCurlCounter(settings.research_rules["bicep_curl"])
    if mode == "arm_rainbow":
        return ArmRainbowCounter(settings.research_rules["arm_rainbow"])
    if mode == "farmers_carry":
        return FarmersCarryCounter(settings.research_rules["farmers_carry"])
    if mode == "good_morning":
        return GoodMorningCounter(settings.research_rules["good_morning"])
    raise ValueError(f"Unknown exercise mode: {mode}")
