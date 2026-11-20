from dataclasses import dataclass

@dataclass(frozen=True)
class RobotPose:
    """Represents the simplified robot pose"""
    x: float
    y: float
    z: float
    yaw: float

@dataclass(frozen=True)
class Point2D:
    x: float
    y: float

@dataclass(frozen=True)
class PickPoses:
    pick: RobotPose
    approach: RobotPose

@dataclass(frozen=True)
class DetectedObject:
    object_id: int
    center_u: float
    center_v: float
    angle_deg: float
    corners: tuple[tuple[float, float], ...]
    area: float

@dataclass(frozen=True)
class ProcessPoses:
    pick_pose: RobotPose
    pick_approach_pose: RobotPose
    place_pose: RobotPose
    place_approach_pose: RobotPose  

