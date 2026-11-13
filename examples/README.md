# Examples

These executable scripts demonstrate StrokeOutline without importing InkGrammar:

1. `01_basic_centerline.py` builds one path from line, quadratic, and cubic segments.
2. `02_variable_width.py` uses a piecewise width profile and adaptive sampling.
3. `03_svg_adapter.py` expands multiple subpaths from an SVG path string.
4. `04_closed_centerline.py` shows implicit closure, opposite contour winding, and area helpers.
5. `05_planarcurve_interop.py` passes a `planarcurve.CubicPath` directly and uses callable width.

Run the examples from the repository root with `python examples/<script>.py`. The SVG example requires the optional FontTools dependency from `strokeoutline[svg]`. The other examples use only StrokeOutline and its PlanarCurve dependency.

`test_examples.py` runs all five scripts as part of the test suite.
