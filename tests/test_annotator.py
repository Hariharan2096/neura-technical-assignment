
import cv2
import numpy as np

from robot_pick_place.vision.annotator import (
    ImageAnnotator,
)
from robot_pick_place.vision.object_detector import (
    DetectedObject,
)


def make_object():
    return DetectedObject(
        object_id=1,
        center_u=320.0,
        center_v=240.0,
        angle_deg=30.0,
        corners=(
            (270.0, 190.0),
            (370.0, 190.0),
            (370.0, 290.0),
            (270.0, 290.0),
        ),
        area=10000.0,
    )


def test_annotation_changes_output_not_input():
    image = np.full(
        (480, 640, 3),
        255,
        dtype=np.uint8,
    )
    original = image.copy()

    annotated = ImageAnnotator().annotate(
        image,
        [make_object()],
    )

    assert np.array_equal(image, original)
    assert not np.array_equal(annotated, original)


def test_annotation_marks_center():
    image = np.full(
        (480, 640, 3),
        255,
        dtype=np.uint8,
    )

    annotated = ImageAnnotator().annotate(
        image,
        [make_object()],
    )

    assert np.array_equal(
        annotated[240, 320],
        np.array([0, 0, 255], dtype=np.uint8),
    )


def test_save_annotated_image(tmp_path):
    image = np.full(
        (480, 640, 3),
        255,
        dtype=np.uint8,
    )

    annotator = ImageAnnotator()
    annotated = annotator.annotate(
        image,
        [make_object()],
    )

    output = tmp_path / "output" / "annotated.png"
    saved_path = annotator.save(annotated, output)

    assert saved_path.exists()

    loaded = cv2.imread(str(saved_path))
    assert loaded is not None
    assert np.array_equal(loaded, annotated)


def test_empty_detections_preserve_image():
    image = np.full(
        (480, 640, 3),
        255,
        dtype=np.uint8,
    )

    annotated = ImageAnnotator().annotate(image, [])

    assert np.array_equal(image, annotated)
    assert annotated is not image
