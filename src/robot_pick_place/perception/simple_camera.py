import cv2
import time
import numpy as np

from .camera_interface import CameraInterface
from .camera_config import CameraConfig

# Error handling for camera operations
class CameraError(Exception):
    """Base exception for camera-related errors."""

class CameraOpenError(CameraError):
    """Raised when the camera cannot be opened after multiple attempts."""

class FrameReadError(CameraError):
    """Raised when a frame cannot be read from the camera after multiple attempts."""

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

    @property
    def is_open(self) -> bool:
        return self._capture is not None and self._capture.isOpened()

    def open(self) -> None:
        """Open the simple webcam based no of retries specified in the config."""

        if self.is_open:
            return  # Already open

        for attempt in range(self.max_open_attempts + 1):
            print(
                f"Opening camera {self.camera_index}"
                f"(attempt {attempt + 1}/{self.max_open_attempts})..."
            )

            capture = cv2.VideoCapture(self.camera_index)

            if capture.isOpened():
                capture.set(
                    cv2.CAP_PROP_FRAME_WIDTH, self.width
                )
               
                capture.set(
                    cv2.CAP_PROP_FRAME_HEIGHT, self.height
                )
                
                capture.set(
                    cv2.CAP_PROP_FPS, self.fps
                )

                self._capture = capture

                print("Camera successfully initialized.")
                return

            capture.release()
            print("Camera unavailable. Retrying...")

            if attempt < self.max_open_attempts:
                time.sleep(self.retry_delay)

        raise CameraOpenError(
            f"Failed to open camera {self.camera_index} after {self.max_open_attempts} attempts."
        )


    def read(self) -> np.ndarray:
        """Read a frame from the webcam based on the number of retries specified in the config."""

        if not self.is_open:
            raise CameraError("Camera is not open. Call 'open()' before reading frames.")

        for attempt in range(self.max_read_attempts + 1):
            success, frame = self._capture.read()
            if success and frame is not None:
                return frame

            print(
                f"Failed to read frame"
                f"(attempt {attempt}/{self.max_read_attempts})"
            )

            if attempt < self.max_read_attempts:
                time.sleep(self.retry_delay)

        raise FrameReadError(
            f"Failed to read frame after {self.max_read_attempts} attempts."
        )
    
            
    def close(self) -> None:
        """Release the webcam."""

        if self._capture is not None:
            self._capture.release()
            self._capture = None    
    
    def __enter__(self):
        """Open the web camera when entering the context manager."""
        self.open()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Release the web camera when exiting the context manager."""
        self.close()

