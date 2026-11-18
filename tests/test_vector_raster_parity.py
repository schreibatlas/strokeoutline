from __future__ import annotations

import numpy as np
import pytest
from planarcurve import Affine2D, CubicPath, CubicSegment

from strokeoutline import (
    Line,
    OutlineConfig,
    Path2D,
    RasterFrame,
    Subpath,
    outline,
    path_from_cubic_path,
    path_from_polyline,
    rasterize_outline,
    render_stroke,
)


def _parity_cases():
    line = path_from_polyline([(8, 20), (48, 20)])
    curve = CubicPath(
        start=(8, 36),
        segments=(CubicSegment((8, 8), (48, 8), (48, 36)),),
    )
    corner = path_from_polyline([(8, 16), (28, 16), (28, 36)])
    closed = path_from_polyline([(12, 12), (44, 12), (44, 44), (12, 44)], closed=True)
    multi_subpath = Path2D(
        (
            Subpath((Line((8, 14), (48, 14)),)),
            Subpath((Line((8, 42), (48, 42)),)),
        )
    )

    cases = [
        pytest.param(line, 4.0, OutlineConfig(), id="straight-constant-width"),
        pytest.param(curve, 4.0, OutlineConfig(), id="cubic-curve"),
        pytest.param(
            line,
            [(0.0, 2.0), (0.4, 5.0), (1.0, 8.0)],
            OutlineConfig(),
            id="piecewise-width",
        ),
        pytest.param(
            line,
            lambda progress: 2.0 + 4.0 * progress,
            OutlineConfig(max_width_error=0.1),
            id="callable-width",
        ),
        pytest.param(
            path_from_polyline([(8, 18), (18, 18), (48, 18)]),
            [(0.0, 2.0), (1.0, 8.0)],
            OutlineConfig(width_parameterization="arclength"),
            id="arclength-width",
        ),
        pytest.param(line, 5.0, OutlineConfig(cap="round"), id="round-cap"),
        pytest.param(line, 5.0, OutlineConfig(cap="butt"), id="butt-cap"),
        pytest.param(line, 5.0, OutlineConfig(cap="square"), id="square-cap"),
        pytest.param(corner, 5.0, OutlineConfig(join="miter"), id="miter-join"),
        pytest.param(corner, 5.0, OutlineConfig(join="bevel"), id="bevel-join"),
        pytest.param(corner, 5.0, OutlineConfig(join="round"), id="round-join"),
        pytest.param(closed, 4.0, OutlineConfig(), id="closed-loop"),
        pytest.param(multi_subpath, 4.0, OutlineConfig(), id="multiple-subpaths"),
        pytest.param(
            path_from_cubic_path(curve),
            4.0,
            OutlineConfig(),
            id="planarcurve-cubic-adapter",
        ),
    ]
    return cases


@pytest.mark.parametrize(("path", "width", "config"), _parity_cases())
def test_render_stroke_has_vector_to_raster_parity(path, width, config):
    frame = RasterFrame(56, 56, Affine2D(m00=1, m11=-1, dx=0, dy=56))
    vector = outline(path, width, config=config)
    direct_raster = rasterize_outline(vector, frame, supersampling=3)
    rendered = render_stroke(
        path,
        width,
        outline_config=config,
        raster_frame=frame,
        supersampling=3,
    )

    assert rendered.outline == vector
    assert rendered.raster is not None
    np.testing.assert_array_equal(rendered.raster.coverage, direct_raster.coverage)
    assert rendered.raster.bounds_px == direct_raster.bounds_px


def test_raster_bounds_are_clipped_to_frame_and_empty_for_outside_outline():
    path = path_from_polyline([(40, 40), (60, 40)])
    result = rasterize_outline(
        outline(path, 4.0),
        RasterFrame(24, 24, Affine2D.identity()),
    )

    assert result.bounds_px is None
    assert not result.coverage.any()
