from abc import ABC, abstractmethod
import numpy as np

class CameraInterface(ABC):
    @abstractmethod
    def open(self) -> None:
        """Opens the camera for capturing frames."""
        pass

    @abstractmethod
    def read(self) -> np.ndarray:
        """Captures a frame from the camera and returns it as a NumPy array."""
        pass

    @abstractmethod
    def close(self) -> None:
        """Closes the camera and releases any resources."""
        pass

    @property
    @abstractmethod
    def is_open(self) -> bool:
        """Returns True if the camera is open, False otherwise."""
        pass