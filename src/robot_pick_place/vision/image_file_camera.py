from pathlib import Path
import cv2
import numpy as np

from robot_pick_place.vision.camera_interface import CameraInterface
from robot_pick_place.vision.exceptions import CameraOpenError, FrameReadError

class ImageFileCamera(CameraInterface):
    """Camera-compatible interface for loading a saved image."""

    def __init__(
        self, image_path: str | Path, 
        width: int = 640, 
        height: int = 480
    ) -> None:
        if (
            not isinstance(width, int)
            or not isinstance(height, int)
            or width <= 0
            or height <= 0
        ):
            raise ValueError("Image width and height must be positive integers.")

        self.image_path = Path(image_path)
        self.width = width
        self.height = height
        self._frame = None

    @property
    def is_open(self) -> bool:
        return self._frame is not None

    def open(self) -> None:
        """Load and validate the image"""

        if self.is_open:
            return

        if not self.image_path.is_file():
            raise CameraOpenError(f"Image file not found: {self.image_path}")

        try:
            frame = cv2.imread(
                str(self.image_path),
                cv2.IMREAD_COLOR,
            )
        except cv2.error as err:
            raise CameraOpenError(f"Failed to decode image: {self.image_path}") from err

        if frame is None or frame.size == 0:
            raise CameraOpenError(f"Cannot read image: {self.image_path}")

        if frame.shape != (self.height, self.width, 3):
            raise CameraOpenError(
                f"Expected image dimensions "
                f"{self.width}x{self.height}, "
                f"got {frame.shape[1]}x{frame.shape[0]}."
            )

        self._frame = frame

    def read(self) -> np.ndarray:
        """Return an independent copy of the loaded BGR image."""

        if not self.is_open:
            raise FrameReadError(
                "Image source is not open. Call open() first."
            )

        return self._frame.copy()

    def close(self) -> None:
        """Release the cached image."""

        self._frame = None