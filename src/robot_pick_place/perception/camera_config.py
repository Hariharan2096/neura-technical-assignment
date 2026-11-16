from pathlib import Path
import yaml

class CameraConfig:

    def __init__(self, config_path: str):

        self.path = Path(config_path)

        if not self.path.is_file():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        with self.path.open("r", encoding="utf-8") as file:
            self.config = yaml.safe_load(file)

        if not isinstance(self.config, dict):
            raise ValueError(f"Invalid configuration format in file: {config_path}")

        camera = self.config["simple_camera"]

        self.device = camera["device"]
        self.acquisition = camera["acquisition"]
        self.image = camera["image"]