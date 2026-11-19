
import pytest
from robot_pick_place.geometry.pose_generator import PoseGenerator


def test_generates_correct_pick_pose():
    generator = PoseGenerator(
        pick_height=20,
        approach_height=70,
    )

    poses = generator.generate(
        x=220,
        y=-40,
        yaw=45,
    )

    assert poses.pick.x == 220
    assert poses.pick.y == -40
    assert poses.pick.z == 20
    assert poses.pick.yaw == 45


def test_generates_correct_approach_pose():
    generator = PoseGenerator()

    poses = generator.generate(
        x=220,
        y=-40,
        yaw=45,
    )

    assert poses.approach.x == 220
    assert poses.approach.y == -40
    assert poses.approach.z == 70
    assert poses.approach.yaw == 45


def test_rejects_invalid_heights():
    with pytest.raises(ValueError):
        PoseGenerator(
            pick_height=70,
            approach_height=20,
        )


def test_rejects_non_finite_coordinates():
    generator = PoseGenerator()

    with pytest.raises(ValueError):
        generator.generate(
            x=float("nan"),
            y=0,
            yaw=0,
        )
