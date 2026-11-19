from pathlib import Path
import yaml

from .exceptions import CameraConfigError

class CameraConfigLoader:

    def __init__(self, config_path: str):

        self.path = Path(config_path)

        if not self.path.is_file():
            raise FileNotFoundError(f"Configuration file not found: {self.path}")

        try:
            with self.path.open("r", encoding="utf-8") as file:
                self.config = yaml.safe_load(file)

        except (OSError, yaml.YAMLError) as e:
            raise CameraConfigError(f"Error reading configuration file: {self.path}") from e

        if not isinstance(self.config, dict):
            raise CameraConfigError("Camera configuration must contain a YAML mapping")

        self._validate()

    def _validate(self) -> None:
        """Validate camera configuration and expose its sections"""

        camera = self.config.get("simple_camera")

        if not isinstance(camera, dict):
            raise CameraConfigError("Missing or invalid 'simple_camera' section")

        required_sections = ("device", "acquisition")

        for section in required_sections:
            if not isinstance(camera.get(section), dict):
                raise CameraConfigError(f"Missing or invalid 'simple_camera.{section}' section.'")

        self.device = camera["device"]
        self.acquisition = camera["acquisition"]

        # Validate camera device settings
        self._validate_integer("index", self.device, minimum=0)
        self._validate_integer("width", self.device, minimum=1)
        self._validate_integer("height", self.device, minimum=1)
        self._validate_integer("fps", self.device, minimum=1)

        self._validate_integer("max_open_attempts", self.acquisition, minimum=1)
        self._validate_integer("max_read_attempts", self.acquisition, minimum=1)
        self._validate_float("retry_delay", self.acquisition, minimum=0.1)

    @staticmethod
    def _validate_integer(
        key: str,
        section: dict,
        minimum: int,
    ) -> None:
        value = section.get(key)

        if (
            isinstance(value, bool)
            or not isinstance(value, int)
            or value < minimum
        ):
            raise CameraConfigError(
                f"'{key}' must be an integer >= {minimum}"
            )

    @staticmethod
    def _validate_float(
        key: str,
        section: dict,
        minimum: int,
    ) -> None:
        value = section.get(key)

        if (
            isinstance(value, bool)
            or not isinstance(value, float)
            or value < minimum
        ):
            raise CameraConfigError(
                f"'{key}' must be an float >= {minimum}"
            )