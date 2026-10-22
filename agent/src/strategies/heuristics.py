import math

from .base import Pose


def manhattan(pose_a: Pose, pose_b: Pose) -> int:
    return abs(pose_a[0] - pose_b[0]) + abs(pose_a[1] - pose_b[1])


def euclidean(pose_a: Pose, pose_b: Pose) -> float:
    return math.hypot(pose_a[0] - pose_b[0], pose_a[1] - pose_b[1])

def chebyshev(pose_a: Pose, pose_b: Pose) -> int:
    return max(abs(pose_a[0] - pose_b[0]), abs(pose_a[1] - pose_b[1]))