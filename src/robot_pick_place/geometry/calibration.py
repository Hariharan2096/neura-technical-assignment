import numpy as np
from robot_pick_place.models import Point2D

class CoordinateTransformer:
    """Affine transformation from image coordinates to robot coordinates"""

    def __init__(
        self,
        pixel_points: list[tuple[float, float]],
        robot_points: list[tuple[float, float]]
    ) -> None:
        if len(pixel_points) != len(robot_points):
            raise ValueError("Calibration point counts must match")

        if len(pixel_points) < 3:
            raise ValueError("At least 3 point pairs are required")

        pixels = np.asarray(pixel_points, dtype=float)
        robots = np.asarray(robot_points, dtype=float)

        if (
            pixels.shape != (len(pixel_points), 2)
            or robots.shape != (len(robot_points), 2)
            or not np.isfinite(pixels).all()
            or not np.isfinite(robots).all()
        ):
            raise ValueError("Calibration points must be finite 2D values")

        # Each row represents: [u, v, 1]
        design = np.column_stack(
            (pixels, np.ones(len(pixels)))
        )

        # Check for collinear points
        if np.linalg.matrix_rank(design) < 3:
            raise ValueError("Calibration points must not be collinear")

        # Fit both robot X and Y simultaneously.
        coefficients, _, _, _ = np.linalg.lstsq(
            design, robots, rcond=None
        )

        # Shape (2, 3): [X, Y] = matrix @ [u, v, 1]
        self._matrix = coefficients.T

        # Needed to transform direction vectors.
        linear = self._matrix[:, :2]

        if abs(np.linalg.det(linear)) < 1e-12:
            raise ValueError(
                "Calibration transformation is not invertible"
            )


    def pixel_to_robot(self, u: float, v: float) -> Point2D:
        """Convert a pixel center to robot XY coordinates (mm)."""

        # Validate the pixel value and raise exception
        if not np.isfinite([u, v]).all():
            raise ValueError("Pixel coordinates must be finite")

        result = self._matrix @ np.array([u, v, 1.0])

        return Point2D(
            x=float(result[0]),
            y=float(result[1]),
        )

    def angle_to_robot(self, angle_deg: float) -> float:
        """Convert image-axis orientation into robot-frame yaw."""
        
        # Validate the value of angle
        if not np.isfinite(angle_deg):
            raise ValueError("Angle must be finite")

        # Convert deg to radians
        theta = np.deg2rad(angle_deg)

        # Direction vector along the object's long axis.
        image_direction = np.array([
            np.cos(theta),
            np.sin(theta),
        ])

        robot_direction = (
            self._matrix[:, :2] @ image_direction
        )

        yaw = np.degrees(
            np.arctan2(
                robot_direction[1],
                robot_direction[0],
            )
        )

        # A rectangle's long axis has 180-degree symmetry.
        return float((yaw + 90.0) % 180.0 - 90.0)