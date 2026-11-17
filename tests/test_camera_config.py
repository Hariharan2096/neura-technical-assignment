import pytest
import yaml

from robot_pick_place.vision.camera_config import CameraConfig
from robot_pick_place.vision.exceptions import CameraConfigError

@pytest.fixture
def valid_config():
    return {
        "simple_camera": {
            "device": {"index": 0},
            "acquisition": {
                "fps": 30,
                "max_open_attempts": 3,
                "max_read_attempts": 3,
                "retry_delay": 0.1,
            },
            "image": {"width": 640, "height": 480},
        }
    }