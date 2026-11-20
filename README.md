# NEURA Robotics — Vision-Guided Pick-and-Place Simulation

A Python application that detects rectangular objects in an image, converts their image coordinates into simulated robot poses, and runs a pick-and-place sequence using a `FakeRobot`. The repository includes a command-line entry point, image-file and webcam based acquisition, annotated image output, configurable motion/gripper delays, simulated grip failures, and a **prototype** random emergency-stop (E-stop) recovery workflow with operator acknowledgement, Continue, and Abort decisions.

> **Simulation only.** This project does not control a physical robot and does not implement safety-rated emergency stopping, reset, or homing. Calibration, workspace limits, motion paths, and recovery actions must be validated before any real-robot use.

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
This application has an option to load already saved images from the asset folder and use it for the robot pick place simulation.

```powershell
python -m robot_pick_place.main --source image --input asset/input/test.png --output asset/output/annotated.png
```

### Capture a frame from a webcam

```powershell
python -m robot_pick_place.main --source webcam --output asset/output/webcam_annotated.png
```

The webcam is configured in `config/camera_config.yaml`. The application acquires **one frame per run**, rather than processing a continuous video stream.

### Enable random simulated E-stop

```powershell
python -m robot_pick_place.main --source image --input asset/input/test.png --output asset/output/annotated.png --simulate-estop --estop-probability 0.2
```

This enables a random E-stop check at the start of simulated motion, gripper-open, and gripper-close operations. The probability is evaluated per eligible operation, **not** once per application or once per detected object. The code uses a fixed random seed of `15` in `create_application()`, so the sequence of E-stop decisions is reproducible for the same execution path. There is currently **no `--estop-seed` CLI argument**.

