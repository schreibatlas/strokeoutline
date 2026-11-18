"""Rasterize the exact vector outline into an explicit pixel frame."""

from planarcurve import Affine2D

from strokeoutline import RasterFrame, path_from_polyline, render_stroke


def main() -> None:
    path = path_from_polyline([(0, 0), (12, 8), (20, 4)])
    frame = RasterFrame(64, 56, Affine2D(m00=2, m11=-2, dx=8, dy=44))
    rendered = render_stroke(path, 2.5, raster_frame=frame, supersampling=4)

    assert rendered.raster is not None
    assert rendered.outline.bounds is not None
    assert rendered.raster.coverage.shape == (56, 64)
    assert rendered.raster.coverage.max() > 0
    assert rendered.raster.bounds_px is not None
    print(f"bounds={rendered.raster.bounds_px}, coverage={rendered.raster.coverage.max():.3f}")


if __name__ == "__main__":
    main()
