# import cv2

from robot_pick_place.vision.simple_camera import SimpleCamera
from robot_pick_place.vision.load_camera_config import CameraConfig
from robot_pick_place.geometry.calibration import CoordinateTransformer


# config = CameraConfig(config_path="config/camera_config.yaml")

# camera = SimpleCamera(
#     config=config
# )

# camera.open()

# frame = camera.read()

# cv2.imshow('Display', frame)

# cv2.waitKey(0)

# cv2.destroyAllWindows()

transformer = CoordinateTransformer(
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

print(transformer.pixel_to_robot(
    u=200.0,
    v=200.0
))

print(transformer.angle_to_robot(170))