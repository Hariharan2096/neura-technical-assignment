import cv2
import numpy as np
import pytest

from robot_pick_place.vision.image_file_camera import (
    ImageFileCamera,
)
from robot_pick_place.vision.exceptions import (
    CameraOpenError,
    FrameReadError,
)


@pytest.fixture
def valid_image(tmp_path):
    path = tmp_path / "test_image.png"

    frame = np.full(
        (480, 640, 3),
        255,
        dtype=np.uint8,
    )

    assert cv2.imwrite(str(path), frame)
    return path


def test_open_valid_image(valid_image):
    camera = ImageFileCamera(valid_image)

    camera.open()

    assert camera.is_open
    camera.close()


def test_read_returns_correct_dimensions(valid_image):
    with ImageFileCamera(valid_image) as camera:
        frame = camera.read()

        assert frame.shape == (480, 640, 3)
        assert frame.dtype == np.uint8


def test_read_returns_independent_copy(valid_image):
    with ImageFileCamera(valid_image) as camera:
        first = camera.read()
        first[0, 0] = (0, 0, 0)

        second = camera.read()

        assert np.array_equal(
            second[0, 0],
            np.array([255, 255, 255]),
        )


def test_missing_image(tmp_path):
    camera = ImageFileCamera(
        tmp_path / "missing.png"
    )

    with pytest.raises(CameraOpenError):
        camera.open()


def test_invalid_image_file(tmp_path):
    path = tmp_path / "invalid.png"
    path.write_text("Not an image", encoding="utf-8")

    camera = ImageFileCamera(path)

    with pytest.raises(CameraOpenError):
        camera.open()


def test_wrong_image_dimensions(tmp_path):
    path = tmp_path / "wrong_size.png"

    frame = np.zeros(
        (240, 320, 3),
        dtype=np.uint8,
    )
    assert cv2.imwrite(str(path), frame)

    camera = ImageFileCamera(path)

    with pytest.raises(CameraOpenError):
        camera.open()


def test_read_before_open(valid_image):
    camera = ImageFileCamera(valid_image)

    with pytest.raises(FrameReadError):
        camera.read()


def test_close_releases_image(valid_image):
    camera = ImageFileCamera(valid_image)
    camera.open()
    camera.close()

    assert not camera.is_open

    with pytest.raises(FrameReadError):
        camera.read()


def test_context_manager_closes_source(valid_image):
    camera = ImageFileCamera(valid_image)

    with camera:
        assert camera.is_open

    assert not camera.is_open
