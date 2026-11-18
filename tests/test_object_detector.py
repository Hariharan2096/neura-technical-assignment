
import cv2
import numpy as np
import pytest

from robot_pick_place.vision.object_detector import (
    ObjectDetector,
)


@pytest.fixture
def detector():
    return ObjectDetector()


def make_image(rectangles):
    image = np.full(
        (480, 640, 3),
        255,
        dtype=np.uint8,
    )

    for center, size, angle in rectangles:
        rect = (center, size, angle)
        corners = cv2.boxPoints(rect)

        cv2.fillConvexPoly(
            image,
            np.rint(corners).astype(np.int32),
            (0, 0, 0),
        )

    return image


def test_detects_three_rectangles(detector):
    image = make_image([
        ((160, 140), (80, 40), 0),
        ((340, 150), (90, 40), 30),
        ((270, 340), (100, 45), -35),
    ])

    objects = detector.detect(image)

    assert len(objects) == 3
    assert [obj.object_id for obj in objects] == [1, 2, 3]


def test_detects_center(detector):
    image = make_image([
        ((320, 240), (100, 40), 0),
    ])

    objects = detector.detect(image)

    assert len(objects) == 1
    assert objects[0].center_u == pytest.approx(
        320, abs=2
    )
    assert objects[0].center_v == pytest.approx(
        240, abs=2
    )


@pytest.mark.parametrize(
    "angle",
    [0, 30, -35, 60],
)
def test_detects_orientation(detector, angle):
    image = make_image([
        ((320, 240), (120, 40), angle),
    ])

    objects = detector.detect(image)

    assert len(objects) == 1
    assert objects[0].angle_deg == pytest.approx(
        angle, abs=3
    )


def test_empty_image_returns_no_objects(detector):
    image = np.full(
        (480, 640, 3),
        255,
        dtype=np.uint8,
    )

    assert detector.detect(image) == []


def test_ignores_small_objects(detector):
    image = make_image([
        ((320, 240), (15, 10), 0),
    ])

    assert detector.detect(image) == []


def test_rejects_invalid_input(detector):
    with pytest.raises(ValueError):
        detector.detect(np.zeros((100, 100), dtype=np.uint8))
