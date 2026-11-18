from __future__ import annotations

import subprocess
import sys

import numpy as np
import pytest
from planarcurve import Affine2D

from strokeoutline import (
    RasterConfig,
    RasterFrame,
    RasterizedOutline,
    outline,
    path_from_polyline,
    rasterize_outline,
)


def test_rasterizes_outline_into_read_only_float_coverage():
    result = outline(path_from_polyline([(4, 10), (20, 10)]), 4.0)
    rasterized = rasterize_outline(
        result,
        RasterFrame(32, 24, Affine2D.identity()),
        supersampling=4,
    )

    assert rasterized.coverage.shape == (24, 32)
    assert rasterized.coverage.dtype == np.float32
    assert not rasterized.coverage.flags.writeable
    assert np.all((rasterized.coverage >= 0) & (rasterized.coverage <= 1))
    assert rasterized.bounds_px is not None
    assert rasterized.coverage[10, 10] > 0
    with pytest.raises(ValueError, match="read-only"):
        rasterized.coverage[10, 10] = 0


def test_raster_frame_transform_controls_axis_direction():
    result = outline(path_from_polyline([(0, 0), (8, 0)]), 2.0)
    frame = RasterFrame(24, 24, Affine2D(m00=1, m11=-1, dx=10, dy=18))

    rasterized = rasterize_outline(result, frame)

    assert rasterized.coverage[18, 10] > 0
    assert rasterized.coverage[5, 10] == 0


def test_closed_stroke_preserves_interior_hole():
    path = path_from_polyline([(5, 5), (20, 5), (20, 20), (5, 20)], closed=True)
    rasterized = rasterize_outline(
        outline(path, 2.0),
        RasterFrame(28, 28, Affine2D.identity()),
        supersampling=4,
    )

    assert rasterized.coverage[12, 12] == 0
    assert rasterized.coverage[5, 12] > 0


def test_rasterization_is_deterministic():
    result = outline(path_from_polyline([(3.25, 4.5), (20, 17)]), 3.0)
    frame = RasterFrame(32, 24, Affine2D.identity())

    first = rasterize_outline(result, frame, supersampling=3)
    second = rasterize_outline(result, frame, supersampling=3)

    np.testing.assert_array_equal(first.coverage, second.coverage)
    assert first.bounds_px == second.bounds_px


@pytest.mark.parametrize("dimensions", [(0, 10), (-1, 10), (10, 0), (10.5, 10), (True, 10)])
def test_raster_frame_rejects_invalid_dimensions(dimensions):
    with pytest.raises(ValueError, match="positive integer"):
        RasterFrame(*dimensions, Affine2D.identity())


def test_raster_frame_rejects_non_finite_transform():
    with pytest.raises(ValueError, match="finite"):
        RasterFrame(10, 10, Affine2D(dx=float("nan")))


@pytest.mark.parametrize(
    "kwargs",
    [{"supersampling": 0}, {"supersampling": True}, {"tile_size": 0}],
)
def test_raster_config_rejects_invalid_controls(kwargs):
    with pytest.raises(ValueError):
        RasterConfig(**kwargs)


def test_rasterized_outline_validates_coverage_contract():
    with pytest.raises(ValueError, match="two-dimensional"):
        RasterizedOutline(np.zeros(3, dtype=np.float32), None)
    with pytest.raises(ValueError, match=r"\[0, 1\]"):
        RasterizedOutline(np.array([[1.1]], dtype=np.float32), None)


def test_package_import_does_not_import_pillow():
    code = """
import builtins
original_import = builtins.__import__
def import_without_pillow(name, *args, **kwargs):
    if name == 'PIL' or name.startswith('PIL.'):
        raise AssertionError('Pillow was imported')
    return original_import(name, *args, **kwargs)
builtins.__import__ = import_without_pillow
import strokeoutline
assert strokeoutline.RasterFrame
"""
    completed = subprocess.run(
        [sys.executable, "-c", code],
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
