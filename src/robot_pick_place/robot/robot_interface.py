from abc import ABC, abstractmethod

from robot_pick_place.models import RobotPose

class RobotInterface(ABC):
    """Abstract interface for robot motion and I/O"""

    @abstractmethod
    def move_to(self, pose: RobotPose) -> None:
        """Move the robot to the specified pose"""
        ...

    @abstractmethod
    def move_home(self) -> None:
        """Move the robot to its home position"""
        ...

    @abstractmethod
    def open_gripper(self) -> None:
        """Open the robot's gripper"""
        ...

    @abstractmethod
    def close_gripper(self) -> None:
        """Close the robot's gripper"""
        ...

    @abstractmethod
    def is_grip_successful(self) -> bool:
        """Return the gripper's grasp confirmation."""
        ...

    @abstractmethod
    def is_part_available(self) -> bool:
        """Read the part-availability input."""
        ...

    @property
    @abstractmethod
    def is_emergency_stopped(self) -> bool:
        """Return whether emergency stop is active."""
        ...

    @abstractmethod
    def raise_alarm(self, message: str) -> None:
        """Report a robot or process alarm"""
        ...