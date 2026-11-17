from loguru import logger
import time
from dataclasses import dataclass
from enum import Enum, auto
from typing import Callable

from robot_pick_place.models import RobotPose
from robot_pick_place.robot.robot_interface import RobotInterface
from robot_pick_place.robot.exceptions import EmergencyStopError, RobotError

class CycleStatus(Enum):
    SUCCESS = auto()
    PART_TIMEOUT = auto()
    GRIP_FAILED = auto()
    EMERGENCY_STOPPED = auto()
    ROBOT_ERROR = auto()


@dataclass(frozen=True)
class PickPlacePlan:
    pick_pose: RobotPose
    pick_approach_pose: RobotPose
    place_pose: RobotPose
    place_approach_pose: RobotPose


@dataclass(frozen=True)
class CycleResult:
    status: CycleStatus
    grip_attempts: int = 0
    message: str = ""

class PickPlaceCycle:
    """Coordinates one pick and place application cycle."""

    def __init__(
            self,
            robot: RobotInterface,
            part_timeout: float = 5.0,
            poll_interval: float = 0.1,
            max_grip_retries: int = 2,
            clock: Callable[[], float] = time.monotonic,
            sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        if part_timeout < 0:
            raise ValueError("part_timeout must be non-negative")
        if poll_interval <= 0:
            raise ValueError("poll_interval must be positive")
        if max_grip_retries < 0:
            raise ValueError("max_grip_retries must be non-negative")

        self.robot = robot
        self.part_timeout = part_timeout
        self.poll_interval = poll_interval
        self.max_grip_retries = max_grip_retries
        self.clock = clock
        self.sleep = sleep

    def _check_estop(self) -> None:
        if self.robot.is_emergency_stopped:
            raise EmergencyStopError("Emergency stop is active")

    def _wait_for_part(self) -> bool:
        deadline = self.clock() + self.part_timeout

        while True:
            self._check_estop()

            if self.robot.is_part_available():
                return True

            remaining = deadline - self.clock()
            if remaining <= 0:
                return False

            self.sleep(min(self.poll_interval, remaining))

    def _attempt_grip(self, plan: PickPlacePlan) -> int | None:
        total_attempts = 1 + self.max_grip_retries

        for attempt in range(1, total_attempts + 1):
            self._check_estop()

            # Open before descending for every attempt
            self.robot.open_gripper()
            self.robot.move_to(plan.pick_approach_pose)
            self.robot.move_to(plan.pick_pose)

            self.robot.close_gripper()

            if self.robot.is_grip_successful():
                logger.info(f"Grip successful on attempt {attempt}")
                return attempt

            logger.warning(f"Grip failed on attempt {attempt}/{total_attempts}")

            # Retreat before another attempt
            self.robot.open_gripper()
            self.robot.move_to(plan.pick_approach_pose)

        return None

    def _place_part(self, plan: PickPlacePlan) -> None:
        # First retreat vertically from the pick location.
        self.robot.move_to(plan.pick_approach_pose)

        # Approach the destination from above.
        self.robot.move_to(plan.place_approach_pose)
        self.robot.move_to(plan.place_pose)

        self.robot.open_gripper()
        self.robot.move_to(plan.place_approach_pose)

    def run(self, plan: PickPlacePlan) -> CycleResult:
        """Execute one cycle and report its result."""

        grip_attempts = 0

        try:
            self._check_estop()

            if not self._wait_for_part():
                message = "Timed out waiting for part"
                self.robot.raise_alarm(message)
                return CycleResult(
                    CycleStatus.PART_TIMEOUT,
                    message=message,
                )

            attempts = self._attempt_grip(plan)

            if attempts is None:
                grip_attempts = 1 + self.max_grip_retries
                message = "Grip failed after all attempts"
                self.robot.raise_alarm(message)
                return CycleResult(
                    CycleStatus.GRIP_FAILED,
                    grip_attempts,
                    message,
                )
            grip_attempts = attempts
            self._place_part(plan)
            self.robot.move_home()

            return CycleResult(
                CycleStatus.SUCCESS,
                grip_attempts,
                "Pick-and-place completed",
            )
        
        except EmergencyStopError as exc:
            # Never command motion after an E-stop.
            message = str(exc)
            self.robot.raise_alarm(message)
            return CycleResult(
                CycleStatus.EMERGENCY_STOPPED,
                grip_attempts,
                message,
            )

        except RobotError as exc:
            message = f"Robot error: {exc}"
            self.robot.raise_alarm(message)
            return CycleResult(
                CycleStatus.ROBOT_ERROR,
                grip_attempts,
                message,
            )