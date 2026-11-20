class RobotError(Exception):
    """Base exception for robot-related errors"""

class EmergencyStopError(RobotError):
    """Raised when robot operation is blocked by E-stop"""

class OperatorAbortError(RobotError):
    """Operator requested cycle abort after E-stop recovery."""