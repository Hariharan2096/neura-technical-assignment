
from pathlib import Path
from unittest.mock import MagicMock

import numpy as np
import pytest

from robot_pick_place.application.pick_place_app import (
    PickPlaceApplication,
)
from robot_pick_place.geometry.calibration import (
    CoordinateTransformer,
)
from robot_pick_place.geometry.pose_generator import (
    PoseGenerator,
)
from robot_pick_place.models import RobotPose
from robot_pick_place.robot.fake_robot import FakeRobot
from robot_pick_place.robot.robot_sequence import (
    PickPlaceCycle,
)
from robot_pick_place.vision.object_detector import (
    DetectedObject,
)


def make_object(object_id, u, v, angle=0.0):
    return DetectedObject(
        object_id=object_id,
        center_u=u,
        center_v=v,
        angle_deg=angle,
        corners=(
            (u - 20, v - 10),
            (u + 20, v - 10),
            (u + 20, v + 10),
            (u - 20, v + 10),
        ),
        area=800.0,
    )


@pytest.fixture
def setup_app(tmp_path):
    frame = np.full(
        (480, 640, 3),
        255,
        dtype=np.uint8,
    )

    camera = MagicMock()
    camera.__enter__.return_value = camera
    camera.read.return_value = frame

    detector = MagicMock()
    annotator = MagicMock()
    annotator.annotate.return_value = frame.copy()

    output_path = tmp_path / "annotated.png"
    annotator.save.return_value = output_path

    transformer = CoordinateTransformer(
        pixel_points=[
            (100, 100),
            (540, 100),
            (540, 380),
            (100, 380),
        ],
        robot_points=[
            (150, -150),
            (150, 70),
            (290, 70),
            (290, -150),
        ],
    )

    robot = FakeRobot(
        home_pose=RobotPose(200, 0, 150, 0),
        grip_results=[True, True, True],
    )
    robot.set_part_available(True)

    cycle = PickPlaceCycle(
        robot=robot,
        part_timeout=0.0,
        poll_interval=0.01,
    )

    app = PickPlaceApplication(
        camera=camera,
        detector=detector,
        annotator=annotator,
        transformer=transformer,
        pose_generator=PoseGenerator(),
        cycle=cycle,
        place_pose=RobotPose(260, 30, 20, 0),
        place_approach_pose=RobotPose(260, 30, 70, 0),
    )

    return app, detector, annotator, robot, output_path


def test_successful_single_object(setup_app):
    app, detector, annotator, robot, output = setup_app

    detector.detect.return_value = [
        make_object(1, 320, 240, 45)
    ]

    result = app.run(output)

    assert result.detected_count == 1
    assert result.successful_picks == 1
    assert result.failed_picks == 0
    assert not result.aborted
    assert result.object_results[0].status == "SUCCESS"

    # Verify the transformed pick pose reached the robot.
    pick_pose = RobotPose(220, -40, 20, 45)

    assert any(
        command[0] == "move_to"
        and command[1].x == pytest.approx(pick_pose.x)
        and command[1].y == pytest.approx(pick_pose.y)
        and command[1].z == pytest.approx(pick_pose.z)
        and command[1].yaw == pytest.approx(
            pick_pose.yaw
        )
        for command in robot.command_history
    )

    annotator.save.assert_called_once()


def test_multiple_objects(setup_app):
    app, detector, _, robot, output = setup_app

    detector.detect.return_value = [
        make_object(1, 160, 140),
        make_object(2, 320, 240),
        make_object(3, 440, 330),
    ]

    result = app.run(output)

    assert result.detected_count == 3
    assert result.successful_picks == 3
    assert result.failed_picks == 0

    assert sum(
        command[0] == "move_home"
        for command in robot.command_history
    ) == 3


def test_no_objects(setup_app):
    app, detector, annotator, robot, output = setup_app

    detector.detect.return_value = []

    result = app.run(output)

    assert result.detected_count == 0
    assert result.successful_picks == 0
    assert result.failed_picks == 0
    assert robot.command_history == []

    annotator.save.assert_called_once()


def test_outside_workspace(setup_app):
    app, detector, _, robot, output = setup_app

    detector.detect.return_value = [
        make_object(1, 50, 50)
    ]

    result = app.run(output)

    assert result.successful_picks == 0
    assert result.failed_picks == 1
    assert result.object_results[0].status == (
        "OUT_OF_WORKSPACE"
    )
    assert robot.command_history == []


def test_grip_failure(setup_app):
    app, detector, _, robot, output = setup_app

    detector.detect.return_value = [
        make_object(1, 320, 240)
    ]

    robot._grip_results.clear()
    robot._grip_results.extend([False, False, False])

    result = app.run(output)

    assert result.successful_picks == 0
    assert result.failed_picks == 1
    assert result.object_results[0].status == "GRIP_FAILED"
    assert result.object_results[0].grip_attempts == 3
    assert len(robot.alarms) == 1


def test_emergency_stop_aborts_remaining_objects(
    setup_app,
):
    app, detector, _, robot, output = setup_app

    detector.detect.return_value = [
        make_object(1, 160, 140),
        make_object(2, 320, 240),
    ]

    robot.on_motion = robot.trigger_emergency_stop

    result = app.run(output)

    assert result.aborted
    assert result.successful_picks == 0
    assert result.object_results[0].status == (
        "EMERGENCY_STOPPED"
    )
    assert len(result.object_results) == 1
