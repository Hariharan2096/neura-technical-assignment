from collections import deque
from collections.abc import Callable, Iterable

from robot_pick_place.models import RobotPose
from robot_pick_place.robot.robot_interface import RobotInterface
from robot_pick_place.robot.exceptions import EmergencyStopError


class FakeRobot(RobotInterface):
    """Deterministic robot simulator for unit testing"""

    def __init__(
        self,
        home_pose: RobotPose,
        grip_results: Iterable[bool] = (),
    ) -> None:
        self.home_pose = home_pose
        self.current_pose = home_pose

        self.gripper_closed = False
        self.part_available = False

        self._emergency_stopped = False
        self._grip_results = deque(grip_results)
        self._last_grip_success = False

        self.command_history: list[tuple] = []
        self.alarms: list[str] = []

        # Optional test hook for injecting a stop during motion.
        self.on_motion: Callable[[], None] | None = None


    @property
    def is_emergency_stopped(self):
        return self._emergency_stopped

    def _check_safety(self) -> None:
        if self._emergency_stopped:
            raise EmergencyStopError(
                "Robot operation blocked: emergency stop active."
            )

    def move_to(self, pose: RobotPose) -> None:
        self._check_safety()

        # Simulate an interruption before motion completes
        if self.on_motion is not None:
            self.on_motion()

        self._check_safety()

        self.current_pose = pose
        self.command_history.append(("move_to", pose))

    def move_home(self) -> None:
        self._check_safety()
        self.move_to(self.home_pose)
        self.command_history.append(("move_home",))

    def open_gripper(self) -> None:
        self._check_safety()

        self.gripper_closed = False
        self._last_grip_success = False
        self.command_history.append(("open_gripper",))


    def close_gripper(self) -> None:
        self._check_safety()

        self.gripper_closed = True

        if self.gripper_closed:
            self._last_grip_success = self._grip_results.popleft()
        else:
            self._last_grip_success = True

        self.command_history.append(("close_gripper",))

    def is_grip_successful(self) -> bool:
        self._check_safety()
        return self.gripper_closed and self._last_grip_success

    def is_part_available(self) -> bool:
        self._check_safety()
        return self.part_available

    def raise_alarm(self, message: str) -> None:
        # Alarm reporting must remain possible during an E-Stop
        self.alarms.append(message)
        self.command_history.append(("alarm", message))

    # Simulation controls: not part of RobotInterface.

    def set_part_available(self, available: bool) -> None:
        self.part_available = available

    def trigger_emergency_stop(self) -> None:
        self._emergency_stopped = True

    def release_emergency_stop(self) -> None:
        self._emergency_stopped = False
