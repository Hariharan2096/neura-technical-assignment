from pathlib import Path

import cv2
import numpy as np

from robot_pick_place.vision.object_detector import DetectedObject

class ImageAnnotator:
    """Draw detected objects and save annotated images."""

    def annotate(
        self,
        image: np.ndarray,
        objects: list[DetectedObject],
    ) -> np.ndarray:
        if (
            not isinstance(image, np.ndarray)
            or image.dtype != np.uint8
            or image.ndim != 3
            or image.shape[2] != 3
            or image.shape[0] == 0
            or image.shape[1] == 0
        ):
            raise ValueError(
                "Expected a non-empty uint8 BGR image"
            )

        annotated = image.copy()

        for obj in objects:
            corners = np.array(
                obj.corners,
                dtype=np.float32,
            ).reshape(4, 2)

            corners_int = np.rint(corners).astype(np.int32)

            cv2.polylines(
                annotated,
                [corners_int],
                isClosed=True,
                color=(0, 255, 0),
                thickness=2,
            )

            center = (
                int(round(obj.center_u)),
                int(round(obj.center_v)),
            )

            # Draw orientation along the rectangle's long axis.
            theta = np.deg2rad(obj.angle_deg)
            line_length = 35

            endpoint = (
                int(round(
                    obj.center_u
                    + line_length * np.cos(theta)
                )),
                int(round(
                    obj.center_v
                    + line_length * np.sin(theta)
                )),
            )

            cv2.line(
                annotated,
                center,
                endpoint,
                color=(255, 0, 0),
                thickness=2,
            )

            cv2.circle(
                annotated,
                center,
                radius=5,
                color=(0, 0, 255),
                thickness=-1,
            )


            label = (
                f"ID {obj.object_id}: "
                f"{obj.angle_deg:.1f} deg"
            )

            text_position = (
                max(0, center[0] - 35),
                max(15, center[1] - 20),
            )

            cv2.putText(
                annotated,
                label,
                text_position,
                cv2.FONT_HERSHEY_SIMPLEX,
                0.45,
                (0, 0, 0),
                2,
                cv2.LINE_AA,
            )

            cv2.putText(
                annotated,
                label,
                text_position,
                cv2.FONT_HERSHEY_SIMPLEX,
                0.45,
                (255, 255, 255),
                1,
                cv2.LINE_AA,
            )

        return annotated

    def save(
        self,
        image: np.ndarray,
        output_path: str | Path,
    ) -> Path:
        path = Path(output_path)

        if not path.suffix:
            raise ValueError(
                "Output path must have an image extension"
            )

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        try:
            success = cv2.imwrite(str(path), image)
        except cv2.error as exc:
            raise OSError(
                f"Failed to save annotated image: {path}"
            ) from exc

        if not success:
            raise OSError(
                f"Failed to save annotated image: {path}"
            )

        return path
