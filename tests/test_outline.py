from __future__ import annotations

import math

import pytest
from planarcurve import CubicBezier, CubicPath, CubicSegment, QuadraticBezier

from strokeoutline import (
    DegeneratePathError,
    InvalidWidthError,
    Line,
    OutlineConfig,
    OutlineResult,
    Path2D,
    Subpath,
    combine_outlines,
    outline,
    outline_disc,
    signed_area,
)


def assert_closed_and_finite(result):
    assert result.contours
    for contour in result.contours:
        assert contour[0] == contour[-1]
        assert all(math.isfinite(value) for point in contour for value in point)
    assert result.bounds is not None
    assert all(math.isfinite(value) for value in result.bounds)


def test_open_line_has_deterministic_round_caps_and_expected_bounds():
    path = Path2D((Subpath((Line((0, 0), (10, 0)),)),))
    first = outline(path, 2.0)
    second = outline(path, 2.0)

    assert first == second
    assert_closed_and_finite(first)
    assert first.bounds == (-1.0, -1.0, 11.0, 1.0)


def test_curve_is_adaptively_sampled_and_attached_segments_share_one_outline():
    curve = Path2D((Subpath((CubicBezier((0, 0), (0, 100), (100, 100), (100, 0)),)),))
    composed = Path2D((Subpath((Line((0, 0), (10, 0)), Line((10, 0), (20, 0)))),))

    curve_result = outline(curve, 4.0)
    composed_result = outline(composed, 4.0)
    assert len(curve_result.contours[0]) > len(composed_result.contours[0])
    assert len(composed_result.contours) == 1
    assert_closed_and_finite(curve_result)
    assert_closed_and_finite(composed_result)


def test_variable_width_changes_bounds_and_is_adaptively_subdivided():
    path = Path2D((Subpath((Line((0, 0), (10, 0)),)),))
    result = outline(
        path,
        [(0.0, 2.0), (0.25, 3.0), (1.0, 10.0)],
        config=OutlineConfig(max_width_error=0.05),
    )

    assert_closed_and_finite(result)
    assert result.bounds == (-1.0, -5.0, 15.0, 5.0)
    assert len(result.contours[0]) > 8


def test_closed_loop_has_oppositely_wound_inner_and_outer_contours():
    path = Path2D(
        (
            Subpath(
                (
                    CubicBezier((0, 0), (0, 100), (100, 100), (100, 0)),
                    CubicBezier((100, 0), (100, -100), (0, -100), (0, 0)),
                ),
                closed=True,
            ),
        )
    )
    result = outline(path, 8.0)

    assert len(result.contours) == 2
    assert_closed_and_finite(result)
    assert signed_area(result.contours[0]) * signed_area(result.contours[1]) < 0


def test_tap_becomes_a_closed_repeatable_circle():
    first = outline_disc((4, -3), 10)
    second = outline_disc((4, -3), 10)

    assert first == second
    assert_closed_and_finite(first)
    assert first.bounds == (-1.0, -8.0, 9.0, 2.0)


def test_width_profile_rejects_invalid_knots():
    path = Path2D((Subpath((Line((0, 0), (10, 0)),)),))
    with pytest.raises(InvalidWidthError, match="positive widths"):
        outline(path, [(0.0, 2.0), (0.5, -1.0), (1.0, 4.0)])


def test_quadratic_and_callable_width_are_supported():
    path = Path2D((Subpath((QuadraticBezier((0, 0), (5, 10), (10, 0)),)),))
    result = outline(path, lambda u: 2 + 2 * u)
    assert_closed_and_finite(result)


def test_callable_width_is_normalized_to_float():
    path = Path2D((Subpath((Line((0, 0), (10, 0)),)),))
    result = outline(path, lambda _u: "2")
    assert result.bounds == (-1.0, -1.0, 11.0, 1.0)


@pytest.mark.parametrize("invalid_width", [None, math.nan, math.inf, 0.0, -1.0])
def test_callable_width_rejects_invalid_initial_values(invalid_width):
    path = Path2D((Subpath((Line((0, 0), (10, 0)),)),))
    with pytest.raises(InvalidWidthError):
        outline(path, lambda _u: invalid_width)


@pytest.mark.parametrize("invalid_width", [None, math.nan, math.inf, 0.0, -1.0])
def test_callable_width_rejects_invalid_intermediate_values(invalid_width):
    path = Path2D((Subpath((Line((0, 0), (10, 0)),)),))

    def width(u):
        return invalid_width if u == 0.25 else 2.0

    with pytest.raises(InvalidWidthError):
        outline(path, width)


def test_callable_width_propagates_user_exceptions():
    path = Path2D((Subpath((Line((0, 0), (10, 0)),)),))

    def width(_u):
        raise RuntimeError("width callback failed")

    with pytest.raises(RuntimeError, match="width callback failed"):
        outline(path, width)


@pytest.mark.parametrize(
    "config_kwargs",
    [
        {"max_centerline_error": True},
        {"max_width_error": True},
        {"max_normal_angle_degrees": True},
    ],
)
def test_outline_config_rejects_boolean_tolerances(config_kwargs):
    with pytest.raises(ValueError, match="positive and finite"):
        OutlineConfig(**config_kwargs)


def test_square_cap_matches_existing_non_round_semantics():
    path = Path2D((Subpath((Line((0, 0), (10, 0)),)),))
    result = outline(path, 2.0, config=OutlineConfig(cap="square"))
    assert result.bounds == (-1.0, -1.0, 11.0, 1.0)


def test_zero_length_segment_is_rejected():
    path = Path2D((Subpath((Line((0, 0), (0, 0)),)),))
    with pytest.raises(DegeneratePathError):
        outline(path, 2.0)


def test_planarcurve_cubic_path_is_accepted_directly():
    path = CubicPath((0, 0), (CubicSegment((3, 0), (7, 0), (10, 0)),))
    result = outline(path, 2.0)
    assert result.bounds == (-1.0, -1.0, 11.0, 1.0)


def test_combine_outlines_preserves_contour_order_and_computes_union_bounds():
    first = OutlineResult(
        (
            ((0.0, 0.0), (1.0, 0.0), (0.0, 0.0)),
            ((0.0, 0.0), (0.0, 2.0), (0.0, 0.0)),
        ),
        (0.0, 0.0, 1.0, 2.0),
    )
    second = OutlineResult(
        (((-3.0, 4.0), (-2.0, 4.0), (-3.0, 4.0)),),
        (-3.0, 4.0, -2.0, 4.0),
    )

    combined = combine_outlines(iter((first, second)))

    assert combined.contours == first.contours + second.contours
    assert combined.bounds == (-3.0, 0.0, 1.0, 4.0)


def test_combine_outlines_empty_input_returns_empty_result():
    assert combine_outlines(()) == OutlineResult((), None)


def test_outline_disc_evaluates_width_profiles_at_midpoint():
    profile = [(0.0, 2.0), (0.5, 8.0), (1.0, 4.0)]

    assert outline_disc((4, -3), profile) == outline_disc((4, -3), 8.0)
