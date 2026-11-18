from __future__ import annotations

import numpy as np
import pytest
from planarcurve import Affine2D

from strokeoutline import (
    OutlineConfig,
    RasterFrame,
    StrokeInput,
    path_from_polyline,
    render_stroke,
    render_strokes,
)


def test_render_stroke_returns_outline_and_optional_raster():
    path = path_from_polyline([(4, 8), (20, 8)])
    frame = RasterFrame(32, 24, Affine2D.identity())

    vector_only = render_stroke(path, 4.0)
    with_raster = render_stroke(path, 4.0, raster_frame=frame)

    assert vector_only.raster is None
    assert vector_only.outline == with_raster.outline
    assert with_raster.raster is not None
    assert with_raster.raster.coverage.shape == (24, 32)


def test_render_strokes_combines_crossing_coverages_by_maximum():
    horizontal = StrokeInput("horizontal", path_from_polyline([(3, 12), (27, 12)]), 5.0)
    vertical = StrokeInput("vertical", path_from_polyline([(15, 3), (15, 21)]), 5.0)
    rendered = render_strokes(
        [horizontal, vertical],
        raster_frame=RasterFrame(32, 24, Affine2D.identity()),
        supersampling=3,
    )

    expected = np.maximum(rendered.layers[0].coverage, rendered.layers[1].coverage)
    np.testing.assert_array_equal(rendered.combined_coverage, expected)
    assert len(rendered.layers) == 2
    assert rendered.layers[0].coverage[12, 15] > 0
    assert len(rendered.combined_outline.contours) == sum(
        len(layer.outline.contours) for layer in rendered.layers
    )
    assert not rendered.combined_coverage.flags.writeable


def test_exactly_overlapping_strokes_remain_opaque_not_additive():
    path = path_from_polyline([(4, 10), (20, 10)])
    frame = RasterFrame(32, 24, Affine2D.identity())
    rendered = render_strokes(
        [StrokeInput("first", path, 4.0), StrokeInput("second", path, 4.0)],
        raster_frame=frame,
    )

    np.testing.assert_array_equal(rendered.layers[0].coverage, rendered.layers[1].coverage)
    np.testing.assert_array_equal(rendered.combined_coverage, rendered.layers[0].coverage)


def test_partial_retrace_renders_as_opaque_coverage():
    path = path_from_polyline([(4, 12), (24, 12), (12, 12), (28, 12)])
    rendered = render_stroke(
        path,
        5.0,
        raster_frame=RasterFrame(36, 24, Affine2D.identity()),
    )

    assert rendered.raster is not None
    assert rendered.raster.coverage[12, 18] > 0.95
    assert rendered.raster.coverage[12, 0] == 0.0


def test_render_stroke_uses_outline_config_for_variable_width():
    path = path_from_polyline([(2, 10), (10, 10), (22, 10)])
    rendered = render_stroke(
        path,
        [(0.0, 2.0), (1.0, 8.0)],
        outline_config=OutlineConfig(width_parameterization="arclength"),
        raster_frame=RasterFrame(32, 24, Affine2D.identity()),
    )

    assert rendered.outline.bounds is not None
    assert rendered.raster is not None
    assert rendered.raster.bounds_px is not None


def test_empty_multi_stroke_render_has_empty_coverage():
    rendered = render_strokes([], raster_frame=RasterFrame(8, 6, Affine2D.identity()))

    assert rendered.layers == ()
    assert rendered.combined_outline.contours == ()
    assert rendered.combined_coverage.shape == (6, 8)
    assert not rendered.combined_coverage.any()


def test_render_strokes_reject_duplicate_ids():
    path = path_from_polyline([(0, 0), (2, 0)])
    strokes = [StrokeInput("same", path, 1.0), StrokeInput("same", path, 2.0)]

    with pytest.raises(ValueError, match="unique"):
        render_strokes(strokes)
