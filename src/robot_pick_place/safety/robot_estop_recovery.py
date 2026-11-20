from enum import Enum, auto
from functools import wraps

class RecoveryAction(Enum):
    CONTINUE =auto()
    ABORT = auto()

from robot_pick_place.robot.exceptions import (
    EmergencyStopError,
    OperatorAbortError,
)

def recoverable_operation(method):
    """Retry an interrupted simulated operation after recovery."""

    @wraps(method)
    def wrapper(self, *args, **kwargs):

        while True:
            try:
                return method(self, *args, **kwargs)

            except EmergencyStopError:
                # Preserve the existing abort behavior when
                # interactive recovery is not configured.
                if self.on_estop_recovery is None:
                    raise

                action = self.on_estop_recovery()

                if self.is_emergency_stopped:
                    raise EmergencyStopError(
                        "Recovery denied: E-stop remains active"
                    )

                if action == RecoveryAction.ABORT:
                    raise OperatorAbortError(
                        "Cycle aborted by operator"
                    )

                if action != RecoveryAction.CONTINUE:
                    raise ValueError(
                        "Invalid E-stop recovery action"
                    )

                # Retry the interrupted operation.
                # FakeRobot methods must only commit their
                # final state after successful completion.

    return wrapper