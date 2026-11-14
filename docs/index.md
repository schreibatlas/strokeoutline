# StrokeOutline

**StrokeOutline converts finite 2D centerlines into sampled filled contours with constant or variable width.** It is a pre-1.0 geometry library for vector brushes, pressure-like paths, skeleton thickening, centerline fonts, map corridors, and other centerline-based applications.

Python >=3.10. Install the core package with `python -m pip install strokeoutline`. SVG parsing is optional: `python -m pip install 'strokeoutline[svg]'`.

StrokeOutline owns adaptive sampling and centerline expansion. PlanarCurve owns the neutral line and Bézier types. The core does not require InkGrammar or FontTools.

## Minimal example

```python
from strokeoutline import outline, path_from_polyline

path = path_from_polyline([(0, 0), (10, 0), (15, 5)])
result = outline(path, 4.0)
print(result.bounds)
```

Width means full diameter. Results contain immutable tuples of finite points, explicitly closed contours, and aggregate `(min_x, min_y, max_x, max_y)` bounds.

## Geometry and compatibility

- Constant, piecewise-linear, and callable positive width profiles are supported. Piecewise profile knots are sampled exactly; callable outputs are memoized per outline operation.
- The compatibility default maps width by segment index and restarts progress at each subpath. `OutlineConfig(width_parameterization="arclength")` opts into normalized physical arc-length progress.
- Open caps are `"round"` by default, with `"square"` and `"butt"` alternatives. The default join is `"legacy"`; `"miter"`, `"bevel"`, and `"round"` are opt-in styles.
- Adaptive subdivision is iterative. Unsatisfied tolerances, depth exhaustion, and no-progress subdivision raise `SubdivisionLimitError`.
- Closed centerlines produce two opposite-winding contours. `combine_outlines()` concatenates contours and does not perform Boolean union.

StrokeOutline is a sampled expander, not a complete SVG/CSS stroker or general-purpose Boolean/offset solver. See [limitations](limitations.md) before relying on output topology around cusps or self-intersections.

## Examples

The [examples guide](examples.md) covers seven scripts, expected invariants, optional dependencies, and import safety.

```{toctree}
:maxdepth: 2
:caption: User guide

getting-started
concepts
path-model
width-profiles
configuration
closed-paths
svg
composition
examples
limitations
integration
development
api/index
```
