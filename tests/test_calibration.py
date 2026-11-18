
import pytest

from robot_pick_place.geometry.calibration import CoordinateTransformer


@pytest.fixture
def transformer():
    return CoordinateTransformer(
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


@pytest.mark.parametrize(
    "u,v,expected_x,expected_y",
    [
        (100, 100, 150, -150),
        (540, 100, 150, 70),
        (540, 380, 290, 70),
        (100, 380, 290, -150),
        (320, 240, 220, -40),
    ],
)
def test_pixel_to_robot(
    transformer, u, v, expected_x, expected_y
):
    result = transformer.pixel_to_robot(u, v)

    assert result.x == pytest.approx(expected_x)
    assert result.y == pytest.approx(expected_y)


@pytest.mark.parametrize(
    "image_angle,expected_yaw",
    [
        (0, 90 - 180),   # Horizontal image axis -> robot Y
        (90, 0),         # Vertical image axis -> robot X
        (45, 45),
        (-45, -45),
    ],
)
def test_angle_transformation(
    transformer, image_angle, expected_yaw
):
    result = transformer.angle_to_robot(image_angle)

    assert result == pytest.approx(expected_yaw)


def test_rejects_collinear_calibration():
    with pytest.raises(ValueError):
        CoordinateTransformer(
            pixel_points=[(0, 0), (1, 1), (2, 2)],
            robot_points=[(0, 0), (1, 1), (2, 2)],
        )
