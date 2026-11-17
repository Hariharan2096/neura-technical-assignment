from dataclasses import dataclass

@dataclass(frozen=True)
class RobotPose:
    """Represents the simplified robot pose"""
    x: float
    y: float
    z: float
    yaw: float