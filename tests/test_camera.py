
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from robot_pick_place.vision.simple_camera import SimpleCamera
from robot_pick_place.vision.exceptions import (
    CameraOpenError,
    FrameReadError,
)


@pytest.fixture
def camera_config():
    config = MagicMock()

    config.device = {
        "index": 0,
        "width": 640,
        "height": 480,
        "fps": 30,
    }

    config.acquisition = {
        "max_open_attempts": 3,
        "max_read_attempts": 3,
        "retry_delay": 0,
    }

    return config


def test_camera_opens_successfully(camera_config):
    with patch(
        "robot_pick_place.vision.simple_camera.cv2.VideoCapture"
    ) as mock_capture:
        mock_capture.return_value.isOpened.return_value = True

        camera = SimpleCamera(camera_config)
        camera.open()

        assert camera.is_open
        mock_capture.assert_called_once_with(0)

        camera.close()


def test_camera_open_retries_exactly_three_times(camera_config):
    with patch(
        "robot_pick_place.vision.simple_camera.cv2.VideoCapture"
    ) as mock_capture:
        mock_capture.return_value.isOpened.return_value = False

        camera = SimpleCamera(camera_config)

        with pytest.raises(CameraOpenError):
            camera.open()

        assert mock_capture.call_count == 3


def test_frame_read_failure(camera_config):
    with patch(
        "robot_pick_place.vision.simple_camera.cv2.VideoCapture"
    ) as mock_capture:
        capture = mock_capture.return_value
        capture.isOpened.return_value = True
        capture.read.return_value = (False, None)

        camera = SimpleCamera(camera_config)
        camera.open()

        with pytest.raises(FrameReadError):
            camera.read()

        assert capture.read.call_count == 3

        camera.close()
