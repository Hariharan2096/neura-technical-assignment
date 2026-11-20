from collections import deque
from collections.abc import Callable, Iterable
import random
import time
from threading import Event

from robot_pick_place.models import RobotPose
from robot_pick_place.robot.robot_interface import RobotInterface
from robot_pick_place.robot.exceptions import EmergencyStopError
from robot_pick_place.safety.robot_estop_recovery import (
    RecoveryAction,
    recoverable_operation,
)


class FakeRobot(RobotInterface):
    """Deterministic robot simulator for unit testing"""

    def __init__(
        self,
        home_pose: RobotPose,
        grip_results: Iterable[bool] = (),
        grip_success_probability: float = 0.5,
        motion_delay: float = 5.0,          
        gripper_open_delay: float = 1.0,
        gripper_close_delay: float = 1.0,
        simulate_estop: bool = False,
        estop_probability: float = 0.5,
        estop_seed: int | None = None,
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

        if not 0.0 <= grip_success_probability <= 1.0:
            raise ValueError(
                "grip_success_probability must be between 0 and 1"
            )

        self.grip_success_probability = grip_success_probability

        for name, value in (
            ("motion_delay", motion_delay),
            ("gripper_open_delay", gripper_open_delay),
            ("gripper_close_delay", gripper_close_delay),
        ):
            if not 0.0 <= value <= float("inf"):
                raise ValueError(f"{name} must be a finite and non-negative.")

        self.motion_delay = motion_delay
        self.gripper_open_delay = gripper_open_delay
        self.gripper_close_delay = gripper_close_delay

        self._estop_event = Event()

        if not 0.0 <= estop_probability <= 1.0:
            raise ValueError(
                "estop_probability must be between 0 and 1"
            )

        self.simulate_estop = simulate_estop
        self.estop_probability = estop_probability

        self._estop_rng = random.Random(estop_seed)

        self.on_estop_recovery: (
            Callable[[], RecoveryAction] | None
        ) = None

        self._random_estop_triggered = False
        
    @property
    def is_emergency_stopped(self) -> bool:
        return self._estop_event.is_set()
    
    def _check_safety(self) -> None:
        if self._emergency_stopped:
            raise EmergencyStopError(
                "Robot operation blocked: emergency stop active."
            )

    def _simulate_delay(self, duration: float) -> None:
        """Simulation sequence delays which can be interrupted by E-Stop"""

        self._check_safety()

        if self._estop_event.wait(timeout=duration):
            self._check_safety()

        self._check_safety()

    def _maybe_trigger_random_estop(
        self,
        operation: str,
    ) -> None:
        """Randomly trigger E-stop before a robot operation."""

        if not self.simulate_estop:
            return

        if self._random_estop_triggered:
            return

        self._check_safety()

        if self._estop_rng.random() < self.estop_probability:
            self._random_estop_triggered = True

            self.trigger_emergency_stop()

            raise EmergencyStopError(
                f"Simulated random E-stop during {operation}"
            )

    @recoverable_operation
    def move_to(self, pose: RobotPose) -> None:
        """Simulate the fake robot movement to a target pose."""
        
        self._check_safety()

        self._maybe_trigger_random_estop(
            f"move_to({pose})"
        )

        # Simulate an interruption before motion completes
        if self.on_motion is not None:
            self.on_motion()

        self._check_safety()

        self._simulate_delay(self.motion_delay)

        self._check_safety()

        self.current_pose = pose

        if pose != self.home_pose:
            self.command_history.append(("move_to", pose))


    def move_home(self) -> None:
        """Commands the fake robot to move to home pose."""
        self._check_safety()
        self.move_to(self.home_pose)
        self.command_history.append(("move_home",))

    @recoverable_operation
    def open_gripper(self) -> None:
        """Executes gripper open command."""
        self._check_safety()

        self._maybe_trigger_random_estop(
            "open_gripper"
        )
        self._simulate_delay(self.gripper_open_delay)

        self._check_safety()

        self.gripper_closed = False
        self._last_grip_success = False

        self.command_history.append(("open_gripper",))

    @recoverable_operation
    def close_gripper(self) -> None:
        """Simulates the gripper close action"""
        self._check_safety()

        self._maybe_trigger_random_estop(
            "close_gripper"
        )
        self._simulate_delay(self.gripper_close_delay)

        self._check_safety()

        self.gripper_closed = True

        if self._grip_results:
            self._last_grip_success = self._grip_results.popleft()
        else:
            self._last_grip_success = (
                random.random() < self.grip_success_probability
            )

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
        self._estop_event.set()

    def release_emergency_stop(self) -> None:
        self._estop_event.clear()
