import argparse
import logging
import sys
from pathlib import Path
from loguru import logger

from robot_pick_place.application.pick_place_app import PickPlaceApplication
from robot_pick_place.application.pick_place_cycle import PickPlaceCycle
from robot_pick_place.geometry.calibration import CoordinateTransformer
from robot_pick_place.geometry.pose_generator import PoseGenerator
from robot_pick_place.models import RobotPose
from robot_pick_place.robot.fake_robot import FakeRobot
from robot_pick_place.vision.annotator import ImageAnnotator
from robot_pick_place.vision.image_file_camera import ImageFileCamera
from robot_pick_place.vision.simple_camera import SimpleCamera
from robot_pick_place.vision.object_detector import ObjectDetector

def parse_args(
        argv: list[str] | None = None,
) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="NEURA Robotics"
    )

    parser.add_argument(
        "--source",
        choices=("image", "webcam"),
        default="image",
        help="Image acquisition source",
    )

    parser.add_argument(
        "--input",
        type=Path,
        help="Input image path for image source",
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=Path("output/annotated.png"),
        help="Annotated output image path",
    )

    parser.add_argument(
        "--camera-index",
        type=int,
        default=0,
        help="Webcam device index"
    )

    parser.add_argument(
        "--log-level",
        choices=("DEBUG", "INFO", "WARNING", "ERROR"),
        default="INFO",
    )
    args = parser.parse_args(argv)

    if args.source == "image" and args.input is None:
        parser.error(
            "--input required when source is image"
        )

    return args


def create_transformer() -> CoordinateTransformer:
    """Create transformer using assignment calibration."""

    return CoordinateTransformer(
        pixel_points=[
            (100, 100),
            (540, 100),
            (540, 380),
            (100, 380),
        ],
        robot_points=[
            (150, -150),
            (150, 70),
            (290, 70),
            (290, -150),
        ],
    )

def create_camera(args: argparse.Namespace):
    """Create the requested camera implementation."""

    if args.source == "image":
        return ImageFileCamera(
            image_path=args.input,
            width=640,
            height=480,
        )

    if args.source == "webcam":
        return SimpleCamera(
            camera_index = args.camera_index,
            width=640,
            height=480,
        )

    raise ValueError(
        "Webcam source is not yet wired into main.py"
    )


def create_application(
    args: argparse.Namespace,
) -> PickPlaceApplication:
    """Assemble the application dependencies."""

    camera = create_camera(args)

    detector = ObjectDetector(
        min_area=500,
        max_area=50000,
        min_rectangularity=0.85,
        min_aspect_ratio=1.15,
    )

    annotator = ImageAnnotator()

    transformer = create_transformer()

    pose_generator = PoseGenerator(
        pick_height=20.0,
        approach_height=70.0,
    )

    home_pose = RobotPose(
        x=200.0,
        y=0.0,
        z=150.0,
        yaw=0.0,
    )

    robot = FakeRobot(
        home_pose=home_pose,
    )

    # Simulation assumption: a part is available.
    robot.set_part_available(True)


    cycle = PickPlaceCycle(
        robot=robot,
        part_timeout=5.0,
        poll_interval=0.1,
        max_grip_retries=2,
    )

    # Example simulated placement location.
    # These coordinates must be validated for a real robot.
    place_pose = RobotPose(
        x=260.0,
        y=30.0,
        z=20.0,
        yaw=0.0,
    )

    place_approach_pose = RobotPose(
        x=260.0,
        y=30.0,
        z=70.0,
        yaw=0.0,
    )

    return PickPlaceApplication(
        camera=camera,
        detector=detector,
        annotator=annotator,
        transformer=transformer,
        pose_generator=pose_generator,
        cycle=cycle,
        place_pose=place_pose,
        place_approach_pose=place_approach_pose,
    )

def main(argv: list[str] | None = None) -> int:
    """Execute the application and return an exit code."""

    args = parse_args(argv)

    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format=(
            "%(asctime)s | %(levelname)s | "
            "%(name)s | %(message)s"
        ),
    )

    try:
        app = create_application(args)

        result = app.run(
            output_path=args.output,
        )

    except (Exception) as exc:
        logger.exception(
            "Application execution failed: %s",
            exc,
        )
        return 1

    print()
    print("NEURA Robotics - Execution Summary")
    print("----------------------------------")
    print(f"Detected objects : {result.detected_count}")
    print(f"Successful picks : {result.successful_picks}")
    print(f"Failed picks     : {result.failed_picks}")
    print(f"Aborted          : {result.aborted}")
    print(f"Annotated image  : {result.annotated_image_path}")

    print()
    print("Object Results")
    print("----------------------------------")

    for item in result.object_results:
        print(
            f"Object {item.object_id}: "
            f"{item.status} "
            f"(attempts={item.grip_attempts})"
        )

        if item.message:
            print(f"  {item.message}")

    if result.aborted:
        return 2

    if (
        result.detected_count == 0
        or result.failed_picks > 0
    ):
        return 3

    return 0


if __name__ == "__main__":
    sys.exit(main())
