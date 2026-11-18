# Rasterization

StrokeOutline rasterizes the vector contours returned by `outline()`. Rasterization never samples or draws the centerline again, so the coverage used for fitting can match the final vector geometry.

```text
PlanarCurve geometry
        ↓
StrokeOutline outline
        ↓
StrokeOutline rasterization
```

Install Pillow support separately from the core package:

```bash
python -m pip install 'strokeoutline[raster]'
```

The core `strokeoutline` import does not import Pillow. SVG and raster extras can be installed independently or together.

## Pixel frame and transforms

`RasterFrame` requires positive integer dimensions and an explicit `planarcurve.Affine2D` mapping model coordinates to pixel coordinates. StrokeOutline does not assume a y-axis direction. Choose and encode the convention in the transform, for example by using a negative y scale for a downward-positive image frame.

```python
from planarcurve import Affine2D
from strokeoutline import RasterFrame, path_from_polyline, render_stroke

path = path_from_polyline([(0, 0), (20, 10)])
frame = RasterFrame(
    width=64,
    height=56,
    model_to_pixel=Affine2D(m00=2, m11=-2, dx=8, dy=44),
)
rendered = render_stroke(path, 2.5, raster_frame=frame, supersampling=4)
assert rendered.raster is not None
coverage = rendered.raster.coverage
```

Coverage is a read-only `float32` array with shape `(height, width)` and values in `[0, 1]`. `bounds_px` is a clipped, half-open `(left, top, right, bottom)` box around non-zero coverage, or `None` when the frame contains no ink. Supersampling is deterministic and the rasterizer works only on the transformed outline crop before returning the full-frame array.

`RasterConfig` validates a supersampling factor and optional tile size. The current backend uses the outline crop and does not tile it. `rasterize_outline(outline_result, frame, supersampling=4)` is also available when a vector outline already exists.

## Multiple strokes and overlap

Use `render_strokes()` to retain each stroke's outline and coverage while also getting a combined vector outline and coverage mask:

```python
from planarcurve import Affine2D
from strokeoutline import RasterFrame, StrokeInput, path_from_polyline, render_strokes

frame = RasterFrame(64, 56, Affine2D(m00=2, m11=-2, dx=8, dy=44))
rendered = render_strokes(
    [
        StrokeInput("first", path_from_polyline([(0, 0), (18, 10)]), 2.5),
        StrokeInput("second", path_from_polyline([(6, 10), (20, 0)]), 2.5),
    ],
    raster_frame=frame,
)
```

Combined raster coverage is the pixelwise maximum of independent layer coverages. This is opaque-ink union semantics, not additive opacity. `combine_outlines()` still concatenates vector contours and does not perform Boolean union or promise merged topology.

## Variable widths and parity

All width forms accepted by `outline()` are supported, including positive constants, piecewise-linear profiles, and deterministic callables. Width is evaluated only while creating the outline. Rasterization transforms and fills those resulting contours without re-evaluating width.

Use serializable piecewise-linear profiles for reproducible optimization. Downstream fitting code should pass its generic geometry and width profile to StrokeOutline rather than draw a thick sampled centerline when training and final rendering need parity. StrokeOutline owns rendering only; application-specific losses and distance metrics remain with the application.

## API reference

```{autoclass} strokeoutline.RasterFrame
:members:
```

```{autoclass} strokeoutline.RasterConfig
:members:
```

```{autoclass} strokeoutline.RasterizedOutline
:members:
```

```{autofunction} strokeoutline.rasterize_outline
```

```{autofunction} strokeoutline.render_stroke
```

```{autofunction} strokeoutline.render_strokes
```
