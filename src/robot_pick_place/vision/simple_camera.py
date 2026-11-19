import cv2
import time
import numpy as np
from loguru import logger

from .camera_interface import CameraInterface
from .load_camera_config import CameraConfig
from .exceptions import CameraError, CameraOpenError, FrameReadError

# Main camera interface
class SimpleCamera(CameraInterface):
    def __init__(self, config: CameraConfig):
        self.camera_index = config.device["index"]
        self.width = config.device["width"]
        self.height = config.device["height"]
        self.fps = config.device["fps"]

        self.max_open_attempts = config.acquisition["max_open_attempts"]
        self.max_read_attempts = config.acquisition["max_read_attempts"]
        self.retry_delay = config.acquisition["retry_delay"]

        self._capture = None

        logger.info(f"Webcamera opened with index {self.camera_index}")

    @property
    def is_open(self) -> bool:
        return self._capture is not None and self._capture.isOpened()

    def open(self) -> None:
        """Open the simple webcam based no of retries specified in the config."""

        if self.is_open:
            return  # Already open

        for attempt in range(1, self.max_open_attempts + 1):
            capture = None  # Reset capture for each attempt

            try:
                logger.info(
                    f"Opening camera {self.camera_index} (attempt {attempt}/{self.max_open_attempts})"
                )

                capture = cv2.VideoCapture(self.camera_index)

                if capture.isOpened():
                    capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)                
                    capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)                    
                    capture.set(cv2.CAP_PROP_FPS, self.fps)

                    self._capture = capture

                    logger.info("Camera successfully initialized.")
                    return

            except cv2.error as e:
                logger.warning(f"OpenCV error while opening camera: {e}")

            finally:
                if capture is not None and capture is not self._capture:
                    capture.release()  # Release the temporary capture if it was created

            if attempt < self.max_open_attempts:
                logger.warning("Retrying camera connection after delay...")            
                time.sleep(self.retry_delay)

        raise CameraOpenError(
            f"Failed to open camera {self.camera_index} after {self.max_open_attempts} attempts."
        )


    def read(self) -> np.ndarray:
        """Read a frame from the webcam based on the number of retries specified in the config."""

        if not self.is_open:
            raise CameraError("Camera is not open. Call 'open()' before reading frames.")

        for attempt in range(1, self.max_read_attempts + 1):

            try:
                success, frame = self._capture.read()

                if (
                    success
                    and isinstance(frame, np.ndarray)
                    and frame.ndim == 3
                    and frame.shape[2] == 3
                    and frame.size > 0
                    and frame.shape[:2] == (self.height, self.width)
                ):
                    return frame

            except cv2.error as e:
                logger.warning(f"OpenCV error while reading frame: {e}")

            logger.warning(
                f"Failed to read frame"
                f"(attempt {attempt}/{self.max_read_attempts})"
            )

            if attempt < self.max_read_attempts:
                time.sleep(self.retry_delay)

        raise FrameReadError(
            f"Failed to read a valid {self.height}x{self.width} frame after {self.max_read_attempts} attempts."
        )
    
            
    def close(self) -> None:
        """Release the webcam."""

        if self._capture is not None:
            self._capture.release()
            self._capture = None

