# Path model

StrokeOutline uses a neutral path model built from ordered 2D segments. StrokeOutline's own model types are immutable dataclasses. `Line` endpoints are normalized to finite float pairs; `OutlineResult` also normalizes contour points.

## `Line`

```python
Line(p0, p1)
```

Both endpoints accept an iterable containing exactly two finite numeric coordinates. Boolean coordinates, strings, non-finite values, and malformed points are rejected with `ValueError`. A zero-length `Line` can be constructed, but `outline()` rejects the degenerate geometry.

`Line` is defined by StrokeOutline. `QuadraticBezier`, `CubicBezier`, `Point2D`, `CubicPath`, and `Segment` originate from PlanarCurve; some are re-exported by StrokeOutline for convenient construction and annotations.

## Bézier segments

`QuadraticBezier` and `CubicBezier` from PlanarCurve can be used directly in a `Subpath`, alongside `Line`. PlanarCurve remains the semantic owner of these segment types.

## `Subpath`

```python
Subpath(segments, closed=False)
```

A subpath requires at least one `Line`, `QuadraticBezier`, or `CubicBezier` segment. Adjacent endpoints must compare exactly equal. When `closed=True`, an implicit closing `Line` is added during outlining if the last endpoint differs from the first start point. A repeated explicit closing segment is not required.

Outlining a closed centerline produces two explicitly closed contours with opposite winding. The implicit closing segment participates in width progress. See [closed paths](closed-paths.md).

## `Path2D`

```python
Path2D(subpaths)
```

A `Path2D` contains one or more independent subpaths. Each subpath is outlined independently, and normalized width progress restarts at zero for each one. Constructors normalize the provided collections to tuples.

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

Use `path_from_cubic_path()` to adapt a `planarcurve.CubicPath` to `Path2D`. Adaptation is optional because `outline()` accepts `CubicPath` directly.
