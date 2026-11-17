from abc import ABC, abstractmethod

import numpy as np


class CameraInterface(ABC):
    """Abstract interface for acquiring BGR images."""

    @abstractmethod
    def open(self) -> None:
        """Open the image source.

        Raises:
            CameraError: If the source cannot be opened.
        """
        ...

    @abstractmethod
    def read(self) -> np.ndarray:
        """Read a valid BGR image.

        Raises:
            CameraError: If image acquisition fails.
        """
        ...

    @abstractmethod
    def close(self) -> None:
        """Release resources. Safe to call multiple times."""
        ...

    @property
    @abstractmethod
    def is_open(self) -> bool:
        """Return whether the image source is open."""
        ...

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
        return False