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
    SubdivisionLimitError,
    Subpath,
    combine_outlines,
    outline,
    outline_disc,
    signed_area,
)
from strokeoutline.core import _endpoint_tangent, _profile_points, _width_function


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


@pytest.mark.parametrize(
    "center",
    [(0,), (0, 1, 2), ("x", 0), (math.nan, 0), (0, math.inf), None],
)
def test_outline_disc_rejects_invalid_centers(center):
    with pytest.raises(ValueError):
        outline_disc(center, 2.0)


def test_outline_result_normalizes_mutable_inputs():
    contour = [[0, 0], [1, 0], [0, 0]]
    contours = [contour]
    bounds = [0, 0, 1, 0]

    result = OutlineResult(contours, bounds)
    contour.append([2, 0])
    contours.clear()
    bounds[0] = -1

    assert result.contours == (((0.0, 0.0), (1.0, 0.0), (0.0, 0.0)),)
    assert result.bounds == (0.0, 0.0, 1.0, 0.0)
    assert isinstance(result.contours, tuple)
    assert isinstance(result.contours[0], tuple)
    assert isinstance(result.contours[0][0], tuple)


@pytest.mark.parametrize(
    ("contours", "bounds"),
    [
        ([[(0, 0), (1, 0)]], (0, 0, 1, 0)),
        ([[(0, 0), (1, 0), (0, 0)]], (0, 0, 2, 0)),
        ([[(0, 0), (1, 0), (0, 0)]], (0, 0, math.inf, 0)),
        ([], (0, 0, 1, 0)),
    ],
)
def test_outline_result_rejects_open_contours_or_inconsistent_bounds(contours, bounds):
    with pytest.raises(ValueError):
        OutlineResult(contours, bounds)


def test_width_profile_accepts_iterable_knots_and_numpy_real_scalars():
    path = Path2D((Subpath((Line((0, 0), (10, 0)),)),))
    knot_generator = ((position, width) for position, width in ((0, 2), (1, 4)))
    assert outline(path, knot_generator).bounds is not None

    np = pytest.importorskip("numpy")
    for width in (np.float32(2), np.float64(2), np.int32(2), np.int64(2)):
        assert outline(path, width).bounds == (-1.0, -1.0, 11.0, 1.0)


def test_large_subdivision_depth_raises_controlled_no_progress_error():
    path = Path2D((Subpath((Line((0, 0), (10, 0)),)),))

    def discontinuous_width(u):
        return 2.0 if u < 0.5 else 4.0

    with pytest.raises(SubdivisionLimitError, match="no floating-point progress"):
        outline(
            path,
            discontinuous_width,
            config=OutlineConfig(max_width_error=0.01, max_subdivision_depth=2000),
        )


def test_subdivision_depth_limit_raises_controlled_error():
    path = Path2D((Subpath((Line((0, 0), (10, 0)),)),))

    with pytest.raises(SubdivisionLimitError, match="depth limit"):
        outline(
            path,
            lambda u: 2.0 if u < 0.5 else 4.0,
            config=OutlineConfig(max_width_error=0.01, max_subdivision_depth=1),
        )


def test_piecewise_width_knots_are_sampled_exactly_without_extra_width_refinement():
    segments = (Line((0, 0), (100, 0)),)
    profile = ((0.0, 2.0), (0.3, 4.0), (0.7, 16.0), (1.0, 6.0))

    points, widths = _profile_points(
        segments, _width_function(profile), OutlineConfig(max_width_error=0.05)
    )

    assert points == [(0.0, 0.0), (30.0, 0.0), (70.0, 0.0), (100.0, 0.0)]
    assert widths == [2.0, 4.0, 16.0, 6.0]


