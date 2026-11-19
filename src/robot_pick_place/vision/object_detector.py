import math
import cv2
import numpy as np

from robot_pick_place.models import DetectedObject

class ObjectDetector:
    """Detect dark rectangular objects on a light background."""

    def __init__(
        self,
        min_area: float = 500.0,
        max_area: float = 50000.0,
        min_rectangularity: float = 0.85,
        blur_kernel_size: int = 5,
    ) -> None:
        if not 0 < min_area < max_area:
            raise ValueError(
                "Area limits must satisfy 0 < min_area < max_area"
            )

        if not 0 < min_rectangularity <= 1:
            raise ValueError(
                "min_rectangularity must be in [0, 1]"
            )


        if (
            isinstance(blur_kernel_size, bool)
            or not isinstance(blur_kernel_size, int)
            or blur_kernel_size <= 0
            or blur_kernel_size % 2 == 0
        ):
            raise ValueError(
                "blur_kernel_size must be a positive odd integer"
            )

        self.min_area = min_area
        self.max_area = max_area
        self.min_rectangularity = min_rectangularity
        self.blur_kernel_size = blur_kernel_size

    @staticmethod
    def _validate_image(image: np.ndarray) -> None:
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


    @staticmethod
    def _long_axis_angle(
        corners: np.ndarray,
    ) -> float:
        """Calculate long-axis angle from rectangle corners."""

        edge1 = corners[1] - corners[0]
        edge2 = corners[2] - corners[1]

        length1 = np.linalg.norm(edge1)
        length2 = np.linalg.norm(edge2)

        long_edge = edge1 if length1 >= length2 else edge2

        angle = math.degrees(
            math.atan2(
                float(long_edge[1]),
                float(long_edge[0]),
            )
        )

        return (angle + 90.0) % 180.0 - 90.0

    def detect(
        self,
        image: np.ndarray,
    ) -> list[DetectedObject]:
        """Return detected rectangles sorted by image position."""

        # Validate image frame
        self._validate_image(image)

        # Convert BGR to greyscale image
        gray = cv2.cvtColor( 
            image, 
            cv2.COLOR_BGR2GRAY,
        )

        # Apply Gaussian blur for image smoothening
        blurred = cv2.GaussianBlur( 
            gray, 
            (self.blur_kernel_size, self.blur_kernel_size), 
            0,
        )

        # Binary image conversion
        _, binary = cv2.threshold(
            blurred,
            0,
            255,
            cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU,
        )

        # Find contours in the image
        contours, _ = cv2.findContours(
            binary,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE,
        )

        candidates = []

        for contour in contours:
            area = cv2.contourArea(contour)

            # Applpy area filter
            if not self.min_area <= area <= self.max_area:
                continue

            rect = cv2.minAreaRect(contour)
            (center_u, center_v), (width, height), _ = rect

            # Apply size filter
            if width <= 0 or height <= 0:
                continue

            rectangle_area = width * height
            rectangularity = area / rectangle_area

            # Apply rectangularity filter
            if rectangularity < self.min_rectangularity:
                continue

            corners_array = cv2.boxPoints(rect)

            angle_deg = self._long_axis_angle(
                corners_array
            )

            corners = tuple(
                (float(point[0]), float(point[1]))
                for point in corners_array
            )

            candidates.append(
                (
                    float(center_u),
                    float(center_v),
                    float(angle_deg),
                    corners,
                    float(area),
                )
            )

        # Deterministic order: top-to-bottom, then left-to-right.
        candidates.sort(key=lambda item: (item[1], item[0]))

        return [
            DetectedObject(
                object_id=index,
                center_u=center_u,
                center_v=center_v,
                angle_deg=angle_deg,
                corners=corners,
                area=area,
            )
            for index, (
                center_u,
                center_v,
                angle_deg,
                corners,
                area,
            ) in enumerate(candidates, start=1)
        ]
