from robot_pick_place.geometry.calibration import CoordinateTransformer
from robot_pick_place.geometry.pose_generator import PoseGenerator

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

# Example detected object
pixel_u = 320
pixel_v = 240
image_angle = 45

robot_xy = transformer.pixel_to_robot(pixel_u, pixel_v)
robot_yaw = transformer.angle_to_robot(image_angle)

generator = PoseGenerator()
poses = generator.generate(
    x=robot_xy.x,
    y=robot_xy.y,
    yaw=robot_yaw,
)

print("Pick pose:", poses.pick)
print("Approach pose:", poses.approach)