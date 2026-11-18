# Examples

The repository contains nine executable examples. Each has a `main()` guard, asserts stable semantic properties, and can be imported without output or filesystem side effects. Run them from the repository root:

```bash
python examples/01_basic_centerline.py
python examples/02_variable_width.py
python examples/03_svg_adapter.py
python examples/04_closed_centerline.py
python examples/05_planarcurve_interop.py
python examples/06_polyline_and_composition.py
python examples/07_caps_and_disc.py
python examples/08_raster_coverage.py
python examples/09_multi_stroke_render.py
```

The SVG example requires FontTools. Install it with `python -m pip install 'strokeoutline[svg]'`.


The raster examples require Pillow. Install it with `python -m pip install 'strokeoutline[raster]'`.

| Script | Demonstrates | Optional dependency | Expected invariant |
| --- | --- | --- | --- |
| [`01_basic_centerline.py`](../examples/01_basic_centerline.py) | Line, quadratic, and cubic segments | None | One finite, explicitly closed contour |
| [`02_variable_width.py`](../examples/02_variable_width.py) | Piecewise width knots and adaptive sampling | None | The wider profile region expands bounds |
| [`03_svg_adapter.py`](../examples/03_svg_adapter.py) | Multiple SVG subpaths | FontTools via `strokeoutline[svg]` | Two source subpaths produce two outline contours |
| [`04_closed_centerline.py`](../examples/04_closed_centerline.py) | Implicit closure and winding | None | Two closed contours have opposite winding |
| [`05_planarcurve_interop.py`](../examples/05_planarcurve_interop.py) | Direct `planarcurve.CubicPath` input | None | Direct input matches the equivalent adapted path |
| [`06_polyline_and_composition.py`](../examples/06_polyline_and_composition.py) | `path_from_polyline()` and `combine_outlines()` | None | Contour order is preserved and aggregate bounds cover both results |
| [`07_caps_and_disc.py`](../examples/07_caps_and_disc.py) | Round/square caps and `outline_disc()` | None | Cap selection changes geometry; the disc is finite and closed |
| [`08_raster_coverage.py`](../examples/08_raster_coverage.py) | Explicit pixel transform and contour rasterization | Pillow via `strokeoutline[raster]` | Coverage matches the vector outline in the requested frame |
| [`09_multi_stroke_render.py`](../examples/09_multi_stroke_render.py) | Per-stroke layers and max-combined opaque coverage | Pillow via `strokeoutline[raster]` | Combined coverage equals the pixelwise maximum of the layers |

The examples demonstrate sampled centerline expansion, not Boolean polygon cleanup or complete SVG/CSS stroke semantics. The default width mode is segment-index progress; see [width profiles](width-profiles.md).
