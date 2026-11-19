from pathlib import Path
import pytest

from robot_pick_place.vision.load_camera_config import CameraConfigLoader
from robot_pick_place.vision.exceptions import CameraConfigError

# Locate the project root relative to this test file
PROJECT_ROOT = Path(__file__).resolve().parents[1]

VALID_CONFIG_PATH = (
    PROJECT_ROOT / "config" / "camera_config.yaml"
)

INVALID_CONFIG_PATH = (
    Path(__file__).resolve().parent
    / "fixtures"
    / "invalid_camera_config.yaml"
)


@pytest.fixture(scope="module")
def camera_config():
    """Load the existing camera configuration."""

    return CameraConfigLoader(str(VALID_CONFIG_PATH))

def test_load_valid_camera_config():
    """Valid camera configuration should load successfully."""

    config = CameraConfigLoader(str(VALID_CONFIG_PATH))

    assert config.device["index"] == 0
    assert config.device["width"] == 640
    assert config.device["height"] == 480
    assert config.device["fps"] == 30

    assert config.acquisition["max_open_attempts"] == 5
    assert config.acquisition["max_read_attempts"] == 3
    assert config.acquisition["retry_delay"] == pytest.approx(0.5)


def test_load_invalid_camera_config():
    """Invalid camera configuration should be rejected."""

    assert INVALID_CONFIG_PATH.is_file()

    with pytest.raises(
        CameraConfigError,
        match="width",
    ):
        CameraConfigLoader(str(INVALID_CONFIG_PATH))


def test_camera_config_structure(camera_config):
    assert "simple_camera" in camera_config.config
    assert "device" in camera_config.config["simple_camera"]
    assert "acquisition" in camera_config.config["simple_camera"]


def test_missing_camera_config(tmp_path):
    missing_path = tmp_path / "nonexistent.yaml"

    with pytest.raises(FileNotFoundError):
        CameraConfigLoader(str(missing_path))

@pytest.mark.parametrize(
    "value",
    [-1, 0, 640.5, "640", True],
)

def test_invalid_camera_width(value):
    with pytest.raises(CameraConfigError):
        CameraConfigLoader._validate_integer(
            key="width",
            section={"width": value},
            minimum=1,
        )

@pytest.mark.parametrize(
    "value",
    [-0.5, 0.0, "0.5", True],
)
def test_invalid_retry_delay(value):
    with pytest.raises(CameraConfigError):
        CameraConfigLoader._validate_float(
            key="retry_delay",
            section={"retry_delay": value},
            minimum=0.1,
        )

