# strokeoutline

`strokeoutline` expands 2D centerlines into deterministic filled contours with constant or variable stroke width. It is the reusable geometry extracted from InkGrammar's stroke outlining engine, without glyph, shaping, font, OCR, or handwriting-model responsibilities.

## Why use this?

Use StrokeOutline when a line-like feature is represented by a centerline but a filled contour is needed. It supports vector brushes, stylus-pressure paths, centerline fonts, skeleton thickening, and corridor visualization without requiring handwriting models or an existing polygon.

## Status

MVP / extraction release. The implementation intentionally preserves the current InkGrammar geometry before attempting robustness improvements.

## Install

```bash
python -m pip install strokeoutline
```

SVG path strings are optional:

```bash
python -m pip install 'strokeoutline[svg]'
```

## Core example

```python
from strokeoutline import Line, Path2D, Subpath, outline

path = Path2D((
    Subpath((Line((0, 0), (10, 0)),)),
))

result = outline(path, width=4.0)
print(result.bounds)
for contour in result.contours:
    print(contour)
```

`planarcurve.CubicPath` can also be passed directly to `outline()`. `planarcurve.CubicBezier` and `planarcurve.QuadraticBezier` can be used as segments inside `Subpath`.

## Variable width

```python
result = outline(
    path,
    width=[
        (0.0, 2.0),
        (0.25, 3.0),
        (1.0, 10.0),
    ],
)
```

Width is the full stroke diameter, not radius. Width profiles may be a positive constant, a strictly increasing piecewise-linear knot sequence spanning `0..1`, or a callable.

### Compatibility semantic

For extraction parity, normalized width progress is **segment-index progress**, not true physical arc length:

```text
u = (segment_index + local_segment_parameter) / segment_count
```

It restarts at `0` for each independent subpath. This is deliberate and should not be changed silently in a compatible release.

## Polyline and composition helpers

Use `path_from_polyline(points, closed=False)` to convert ordered finite 2D points into a `Path2D`. A closed polyline is implicitly connected to its first point. `combine_outlines(results)` concatenates contours in input order and recomputes aggregate bounds. It does not perform Boolean union or merge touching contours.

## SVG compatibility

```python
from strokeoutline.svg import outline_svg_path

result = outline_svg_path("M 0 0 C 0 100 100 100 100 0", width=4.0)
```

The SVG adapter uses FontTools only when imported. The geometric core does not import InkGrammar or FontTools.

## Geometry contract

- coordinates are ordinary `(x, y)` floats;
- output contours repeat the first point at the end;
- open paths support `round` and `square` caps;
- closed centerlines return two contours with opposite winding;
- output is deterministic for identical input/configuration;
- difficult self-intersections, sharp cusps, very large widths relative to curvature, and degenerate tangents are not yet a robust Boolean-offset problem solver.

### Not a complete SVG/CSS stroker

The optional SVG adapter parses SVG path geometry, but StrokeOutline does not implement complete SVG/CSS stroke joins or Boolean cleanup. It provides deterministic sampled centerline expansion with controlled tolerances, not a robust polygon offset solver for every topology.

## Versioning

Versions are derived dynamically from Git tags with `setuptools_scm`. Release tags should use `vX.Y.Z`, for example `v0.1.0`.

## Development

```bash
python -m pip install -e '.[dev]'
ruff format --check .
ruff check .
pytest
python -m build
python -m twine check dist/*
```

## Examples

See [`examples/README.md`](examples/README.md) for the five runnable, domain-neutral examples. They can be executed individually with `python examples/<script>.py`; the test suite runs all five.

## Extraction boundary

The package owns centerline-to-contour geometry and point-disc expansion. InkGrammar should retain `ShapedText` traversal as an adapter that calls this package. The MVP includes an SVG compatibility adapter; a future public parsed-segment API in `planarcurve` can become the single SVG parsing owner without changing `strokeoutline`'s core API.

## License

Apache-2.0.
