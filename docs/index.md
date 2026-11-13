# StrokeOutline

**StrokeOutline converts 2D centerlines into deterministic filled contours with constant or variable width.** It provides reusable stroke-expansion geometry for vector graphics, pressure-like paths, skeleton thickening, centerline fonts, map corridors, and other centerline-based applications without requiring InkGrammar or an existing polygon.

StrokeOutline is a deterministic sampled centerline expander, not a complete SVG/CSS stroker or a general-purpose polygon Boolean/offset solver.

## Install

```bash
python -m pip install strokeoutline
```

For the optional SVG path adapter:

```bash
python -m pip install 'strokeoutline[svg]'
```

## Minimal example

```python
from strokeoutline import outline, path_from_polyline

path = path_from_polyline([(0, 0), (10, 0), (15, 5)])
result = outline(path, 4.0)

print(result.bounds)
print(len(result.contours))
```

The width is a full diameter. The result contains one or more explicitly closed contours, and bounds are ordered `(min_x, min_y, max_x, max_y)`.

## What StrokeOutline does

- Expands lines and quadratic or cubic Bézier centerlines into filled contours.
- Accepts constant, piecewise-linear, and callable width profiles.
- Handles open paths with round or square caps and closed centerlines with two oppositely wound contours.
- Supports optional SVG path parsing through a separate FontTools-backed adapter.
- Produces deterministic sampled output for the same inputs and configuration.

## What it does not do

StrokeOutline does not provide complete SVG/CSS stroke semantics, configurable join styles, robust self-intersection cleanup, or polygon Boolean union. Width progress follows segment-index parameterization, not physical arc length.

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
