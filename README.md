# StrokeOutline

StrokeOutline converts finite 2D centerlines into sampled, explicitly closed contours with constant or variable stroke width. It is a pre-1.0 geometry library extracted from InkGrammar. PlanarCurve owns the neutral line and Bézier types; StrokeOutline owns sampling, stroke expansion, and output contours.

StrokeOutline is not a complete SVG/CSS stroker or a general polygon offset/Boolean engine.

## Requirements and installation

Python >=3.10. Install the core package with:

```bash
python -m pip install strokeoutline
```

SVG path parsing is optional and requires FontTools:

```bash
python -m pip install 'strokeoutline[svg]'
```


Contour rasterization is optional and requires Pillow:

```bash
python -m pip install 'strokeoutline[raster]'
```

## Quick start

```python
from strokeoutline import outline, path_from_polyline

path = path_from_polyline([(0, 0), (10, 0), (15, 5)])
result = outline(path, width=4.0)

print(result.bounds)  # (min_x, min_y, max_x, max_y)
```

Width is the full stroke diameter, not the radius. `OutlineResult` is immutable. Its contours and points are tuples, each output contour repeats its first point at the end, and aggregate bounds are `None` only when there are no contours.

## Width profiles

`outline()` accepts a positive real scalar, a piecewise-linear iterable of `(u, width)` knots spanning `0..1`, or a callable returning a finite positive width. Boolean widths and knots are rejected. Piecewise knots are sampled at their specified progress positions. Callable results are memoized within one `outline()` call. Callbacks should be deterministic and sufficiently continuous to satisfy the sampling tolerance.

The compatibility default is segment-index progress, restarted for each independent subpath:

```text
u = (segment_index + local_segment_parameter) / segment_count
```

It is not physical distance. An implicit closing segment participates in the segment count of a closed subpath. To opt into normalized physical arc length, pass `width_parameterization="arclength"` to `outline()` or `outline_svg_path()`. The existing `OutlineConfig(width_parameterization="arclength")` option remains supported.

```python
result = outline(path, [(0.0, 2.0), (1.0, 6.0)], width_parameterization="arclength")
```

`outline_disc(center, diameter)` evaluates a width profile at `u == 0.5`, since a point has no path progression.

## Caps and joins

Open-path caps default to `"round"`; `"square"` extends by half the endpoint width along the analytic endpoint tangent, and `"butt"` ends at the centerline endpoint. Caps do not apply to closed paths.

The default join is `"legacy"`, preserving the sampled bisector behavior. It is not a standard miter or bevel join. Opt-in `join="miter"`, `"bevel"`, or `"round"` selects explicit sampled join construction. `miter_limit` is a positive ratio, defaulting to `4.0`; over-limit miters fall back to bevel geometry.

## Sampling and numerical limits

`OutlineConfig` controls centerline deviation, width interpolation error, tangent-angle change, subdivision depth, caps, joins, and width parameterization. Subdivision is iterative. If tolerances cannot be met, the depth limit is exceeded, or floating-point subdivision makes no progress, StrokeOutline raises `SubdivisionLimitError`, not `RecursionError`.

Coordinates and widths may use any consistent units. There is no fixed pixel or font-unit scale. Exact zero-length geometry is rejected; finite precision still affects extremely small features relative to large coordinate translations.

The output is sampled, not an analytic offset. StrokeOutline does not perform Boolean cleanup or guarantee simple topology for arbitrary self-intersections, cusps, or very large offsets.

## Composition, PlanarCurve, and SVG

`combine_outlines()` concatenates contours in order and recomputes bounds. It does not perform a Boolean union. `planarcurve.CubicPath` can be passed directly to `outline()`; PlanarCurve remains the semantic owner of its geometry types, which StrokeOutline also re-exports as a convenience.

The optional `strokeoutline.svg` adapter parses path geometry through FontTools. Regression-tested commands include relative coordinates, horizontal/vertical lines, smooth cubic/quadratic commands, arcs converted to cubic segments, and close paths. SVG parsing is not rendering and does not imply complete CSS/SVG stroke semantics.

## Examples and documentation

The [examples guide](examples/README.md) lists seven runnable scripts, their optional dependencies, and their semantic invariants. Importing an example has no output or filesystem side effects.

The [Sphinx documentation](docs/index.md) contains the user guide, concepts, API reference, SVG details, and limitations.

## Development

```bash
python -m pip install -e '.[dev]'
ruff format --check .
ruff check .
pytest
python docs/make.py html
python docs/make.py doctest
python -m build
python -m twine check dist/*
```
