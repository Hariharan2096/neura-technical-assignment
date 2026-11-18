import math
from dataclasses import dataclass

from robot_pick_place.models import RobotPose

@dataclass(frozen=True)
class PickPoses:
    pick: RobotPose
    approach: RobotPose

class PoseGenerator:
    """Generate top-down pick and approach poses."""

    def __init__(
        self,
        pick_height: float = 20.0,
        approach_height: float = 70.0,
    ) -> None:
        if not all(
            math.isfinite(v)
            for v in (pick_height, approach_height)
        ):
            raise ValueError("Pose heights must be finite")

        if pick_height < 0:
            raise ValueError("Pick height must be non-negative")

        if approach_height <= pick_height:
            raise ValueError(
                "Approach height must exceed pick height"
            )

        self.pick_height = pick_height
        self.approach_height = approach_height

    def generate(
            self,
            x: float,
            y: float,
            yaw: float,
    ) -> PickPoses:
        """Generate pick and approach poses in robot coordinates."""

        if not all(
            math.isfinite(v)
            for v in (x, y, yaw)
        ):
            raise ValueError("Robot coordinates and yaw must be finite")

        return PickPoses(
            pick=RobotPose(
                x=x,
                y=y,
                z=self.pick_height,
                yaw=yaw
            ),
            approach=RobotPose(
                x=x,
                y=y,
                z=self.approach_height,
                yaw=yaw,
            ),
        )
