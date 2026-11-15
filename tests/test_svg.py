from __future__ import annotations

import math

import pytest

from strokeoutline import (
    CubicBezier,
    Line,
    OutlineConfig,
    QuadraticBezier,
    WidthParameterization,
    outline,
    signed_area,
)
from strokeoutline.svg import outline_svg_path, path_from_svg


def test_svg_line_parity_with_inkgrammar_baseline():
    result = outline_svg_path("M 0 0 L 10 0", 2.0)
    assert result.bounds == (-1.0, -1.0, 11.0, 1.0)


def test_svg_variable_width_parity_with_inkgrammar_baseline():
    result = outline_svg_path(
        "M 0 0 L 10 0",
        [(0.0, 2.0), (0.25, 3.0), (1.0, 10.0)],
        config=OutlineConfig(max_width_error=0.05),
    )
    assert result.bounds == (-1.0, -5.0, 15.0, 5.0)


def test_svg_closed_loop_winding_parity():
    result = outline_svg_path(
        "M 0 0 C 0 100 100 100 100 0 C 100 -100 0 -100 0 0 Z",
        8.0,
    )
    assert len(result.contours) == 2
    assert signed_area(result.contours[0]) * signed_area(result.contours[1]) < 0


def test_svg_multiple_subpaths_are_preserved():
    path = path_from_svg("M 0 0 L 10 0 M 20 0 L 30 0")
    assert len(path.subpaths) == 2


def test_svg_relative_horizontal_and_vertical_lines_are_normalized():
    path = path_from_svg("m 1 2 h 5 v 3")

    assert path.subpaths[0].segments == (Line((1, 2), (6, 2)), Line((6, 2), (6, 5)))


def test_svg_smooth_cubic_and_quadratic_commands_are_supported():
    cubic_path = path_from_svg("M 0 0 C 1 2 3 4 5 6 S 8 10 11 12")
    quadratic_path = path_from_svg("M 0 0 Q 5 10 10 0 T 20 0")

    assert cubic_path.subpaths[0].segments
    assert all(isinstance(segment, CubicBezier) for segment in cubic_path.subpaths[0].segments)
    assert quadratic_path.subpaths[0].segments
    assert all(
        isinstance(segment, QuadraticBezier) for segment in quadratic_path.subpaths[0].segments
    )


def test_svg_arc_and_close_commands_produce_supported_geometry():
    arc_path = path_from_svg("M 0 0 A 10 10 0 0 1 20 0")
    closed_path = path_from_svg("M 0 0 H 10 V 10 Z")
    result = outline_svg_path("M 0 0 A 10 10 0 0 1 20 0", 2.0)

    assert all(isinstance(segment, CubicBezier) for segment in arc_path.subpaths[0].segments)
    assert closed_path.subpaths[0].closed
    assert result.bounds is not None
    assert all(math.isfinite(value) for value in result.bounds)


def test_svg_adapter_forwards_width_parameterization():
    path = "M 0 0 L 10 0 L 100 0"
    profile = ((0.0, 2.0), (0.5, 10.0), (1.0, 2.0))
    mode: WidthParameterization = "arclength"

    legacy = outline_svg_path(path, profile)
    arclength = outline_svg_path(path, profile, width_parameterization=mode)
    expected = outline(path_from_svg(path), profile, width_parameterization=mode)

    assert arclength == expected
    assert arclength != legacy
    assert (
        outline_svg_path(path, profile, config=OutlineConfig(width_parameterization="arclength"))
        == arclength
    )
    with pytest.raises(ValueError, match="width_parameterization"):
        outline_svg_path(path, profile, width_parameterization="invalid")


def test_svg_move_only_subpath_is_rejected():
    with pytest.raises(ValueError, match="no drawable segments"):
        path_from_svg("M 0 0")
