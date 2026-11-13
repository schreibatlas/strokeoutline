# Path model

StrokeOutline uses a neutral path model built from ordered 2D segments.

## `Line`

```python
Line(p0, p1)
```

Both endpoints are finite 2D coordinates. `Line` is defined by StrokeOutline.

## Bézier segments

`QuadraticBezier` and `CubicBezier` are types from `planarcurve`. They can be used directly as segments in a `Subpath`, alongside `Line`.

## `Subpath`

```python
Subpath(segments, closed=False)
```

A subpath requires at least one segment. Its segment sequence must contain `Line`, `QuadraticBezier`, or `CubicBezier` objects connected in order. Connectivity currently uses exact endpoint equality.

When `closed=True`, an implicit closing `Line` is added if the last endpoint differs from the first start point. A repeated explicit closing segment is not required. Closing a centerline produces two output contours; see [closed paths](closed-paths.md).

## `Path2D`

```python
Path2D(subpaths)
```

A `Path2D` contains one or more independent subpaths. Each subpath is outlined independently, and normalized width progress restarts from zero for each one.

## `path_from_polyline()`

```python
from strokeoutline import path_from_polyline

path = path_from_polyline(
    [(0, 0), (10, 0), (10, 10)],
    closed=True,
)
```

At least two finite 2D points are required. `closed=True` adds an implicit closing segment. Repeated adjacent points are retained, not removed; outlining such a path raises `DegeneratePathError` for its zero-length segment.

## `path_from_cubic_path()`

Use `path_from_cubic_path()` to adapt a `planarcurve.CubicPath` to `Path2D`. For ordinary outlining, adaptation is optional because `outline()` accepts `CubicPath` directly.