def test_piecewise_knots_map_across_segments_and_closed_implicit_segment():
    segments = (Line((0, 0), (10, 0)), Line((10, 0), (10, 20)))
    profile = ((0.0, 2.0), (0.25, 4.0), (0.75, 8.0), (1.0, 10.0))
    points, widths = _profile_points(segments, _width_function(profile), OutlineConfig())
    sampled_widths = dict(zip(points, widths, strict=True))
    assert sampled_widths[(5.0, 0.0)] == 4.0
    assert sampled_widths[(10.0, 10.0)] == 8.0

    closed_segments = Subpath(segments, closed=True).outlining_segments()
    closed_profile = ((0.0, 2.0), (2 / 3, 8.0), (1.0, 10.0))
    closed_points, closed_widths = _profile_points(
        closed_segments, _width_function(closed_profile), OutlineConfig()
    )
    assert dict(zip(closed_points, closed_widths, strict=True))[(10.0, 20.0)] == 8.0


def test_callable_width_is_evaluated_once_per_parameter():
    path = Path2D((Subpath((Line((0, 0), (10, 0)),)),))
    calls = {}

    def width(u):
        calls[u] = calls.get(u, 0) + 1
        return 2.0 + 3.0 * u * u

    outline(path, width, config=OutlineConfig(max_width_error=0.001))

    assert calls
    assert max(calls.values()) == 1


def test_tiny_and_large_translated_lines_are_not_rejected_by_absolute_epsilon():
    tiny = Path2D((Subpath((Line((0, 0), (1e-13, 0)),)),))
    translated = Path2D((Subpath((Line((1e12, 1e12), (1e12 + 1, 1e12)),)),))

    assert_closed_and_finite(outline(tiny, 1e-13))
    assert_closed_and_finite(outline(translated, 0.1))


def test_endpoint_tangents_use_analytic_derivatives_and_degenerate_fallbacks():
    curve = QuadraticBezier((0, 0), (0, 10), (10, 10))
    cusp = CubicBezier((0, 0), (0, 0), (1, 1), (2, 0))

    assert _endpoint_tangent(curve, 0.0, (1, 0)) == (0.0, 1.0)
    assert _endpoint_tangent(curve, 1.0, (0, 1)) == (1.0, 0.0)
    assert _endpoint_tangent(cusp, 0.0, (1, 0)) == (1.0, 0.0)


def test_explicit_join_styles_preserve_legacy_default_and_distinguish_geometry():
    path = Path2D((Subpath((Line((0, 0), (10, 0)), Line((10, 0), (10, 10)))),))
    legacy = outline(path, 2.0, config=OutlineConfig(cap="butt", join="legacy"))
    miter = outline(path, 2.0, config=OutlineConfig(cap="butt", join="miter"))
    bevel = outline(path, 2.0, config=OutlineConfig(cap="butt", join="bevel"))
    rounded = outline(path, 2.0, config=OutlineConfig(cap="butt", join="round"))

    assert outline(path, 2.0, config=OutlineConfig(cap="butt")) == legacy
    assert (11.0, -1.0) in miter.contours[0]
    assert (11.0, -1.0) not in bevel.contours[0]
    assert len(rounded.contours[0]) > len(bevel.contours[0])


def test_butt_cap_does_not_extend_open_line_endpoints():
    path = Path2D((Subpath((Line((0, 0), (10, 0)),)),))

    butt = outline(path, 2.0, config=OutlineConfig(cap="butt"))
    square = outline(path, 2.0, config=OutlineConfig(cap="square"))

    assert butt.bounds == (0.0, -1.0, 10.0, 1.0)
    assert square.bounds == (-1.0, -1.0, 11.0, 1.0)


