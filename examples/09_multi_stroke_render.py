"""Render independent strokes and combine their opaque coverage."""

import numpy as np
from planarcurve import Affine2D

from strokeoutline import RasterFrame, StrokeInput, path_from_polyline, render_strokes


def main() -> None:
    frame = RasterFrame(64, 56, Affine2D(m00=2, m11=-2, dx=8, dy=44))
    rendered = render_strokes(
        [
            StrokeInput("first", path_from_polyline([(0, 0), (18, 10)]), 2.5),
            StrokeInput("second", path_from_polyline([(6, 10), (20, 0)]), 2.5),
        ],
        raster_frame=frame,
        supersampling=4,
    )

    assert len(rendered.layers) == 2
    assert rendered.combined_coverage is not None
    expected = np.maximum(rendered.layers[0].coverage, rendered.layers[1].coverage)
    np.testing.assert_array_equal(rendered.combined_coverage, expected)
    print(f"layers={len(rendered.layers)}, coverage={rendered.combined_coverage.max():.3f}")


if __name__ == "__main__":
    main()
