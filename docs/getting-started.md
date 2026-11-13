# Getting started

Go from installation to a useful outline in a few minutes.

## Installation

Install the geometry library:

```bash
python -m pip install strokeoutline
```

For SVG path strings, install the optional adapter dependency:

```bash
python -m pip install 'strokeoutline[svg]'
```

For a development checkout, install the development and documentation dependencies:

```bash
python -m pip install -e '.[dev]'
python -m pip install -r docs/requirements.txt
```

FontTools is not required for core outlining.

## First outline

`path_from_polyline()` is the shortest way to create a centerline:

```python
from strokeoutline import outline, path_from_polyline

path = path_from_polyline([(0, 0), (20, 0), (30, 10)])
result = outline(path, width=6.0)

print(result.bounds)
for contour in result.contours:
    print(len(contour))
```

Here `width=6.0` is a six-unit full diameter, not a radius. `result.contours` is a tuple of closed contours; each non-empty contour repeats its first point at the end. `result.bounds` is `(min_x, min_y, max_x, max_y)`, or `None` for an empty aggregate result.

Input coordinates and widths have no prescribed unit. Use the same coordinate system for both.

### Stable doctest

```{doctest}
>>> from strokeoutline import path_from_polyline, outline
>>> path = path_from_polyline([(0, 0), (10, 0)])
>>> result = outline(path, 2.0)
>>> result.bounds
(-1.0, -1.0, 11.0, 1.0)
>>> len(result.contours)
1
```

## A Bézier path

The path model also accepts `planarcurve` segments directly:

```python
from planarcurve import CubicBezier, QuadraticBezier
from strokeoutline import Line, Path2D, Subpath, outline

path = Path2D(
    (
        Subpath(
            (
                Line((0, 0), (10, 0)),
                QuadraticBezier((10, 0), (15, 8), (20, 0)),
                CubicBezier((20, 0), (25, -8), (30, 8), (35, 0)),
            )
        ),
    )
)
result = outline(path, 4.0)
```

## Next steps

- Learn the [path model](path-model.md) and [width profiles](width-profiles.md).
- Tune [adaptive sampling](configuration.md) when needed.
- Read about [SVG input](svg.md), [closed paths](closed-paths.md), and [limitations](limitations.md).
- Browse the [examples](examples.md) and [API reference](api/index.md).
