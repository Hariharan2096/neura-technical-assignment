
import pytest

from robot_pick_place.models import RobotPose
from robot_pick_place.robot.fake_robot import FakeRobot
from robot_pick_place.robot.exceptions import EmergencyStopError


@pytest.fixture
def home_pose():
    return RobotPose(x=200, y=0, z=150, yaw=0.0)


@pytest.fixture
def robot(home_pose):
    return FakeRobot(home_pose)


def test_robot_moves_to_target(robot):
    target = RobotPose(220, -40, 70, 45)

    robot.move_to(target)

    assert robot.current_pose == target
    assert robot.command_history[-1] == ("move_to", target)


def test_robot_returns_home(robot, home_pose):
    robot.move_to(RobotPose(220, -40, 70, 45))
    robot.move_home()

    assert robot.current_pose == home_pose


def test_successful_grip(home_pose):
    robot = FakeRobot(home_pose, grip_results=[True])

    robot.close_gripper()

    assert robot.is_grip_successful()


def test_failed_grip(home_pose):
    robot = FakeRobot(home_pose, grip_results=[False])

    robot.close_gripper()

    assert not robot.is_grip_successful()


def test_emergency_stop_blocks_motion(robot):
    initial_pose = robot.current_pose
    robot.trigger_emergency_stop()

    with pytest.raises(EmergencyStopError):
        robot.move_to(RobotPose(220, -40, 70, 45))

    assert robot.current_pose == initial_pose


def test_emergency_stop_during_motion(robot):
    initial_pose = robot.current_pose
    robot.on_motion = robot.trigger_emergency_stop

    with pytest.raises(EmergencyStopError):
        robot.move_to(RobotPose(220, -40, 70, 45))

    assert robot.current_pose == initial_pose


def test_emergency_stop_blocks_gripper(robot):
    robot.trigger_emergency_stop()

    with pytest.raises(EmergencyStopError):
        robot.close_gripper()

    assert not robot.gripper_closed


def test_alarm_recording(robot):
    robot.raise_alarm("Grip failed")

    assert robot.alarms == ["Grip failed"]


def test_part_availability(robot):
    assert not robot.is_part_available()

    robot.set_part_available(True)

    assert robot.is_part_available()
