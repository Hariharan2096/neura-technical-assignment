
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from robot_pick_place.main import (
    create_application,
    create_transformer,
    main,
    parse_args,
)


def test_parse_image_arguments():
    args = parse_args([
        "--source", "image",
        "--input", "objects.png",
        "--output", "annotated.png",
    ])

    assert args.source == "image"
    assert args.input == Path("objects.png")
    assert args.output == Path("annotated.png")


def test_image_source_requires_input():
    with pytest.raises(SystemExit) as exc:
        parse_args(["--source", "image"])

    assert exc.value.code == 2


def test_calibration_midpoint():
    transformer = create_transformer()

    point = transformer.pixel_to_robot(320, 240)

    assert point.x == pytest.approx(220)
    assert point.y == pytest.approx(-40)


def test_create_application():
    args = parse_args([
        "--source", "image",
        "--input", "objects.png",
    ])

    app = create_application(args)

    assert app.camera.image_path == Path("objects.png")
    assert app.pose_generator.pick_height == 20
    assert app.pose_generator.approach_height == 70


def make_result(
    detected_count=3,
    successful_picks=3,
    failed_picks=0,
    aborted=False,
):
    return SimpleNamespace(
        detected_count=detected_count,
        successful_picks=successful_picks,
        failed_picks=failed_picks,
        aborted=aborted,
        annotated_image_path=Path("annotated.png"),
        object_results=(),
    )


@patch("robot_pick_place.main.create_application")
def test_main_success(mock_create, capsys):
    app = MagicMock()
    app.run.return_value = make_result()
    mock_create.return_value = app

    exit_code = main([
        "--source", "image",
        "--input", "objects.png",
    ])

    assert exit_code == 0
    assert "Successful picks : 3" in capsys.readouterr().out


@patch("robot_pick_place.main.create_application")
def test_main_partial_failure(mock_create):
    app = MagicMock()
    app.run.return_value = make_result(
        successful_picks=2,
        failed_picks=1,
    )
    mock_create.return_value = app

    exit_code = main([
        "--input", "objects.png",
    ])

    assert exit_code == 3


@patch("robot_pick_place.main.create_application")
def test_main_emergency_abort(mock_create):
    app = MagicMock()
    app.run.return_value = make_result(
        successful_picks=1,
        failed_picks=0,
        aborted=True,
    )
    mock_create.return_value = app

    exit_code = main([
        "--input", "objects.png",
    ])

    assert exit_code == 2


@patch("robot_pick_place.main.create_application")
def test_main_handles_exception(mock_create):
    mock_create.side_effect = RuntimeError(
        "Simulated startup failure"
    )

    exit_code = main([
        "--input", "objects.png",
    ])

    assert exit_code == 1
