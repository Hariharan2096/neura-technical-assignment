from robot_pick_place.perception.camera_config import CameraConfig
from robot_pick_place.perception.simple_camera import SimpleCamera
import cv2

def main():
    # Initialize the webcam (0 is usually the built-in camera; try 1 or 2 for external
    #  USB cams)

    config = CameraConfig("config/camera_config.yaml")

    try:
        with SimpleCamera(config) as camera:
            if not camera.is_open:
                print("Failed to open the camera.")
                return

            while True:
                frame = camera.read()
                if frame is None:
                    print("Failed to read a frame from the camera.")
                    break

                cv2.imshow("Camera Feed", frame)

                # Exit on 'q' key press
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
    finally:
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()