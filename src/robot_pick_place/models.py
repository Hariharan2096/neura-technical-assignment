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