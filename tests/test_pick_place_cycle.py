
import pytest

from robot_pick_place.models import RobotPose
from robot_pick_place.robot.fake_robot import FakeRobot
from robot_pick_place.robot.robot_sequence import (
    PickPlaceCycle,
    PickPlacePlan,
    CycleStatus,
)


@pytest.fixture
def plan():
    return PickPlacePlan(
        pick_pose=RobotPose(220, -40, 20, 45),
        pick_approach_pose=RobotPose(220, -40, 70, 45),
        place_pose=RobotPose(260, 30, 20, 0),
        place_approach_pose=RobotPose(260, 30, 70, 0),
    )


@pytest.fixture
def home_pose():
    return RobotPose(200, 0, 150, 0)


def make_robot(home_pose, grip_results=(True,)):
    robot = FakeRobot(
        home_pose,
        grip_results=grip_results,
    )
    robot.set_part_available(True)
    return robot


def test_successful_pick_and_place(home_pose, plan):
    robot = make_robot(home_pose)
    cycle = PickPlaceCycle(robot)

    result = cycle.run(plan)

    assert result.status == CycleStatus.SUCCESS
    assert result.grip_attempts == 1
    assert robot.current_pose == home_pose
    assert not robot.gripper_closed
    assert not robot.alarms


def test_grip_succeeds_on_second_attempt(home_pose, plan):
    robot = make_robot(
        home_pose,
        grip_results=[False, True],
    )

    result = PickPlaceCycle(robot).run(plan)

    assert result.status == CycleStatus.SUCCESS
    assert result.grip_attempts == 2

    close_commands = [
        command for command in robot.command_history
        if command[0] == "close_gripper"
    ]
    assert len(close_commands) == 2


def test_grip_failure_after_three_attempts(home_pose, plan):
    robot = make_robot(
        home_pose,
        grip_results=[False, False, False],
    )

    result = PickPlaceCycle(robot).run(plan)

    assert result.status == CycleStatus.GRIP_FAILED
    assert result.grip_attempts == 3
    assert len(robot.alarms) == 1
    assert robot.current_pose == plan.pick_approach_pose


def test_part_timeout(home_pose, plan):
    robot = FakeRobot(home_pose)
    # Part availability remains False.

    class FakeClock:
        def __init__(self):
            self.now = 0.0

        def monotonic(self):
            return self.now

        def sleep(self, seconds):
            self.now += seconds

    clock = FakeClock()

    cycle = PickPlaceCycle(
        robot,
        part_timeout=1.0,
        poll_interval=0.1,
        clock=clock.monotonic,
        sleep=clock.sleep,
    )

    result = cycle.run(plan)

    assert result.status == CycleStatus.PART_TIMEOUT
    assert len(robot.alarms) == 1
    assert not any(
        command[0] == "move_to"
        for command in robot.command_history
    )


def test_estop_before_cycle(home_pose, plan):
    robot = make_robot(home_pose)
    robot.trigger_emergency_stop()

    result = PickPlaceCycle(robot).run(plan)

    assert result.status == CycleStatus.EMERGENCY_STOPPED
    assert robot.current_pose == home_pose
    assert len(robot.alarms) == 1


def test_estop_during_motion(home_pose, plan):
    robot = make_robot(home_pose)
    robot.on_motion = robot.trigger_emergency_stop

    result = PickPlaceCycle(robot).run(plan)

    assert result.status == CycleStatus.EMERGENCY_STOPPED
    assert robot.current_pose == home_pose

    assert not any(
        command[0] == "close_gripper"
        for command in robot.command_history
    )


def test_successful_command_sequence(home_pose, plan):
    robot = make_robot(home_pose)

    result = PickPlaceCycle(robot).run(plan)

    assert result.status == CycleStatus.SUCCESS

    commands = [
        command[0] for command in robot.command_history
    ]

    assert commands == [
        "open_gripper",
        "move_to",  # Pick approach
        "move_to",  # Pick
        "close_gripper",
        "move_to",  # Retreat
        "move_to",  # Place approach
        "move_to",  # Place
        "open_gripper",
        "move_to",  # Place retreat
        "move_to",  # Home (FakeRobot implementation)
        "move_home",
    ]
