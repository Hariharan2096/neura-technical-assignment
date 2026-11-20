# NEURA Robotics — Vision-Guided Pick-and-Place Simulation

A Python application that detects rectangular objects in an image, converts their image coordinates into simulated robot poses, and runs a pick-and-place sequence using a `FakeRobot`. The repository includes a command-line entry point, image-file and webcam based acquisition, annotated image output, configurable motion/gripper delays, simulated grip failures, and a **prototype** random emergency-stop (E-stop) recovery workflow with operator acknowledgement, Continue, and Abort decisions.

## Requirements

- Python 3.10+ (the code uses modern type annotations)
- A camera only when using `--source webcam`
- Python dependencies declared in `pyproject.toml`: `numpy`, `opencv-python`, `PyYAML`, `loguru`
- `pytest` to run the tests (install separately)

## Setup

Run these commands from the repository root, the folder containing `pyproject.toml`:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
python -m pip install pytest
```

## Quick start

### Process the included test image

```powershell
python -m robot_pick_place.main --source image --input asset/input/test.png --output asset/output/annotated.png
```
This application has an option to load already saved test images from the asset folder and use it for the simulation of robot pick place application.

### Capture a frame from a webcam

```powershell
python -m robot_pick_place.main --source webcam --output asset/output/webcam_annotated.png
```

The webcam is configured in `config/camera_config.yaml`. The application acquires one frame per run, rather than processing a continuous video stream.

### Enable random simulated E-stop

```powershell
python -m robot_pick_place.main --source image --input asset/input/test.png --output asset/output/annotated.png --simulate-estop --estop-probability 0.2
```

This enables a random E-stop trigger during the actual robot sequence. The probability is evaluated per eligible robot action such as move_to(), gripper_open(), and gripper_close(). 

## Command-line arguments

| Argument | Default | Description |
| --- | --- | --- |
| `--source {image,webcam}` | `image` | Select image-file or webcam acquisition. |
| `--input PATH` | None | Required when `--source image` is selected. |
| `--output PATH` | `output/annotated.png` | Location for the annotated image. |
| `--simulate-estop` | Off | Enable random simulated E-stop injection and the CLI recovery callback. |
| `--estop-probability FLOAT` | `0.15` | Probability from `0.0` to `1.0` at each eligible robot operation. |
| `-h`, `--help` | — | Show CLI help. |

The default output path is `output/annotated.png`, which is **different** from the checked-in example output at `asset/output/annotated.png`. Supply `--output asset/output/annotated.png` to overwrite the included example.

## Main Design Decisions

| Design decision | Reasoning |
| --- | --- |
| Modular software architecture  | For this project, I have broken down the overall application workflow into distinct modules and implemented them separately. This makes the project easier to maintain, test, debug, and extend without affecting unrelated modules. |
| Abstraction interface | Abstract interfaces are defined for the robot and camera modules, with concrete implementations extending these interfaces. This design enables seamless replacement of simulated components with real hardware and provides the flexibility to integrate additional hardware in the future without significant changes to the existing application logic. |
| E-stop simulation and operator Interaction | 	The safety mechanism uses an E-stop event to interrupt simulated robot operations and a recovery callback to obtain operator acknowledgement, closely replicating real-world emergency stop and recovery scenarios. |
| Coordinate calibration | An affine transformation-based calibration approach is used to map the detected object positions from camera coordinates to robot coordinates. Further, the calibration parameters can be updated without core application logic. | 

---

## Written Questions:

1. **Define Edge cases and error handling methods that you would like to integrate
and how?**  
For this application, the common edge cases that i would define are unsuccessful object detection due to external factors such as specular reflection or similar, object lying partly outside the camera field of view, and object slipping from gripper during robot movement. Further, I would like to integrate error handling methods for communication error, Process errors, Hardware malfunctions such as device failures, software based errors such as wrong configuration or similar. The error handling methods are integrated as separate functions and are executed everytime at the start of the program cycle to catch the errors beforehand so that the system does not execute a movement.

2. **A robot consistently picks 2 mm away from the target. Where do you look
first?**  
Since the nature of the error is steady state, first I would look at the tool center point defined in the robot software and verify if it is calculated correctly based on the end effector design. Once the TCP has been verified and the issue still persists, secondly, the transformation matrix from camera to robot coordinates can also be checked and verified. 

3. **What should the software do when an emergency stop is released?**  
When the emergency stop is released, the software should wait for the operator to acknowledge the pressing of the estop and make sure that it is safe to run the robot again. First, the software should raise an alarm that the emergency stop has been pressed and then should wait for acknowledgement.
