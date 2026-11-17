class CameraError(Exception):
    """Base exception for camera-related errors."""

class CameraOpenError(CameraError):
    """Raised when the camera cannot be opened after multiple attempts."""

class FrameReadError(CameraError):
    """Raised when a frame cannot be read from the camera after multiple attempts."""

class CameraConfigError(ValueError):
    """Raised when camera configuration is invalid."""