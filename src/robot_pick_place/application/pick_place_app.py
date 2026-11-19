from loguru import logger
from dataclasses import dataclass
from pathlib import Path

from robot_pick_place.models import RobotPose
from robot_pick_place.geometry.calibration import CoordinateTransformer
from robot_pick_place.geometry.pose_generator import PoseGenerator
from robot_pick_place.robot.robot_sequence import CycleStatus, RobotSequence, ProcessPoses
from robot_pick_place.vision.camera_interface import CameraInterface
from robot_pick_place.vision.object_detector import ObjectDetector
from robot_pick_place.vision.annotator import ImageAnnotator

@dataclass(frozen=True)
class PixelWorkspace:
    min_u: float = 100.0
    max_u: float = 540.0
    min_v: float = 100.0
    max_v: float = 380.0

    def contains(self, u: float, v: float) -> bool:
        return (
            self.min_u <= u <= self.max_u
            and self.min_v <= v <= self.max_v
        )

@dataclass(frozen=True)
class ObjectExecutionResult:
    object_id: int
    status: str
    message: str
    grip_attempts: int = 0

@dataclass(frozen=True)
class ApplicationResult:
    detected_count: int
    successful_picks: int
    failed_picks: int
    annotated_image_path: Path
    object_results: tuple[ObjectExecutionResult, ...]
    aborted: bool = False

class PickPlaceApplication:
    """Coordinate vision, pose planning and robot execution as one single application"""

    def __init__(
        self,
        camera: CameraInterface,
        detector: ObjectDetector,
        annotator: ImageAnnotator,
        transformer: CoordinateTransformer,
        pose_generator: PoseGenerator,
        seq: RobotSequence,
        place_pose: RobotPose,
        place_approach_pose: RobotPose,
    ) -> None:
        self.camera = camera
        self.detector = detector
        self.annotator = annotator
        self.transformer = transformer
        self.pose_generator = pose_generator
        self.seq = seq
        self.place_pose = place_pose
        self.place_approach_pose = place_approach_pose

    def run(
        self,
        output_path: str | Path,
    ) -> ApplicationResult:
        """Acquire one image and process its detected objects."""

        # 1. Acquire image.
        with self.camera:
            frame = self.camera.read()

        # 2. Detect objects.
        objects = self.detector.detect(frame)

        logger.info(f"Detected {len(objects)} rectangular objects")

        # 3. Save annotated image before robot execution.
        annotated = self.annotator.annotate(
            frame, objects
        )
        saved_path = self.annotator.save(
            annotated, output_path
        )

        results: list[ObjectExecutionResult] = []
        aborted = False

        # 4. Process objects in detector order.
        for obj in objects:
            if self.seq.robot.is_emergency_stopped:
                aborted = True
                logger.error("Emergency stop active")
                break

            # 5. Convert image coordinates into robot XY.
            robot_xy = self.transformer.pixel_to_robot(
                obj.center_u,
                obj.center_v,
            )

            robot_yaw = self.transformer.angle_to_robot(
                obj.angle_deg
            )

            # 6. Generate pick and approach poses.
            pick_poses = self.pose_generator.generate(
                x=robot_xy.x,
                y=robot_xy.y,
                yaw=robot_yaw,
            )

            # 7. Construct the robot execution plan.
            plan = ProcessPoses(
                pick_pose=pick_poses.pick,
                pick_approach_pose=pick_poses.approach,
                place_pose=self.place_pose,
                place_approach_pose=self.place_approach_pose,
            )

            # 8. Execute the pick-and-place cycle.
            seq_result = self.seq.run(plan)

            results.append(
                ObjectExecutionResult(
                    object_id=obj.object_id,
                    status=seq_result.status.name,
                    message=seq_result.message,
                    grip_attempts=seq_result.grip_attempts,
                )
            )

            logger.info(
                f"Object {obj.object_id}: {seq_result.status.name}"
            )

            # 9. Abort immediately on emergency stop
            # or a robot error with unknown safety state.
            if seq_result.status in (
                CycleStatus.EMERGENCY_STOPPED,
                CycleStatus.ROBOT_ERROR,
            ):
                aborted = True
                break

        successful = sum(
            result.status == CycleStatus.SUCCESS.name
            for result in results
        )

        failed = sum(
            result.status != CycleStatus.SUCCESS.name
            for result in results
        )

        return ApplicationResult(
            detected_count=len(objects),
            successful_picks=successful,
            failed_picks=failed,
            annotated_image_path=saved_path,
            object_results=tuple(results),
            aborted=aborted,
        )