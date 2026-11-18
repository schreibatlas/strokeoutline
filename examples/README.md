# Examples

These scripts demonstrate the public StrokeOutline API without importing InkGrammar. Importing an example does not execute it, print output, or create files.

Run from the repository root:

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

The SVG example requires FontTools:

```bash
python -m pip install 'strokeoutline[svg]'
```


Rasterization is optional and requires Pillow:

```bash
python -m pip install 'strokeoutline[raster]'
```

| Script | Demonstrates | Optional dependency | Expected invariant |
| --- | --- | --- | --- |
| `01_basic_centerline.py` | Line, quadratic, and cubic segments in one subpath | None | One finite, explicitly closed outline contour |
| `02_variable_width.py` | Piecewise width profile, adaptive sampling, and arc-length progress across unequal segments | None | The wider profile region expands the contour bounds independently of segment lengths |
| `03_svg_adapter.py` | Multiple SVG subpaths | FontTools via `strokeoutline[svg]` | Two source subpaths produce two independent outline contours |
| `04_closed_centerline.py` | Implicit closure and closed-centerline winding | None | Two closed output contours have opposite winding |
| `05_planarcurve_interop.py` | Direct `planarcurve.CubicPath` input and callable width | None | Direct input matches the equivalent adapted `Path2D` |
| `06_polyline_and_composition.py` | `path_from_polyline()` and `combine_outlines()` | None | Contour order is preserved and aggregate bounds cover both results |
| `07_caps_and_disc.py` | Round/square caps and `outline_disc()` | None | Cap choice changes endpoint geometry; the disc is finite and closed |
| `08_raster_coverage.py` | Explicit pixel transform and contour rasterization | Pillow via `strokeoutline[raster]` | Coverage matches the vector outline in the requested frame |
| `09_multi_stroke_render.py` | Per-stroke layers and max-combined opaque coverage | Pillow via `strokeoutline[raster]` | Combined coverage equals the pixelwise maximum of the layers |

The examples demonstrate sampled centerline expansion, not Boolean polygon cleanup or complete SVG/CSS stroke semantics. Width progress uses the compatibility segment-index parameterization unless an example explicitly selects another mode.