**Important:** The uploaded project snapshot predates the two fixes discussed for E-stop state consistency and operator-abort exception handling. The workflow below describes the intended behavior **after those fixes are applied**. See [Operator abort handling](#operator-abort-handling) and [Known limitations](#known-limitations).

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

## Inputs

### Image input

- The `ImageFileCamera` loads a single image from the `--input` path.
- It expects an 8-bit, three-channel **640 × 480** image; an image of a different size raises a camera error.
- OpenCV processes the frame in BGR format.
- The included sample is `asset/input/test.png`.

### Webcam input

`SimpleCamera` uses OpenCV and the following settings in `config/camera_config.yaml`:

| Setting | Value |
| --- | --- |
| Camera index | `0` |
| Frame width × height | `640 × 480` |
| Requested frame rate | `30 FPS` |
| Maximum open attempts | `5` |
| Maximum read attempts | `3` |
| Retry delay | `0.5 s` |

### Object detection assumptions

The detector is designed for **dark rectangular objects against a light background**. It uses grayscale conversion, Gaussian blur, inverse Otsu thresholding, external contours, area filtering, and rectangularity filtering. The `main.py` configuration uses:

- Minimum contour area: `50`
- Maximum contour area: `15,000`
- Minimum rectangularity: `0.85`
- Gaussian blur kernel: `3 × 3`

Detected objects receive sequential IDs after sorting top-to-bottom and then left-to-right. Each detection includes an image center, orientation, corners, and contour area.

## Application workflow

```text
CLI arguments
    |
    v
ImageFileCamera or SimpleCamera
    |
    v
Acquire one 640x480 frame
    |
    v
ObjectDetector -> rectangular objects
    |
    v
ImageAnnotator -> save annotated image
    |
    v
For each detected object (sorted image order):
    |-- Pixel center and angle -> robot XY and yaw
    |-- PoseGenerator -> pick and approach poses
    |-- RobotSequence.run(ProcessPoses)
    |     |-- Check E-stop and wait for part
    |     |-- Open gripper, approach, descend, close gripper
    |     |-- Check grip; retry if needed
    |     |-- Retreat, move to place, release part
    |     `-- Return to home pose
    `-- Record per-object result; abort on critical status
    |
    v
Print execution summary and return exit code
```

### Coordinate transformation

`CoordinateTransformer` uses four hard-coded pixel-to-robot calibration correspondences in `main.py`:

| Pixel `(u, v)` | Robot `(X, Y)` |
| --- | --- |
| `(100, 100)` | `(150, -150)` |
| `(540, 100)` | `(150, 70)` |
| `(540, 380)` | `(290, 70)` |
| `(100, 380)` | `(290, -150)` |

The transformer estimates a 2D affine mapping and transforms detected object orientation into robot yaw. These coordinates are assignment-specific simulation values, not calibrated values for a physical robot.

### Robot poses and sequence

The application uses the following simulation parameters:

| Parameter | Value |
| --- | --- |
| Pick Z | `20.0` |
| Pick approach Z | `70.0` |
| Home pose `(x, y, z, yaw)` | `(200, 0, 150, 0)` |
| Place pose | `(260, 30, 20, 0)` |
| Place approach pose | `(260, 30, 70, 0)` |
| Part-available timeout | `5.0 s` |
| Part polling interval | `0.1 s` |
| Maximum grip retries | `2` (up to 3 attempts total) |

`main.py` sets simulated part availability to `True` before execution. A failed grip may be retried; exhausted retries return `GRIP_FAILED`. A successful pick-and-place cycle returns to the home pose.

### Simulated robot timing and grip outcomes

The `FakeRobot` constructor accepts configurable motion, gripper-open, and gripper-close delays. In the current `main.py`, **each is set to `1.0 s`**. The implementation uses a `threading.Event` to allow the delay to wake when an E-stop is triggered.

The robot supports a queue of predefined grip results for tests and a random fallback. The application factory configures `grip_success_probability=0.8` for random grip attempts when the predefined queue is empty.

## E-stop and operator recovery (prototype)

With `--simulate-estop`, `FakeRobot` can inject an E-stop during an eligible operation. Its recovery decorator (`safety/robot_estop_recovery.py`) invokes a CLI callback in `main.py` when an `EmergencyStopError` occurs.

The **intended** operator interaction is:

1. The simulated operation stops and the CLI displays an E-stop warning.
2. The operator is prompted: `Acknowledge and authorize simulated E-stop release? [y/n]`.
3. Answering `y` calls `release_emergency_stop()`; answering `n` leaves the prompt active.
4. The operator selects `1` to **continue** or `2` to **abort**.
5. **Continue** retries the interrupted robot operation, rather than restarting the whole pick-and-place cycle.
6. **Abort** raises `OperatorAbortError`. After confirming the E-stop is released, `RobotSequence.run()` commands `move_home()` and returns `CycleStatus.OPERATOR_ABORTED`; `PickPlaceApplication` marks the run aborted and stops processing further objects. If E-stop is still active, no home movement is attempted. If home movement fails, the sequence reports the relevant robot or E-stop error.

The simulator tracks whether a random E-stop has already been injected, so its random injection is designed to happen **at most once per `FakeRobot` instance**. An external E-stop may still be triggered independently.

### Operator abort handling

`OperatorAbortError` is a subclass of `RobotError`. Therefore, the exception handlers in `RobotSequence.run()` must be ordered **from specific to general**:

```python
except OperatorAbortError as exc:
    # Confirm E-stop is released, then attempt simulated return home.
    ...
except EmergencyStopError as exc:
    # Report an active/unrecovered E-stop; do not command motion.
    ...
except RobotError as exc:
    # Handle remaining robot failures.
    ...
```

In the operator-abort handler, the robot state check must use **`self.robot.is_emergency_stopped`**, not `self.robot_is_emergency_stopped`.

After acknowledgement and simulated E-stop release, the expected outcomes are:

| Operator choice or recovery outcome | Sequence result | Application behavior |
| --- | --- | --- |
| Continue | Normal cycle result if the retried operation succeeds | Continue the current cycle and remaining objects |
| Abort, return home succeeds | `OPERATOR_ABORTED` | Mark `aborted=True`; do not process remaining objects |
| Abort while E-stop remains active | `EMERGENCY_STOPPED` | No homing; abort application |
| E-stop occurs during return home | `EMERGENCY_STOPPED` | Stop and abort application |
| Other robot failure during return home | `ROBOT_ERROR` | Abort application and report failure |

An acknowledged operator abort is an intentional stop, so successful homing should be recorded through the sequence result and logger, **not raised as a new robot alarm**. Errors and unsafe recovery conditions may still raise alarms.

The application must include `CycleStatus.OPERATOR_ABORTED` alongside `EMERGENCY_STOPPED` and `ROBOT_ERROR` in its abort-status check. The uploaded snapshot already includes this application-level status check.

**Implementation status:** The uploaded ZIP still contains the old handler ordering and incorrect property reference. Apply the corrections described above before relying on this workflow. The README documents the corrected behavior as a target, not as a verified tested feature.

**This is not a safety-certified recovery procedure.** A real robot must not automatically resume or move home based solely on a software acknowledgement.

## Outputs

### Annotated image

The annotated image is written to the path passed through `--output`. It is saved **before** robot sequence execution, so it can exist even if a later pick fails or the application aborts. The annotator draws object outlines, center markers, orientation indicators, and object labels.

### Console summary

The CLI prints:

```text
NEURA Robotics - Execution Summary
----------------------------------
Detected objects : ...
Successful picks : ...
Failed picks     : ...
Aborted          : ...
Annotated image  : ...

Object Results
----------------------------------
Object 1: SUCCESS (attempts=1)
  Pick-and-place completed
```

Each object result contains its ID, status, grip-attempt count, and message. Status values defined by `RobotSequence` include `SUCCESS`, `PART_TIMEOUT`, `GRIP_FAILED`, `EMERGENCY_STOPPED`, `ROBOT_ERROR`, and `OPERATOR_ABORTED`.

### Exit codes

| Code | Meaning |
| --- | --- |
| `0` | At least one object was detected, no recorded picks failed, and the application was not aborted. |
| `1` | Unhandled exception during application construction or execution. |
| `2` | Application result indicates an aborted run. |
| `3` | No objects detected, or one or more pick operations failed without an application abort. |

Invalid command-line arguments are rejected by `argparse` before application execution.

## Project structure

```text
Neura Technical Assignment/
├── asset/
│   ├── input/test.png
│   └── output/annotated.png
├── config/camera_config.yaml
├── pyproject.toml
├── README.md
├── src/robot_pick_place/
│   ├── main.py
│   ├── models.py
│   ├── application/pick_place_app.py
│   ├── geometry/
│   │   ├── calibration.py
│   │   └── pose_generator.py
│   ├── robot/
│   │   ├── exceptions.py
│   │   ├── fake_robot.py
│   │   ├── robot_interface.py
│   │   └── robot_sequence.py
│   ├── safety/robot_estop_recovery.py
│   └── vision/
│       ├── annotator.py
│       ├── camera_interface.py
│       ├── image_file_camera.py
│       ├── load_camera_config.py
│       ├── object_detector.py
│       └── simple_camera.py
└── tests/
    ├── test_main.py
    ├── test_fake_robot.py
    ├── test_robot_sequence.py
    ├── test_pick_place_app.py
    └── ...
```

## Testing

Install the package and `pytest`, then run:

```powershell
python -m pytest -v
```

To run a specific area:

```powershell
python -m pytest tests/test_fake_robot.py tests/test_robot_sequence.py -v
```

The test suite includes camera loading/configuration, object detection, annotation, calibration, pose generation, simulated robot operations, sequence execution, CLI, and application integration. Tests that instantiate a `FakeRobot` without overriding its delays may take longer because the class defaults to a nonzero motion delay.

## Known limitations

The following observations reflect the **current uploaded source**, not proposed future changes:

1. **E-stop state mismatch:** `FakeRobot.is_emergency_stopped` reads `_estop_event`, and `trigger_emergency_stop()` / `release_emergency_stop()` set/clear that event; however, `_check_safety()` checks `_emergency_stopped`, which is initialized `False` and is not updated by those methods. This makes E-stop enforcement inconsistent. `_check_safety()` should check the event-backed property.
2. **Operator-abort handler issues in uploaded snapshot:** `RobotSequence.run()` catches `RobotError` before `OperatorAbortError`, making the latter unreachable because it subclasses `RobotError`. The handler also uses `self.robot_is_emergency_stopped` instead of `self.robot.is_emergency_stopped`. **Fix:** catch `OperatorAbortError` before `RobotError`, check the robot property, verify release before homing, and return `OPERATOR_ABORTED` on successful homing. See [Operator abort handling](#operator-abort-handling).
3. **Workspace enforcement:** `PixelWorkspace` is defined in `pick_place_app.py`, but the object-processing loop does not currently apply a workspace bounds check before transforming and executing a detected object.
4. **No dashboard:** The uploaded project does not contain a working Streamlit dashboard. Streamlit is not listed in `pyproject.toml`.
5. **Single-frame processing:** Image and webcam modes process one frame per CLI invocation. There is no continuous camera tracking or live robot feedback.
6. **Simulation-only homing and placement:** Home and place poses are fixed examples; collision avoidance, physical interlocks, and safe path planning are not implemented.

## Troubleshooting

- **`--input required when source is image`:** Supply `--input asset/input/test.png` or use `--source webcam`.
- **Image size error:** Ensure the input image is exactly 640 × 480 pixels with three color channels.
- **Webcam cannot open:** Check `config/camera_config.yaml`, camera permissions, and whether another application is using the device.
- **Annotated output appears in an unexpected folder:** Pass `--output asset/output/annotated.png`; otherwise the default is `output/annotated.png`.
- **Random E-stop behavior repeats:** The seed is hard-coded to `15` in `main.py`. This is intentional for repeatable simulation, but currently cannot be overridden via CLI.
- **E-stop recovery behaves unexpectedly:** Verify that `_check_safety()` reads the same event used by trigger/release, and that `OperatorAbortError` is caught before `RobotError`. See [Operator abort handling](#operator-abort-handling) and [Known limitations](#known-limitations).

---

**Scope:** A software-only technical assignment demonstrating modular vision processing, coordinate transformation, robot sequence orchestration, simulation, error handling, and operator-recovery concepts.
