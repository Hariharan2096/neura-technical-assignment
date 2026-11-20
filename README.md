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

| Design decision | Description |
| --- | --- |
| Modular software architecture  | For this project, I have broken down the overall application workflow into distinct modules and implemented them separately. This makes the project easier to maintain, test, debug, and extend without affecting unrelated modules|
| Abstraction interface | Abstract interfaces are defined for the robot and camera modules, with concrete implementations extending these interfaces. This design enables seamless replacement of simulated components with real hardware and provides the flexibility to integrate additional hardware in the future without significant changes to the existing application logic |
| Estop simulation and operator inputs | The safety design uses an E-stop event to interrupt the simulated operations and a recovery callback to request operator acknowledgement to mimic the real time operating conditions |
| Coordinate calibration | An affine transformation-based calibration approach is used to map the detected object positions from camera coordinates to robot coordinates. | 
| Configurable simulation | |


## Known limitations

The following observations reflect the **current uploaded source**, not proposed future changes:

1. **E-stop state mismatch:** `FakeRobot.is_emergency_stopped` reads `_estop_event`, and `trigger_emergency_stop()` / `release_emergency_stop()` set/clear that event; however, `_check_safety()` checks `_emergency_stopped`, which is initialized `False` and is not updated by those methods. This makes E-stop enforcement inconsistent. `_check_safety()` should check the event-backed property.
2. **Operator-abort handler issues in uploaded snapshot:** `RobotSequence.run()` catches `RobotError` before `OperatorAbortError`, making the latter unreachable because it subclasses `RobotError`. The handler also uses `self.robot_is_emergency_stopped` instead of `self.robot.is_emergency_stopped`. **Fix:** catch `OperatorAbortError` before `RobotError`, check the robot property, verify release before homing, and return `OPERATOR_ABORTED` on successful homing. See [Operator abort handling](#operator-abort-handling).
3. **Workspace enforcement:** `PixelWorkspace` is defined in `pick_place_app.py`, but the object-processing loop does not currently apply a workspace bounds check before transforming and executing a detected object.
4. **No dashboard:** The uploaded project does not contain a working Streamlit dashboard. Streamlit is not listed in `pyproject.toml`.
5. **Single-frame processing:** Image and webcam modes process one frame per CLI invocation. There is no continuous camera tracking or live robot feedback.
6. **Simulation-only homing and placement:** Home and place poses are fixed examples; collision avoidance, physical interlocks, and safe path planning are not implemented.

## Future Scopes

---

## Written Questions:

1. **Define Edge cases and error handling methods that you would like to integrate
and how?**  
xxx


2. **A robot consistently picks 2 mm away from the target. Where do you look
first?**  
Since the nature of the error is steady state, first I would look at the tool center point defined in the robot software and verify if it is calculated correctly based on the end effector design.

3. **What should the software do when an emergency stop is released?**  
When the emergency stop is released, the software should wait for the operator to acknowledge the pressing of the estop and make sure that it is safe to run the robot again.