def test_arc_length_width_progress_uses_physical_segment_lengths():
    segments = (Line((0, 0), (10, 0)), Line((10, 0), (100, 0)))
    profile = ((0.0, 2.0), (0.5, 10.0), (1.0, 2.0))

    segment_points, segment_widths = _profile_points(
        segments, _width_function(profile), OutlineConfig()
    )
    arc_points, arc_widths = _profile_points(
        segments,
        _width_function(profile),
        OutlineConfig(width_parameterization="arclength"),
    )
    segment_widths_by_point = dict(zip(segment_points, segment_widths, strict=True))
    arc_widths_by_point = dict(zip(arc_points, arc_widths, strict=True))

    assert segment_widths_by_point[(10.0, 0.0)] == 10.0
    assert arc_widths_by_point[(10.0, 0.0)] == pytest.approx(3.6)
    assert any(math.isclose(point[0], 50.0) for point in arc_points)
    assert any(width == 10.0 for width in arc_widths)


@pytest.mark.parametrize(
    "config_kwargs",
    [
        {"cap": "invalid"},
        {"join": "invalid"},
        {"width_parameterization": "invalid"},
        {"miter_limit": 0.0},
        {"miter_limit": math.inf},
    ],
)
def test_outline_config_rejects_invalid_geometry_options(config_kwargs):
    with pytest.raises(ValueError):
        OutlineConfig(**config_kwargs)


@pytest.mark.parametrize(
    ("subpath", "width"),
    [
        (
            Subpath((Line((0, 0), (10, 0)), Line((10, 0), (11, 3)))),
            2.0,
        ),
        (
            Subpath((Line((0, 0), (10, 0)), Line((10, 0), (5, 5)))),
            2.0,
        ),
        (
            Subpath((Line((0, 0), (10, 0)), Line((10, 0), (0.1, 0.01)))),
            2.0,
        ),
        (
            Subpath((Line((0, 0), (10, 0)), Line((10, 0), (10, 10)))),
            ((0.0, 2.0), (0.5, 8.0), (1.0, 3.0)),
        ),
        (
            Subpath(
                (
                    Line((0, 0), (10, 0)),
                    Line((10, 0), (5, 10)),
                    Line((5, 10), (0, 0)),
                ),
                closed=True,
            ),
            2.0,
        ),
    ],
)
@pytest.mark.parametrize("join", ["legacy", "miter", "bevel", "round"])
def test_join_modes_handle_sharp_variable_and_closed_corners(subpath, width, join):
    result = outline(
        Path2D((subpath,)),
        width,
        config=OutlineConfig(cap="butt", join=join, miter_limit=3.0),
    )

    assert_closed_and_finite(result)
    if subpath.closed:
        assert len(result.contours) == 2


def test_miter_limit_bevels_an_over_limit_corner():
    path = Path2D((Subpath((Line((0, 0), (10, 0)), Line((10, 0), (10, 10)))),))

    result = outline(path, 2.0, config=OutlineConfig(cap="butt", join="miter", miter_limit=1.0))

    assert (11.0, -1.0) not in result.contours[0]


def test_curved_round_caps_follow_analytic_endpoint_tangent_across_tolerances():
    path = Path2D((Subpath((QuadraticBezier((0, 0), (0, 10), (10, 10)),)),))

    for tolerance in (0.25, 0.05):
        result = outline(path, 2.0, config=OutlineConfig(max_centerline_error=tolerance))
        assert any(
            math.isclose(x, 0.0, abs_tol=1e-12) and math.isclose(y, -1.0)
            for x, y in result.contours[0]
        )


def test_disc_accepts_two_coordinate_list_and_numpy_array():
    assert outline_disc([4, -3], 10.0).bounds == (-1.0, -8.0, 9.0, 2.0)
    np = pytest.importorskip("numpy")
    assert outline_disc(np.array([4.0, -3.0]), 10.0).bounds == (-1.0, -8.0, 9.0, 2.0)


@pytest.mark.parametrize(
    "profile",
    [
        [(0.0, True), (1.0, 2.0)],
        [(0.0, 2.0), (True, 3.0), (1.0, 4.0)],
    ],
)
def test_width_profile_rejects_boolean_knots(profile):
    path = Path2D((Subpath((Line((0, 0), (10, 0)),)),))
    with pytest.raises(InvalidWidthError):
        outline(path, profile)
