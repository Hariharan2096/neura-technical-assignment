
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from robot_pick_place.vision.simple_camera import SimpleCamera
from robot_pick_place.vision.exceptions import CameraOpenError, FrameReadError

@pytest.fixture
def camera():
    """Create a SimpleCamera without accessing hardware."""
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
        "retry_delay": 0.2,
    }
    return SimpleCamera(config)

@pytest.fixture
def valid_frame():
    """Create a valid 640x480 BGR image."""
    return np.zeros((480, 640, 3), dtype=np.uint8)

@pytest.fixture
def mock_capture():
    """Create a simulated OpenCV capture device."""

    capture = MagicMock()
    capture.isOpened.return_value = True

    return capture

def test_camera_initialization(camera):
    assert camera.camera_index == 0
    assert camera.width == 640
    assert camera.height == 480
    assert camera.fps == 30

    assert camera.max_open_attempts == 3
    assert camera.max_read_attempts == 3
    assert camera.retry_delay == 0.2

    assert camera._capture is None
    assert camera.is_open is False

def test_camera_is_open(camera, mock_capture):
    camera._capture = mock_capture

    assert camera.is_open is True

    mock_capture.isOpened.return_value = False

    assert camera.is_open is False