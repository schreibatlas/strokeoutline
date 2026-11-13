# Path model API

## StrokeOutline path types

```{autoclass} strokeoutline.Line
:members:
```

```{autoclass} strokeoutline.Subpath
:members:
```

```{autoclass} strokeoutline.Path2D
:members:
```

```{autofunction} strokeoutline.path_from_polyline

```

```{autofunction} strokeoutline.path_from_cubic_path

```

## PlanarCurve types accepted by the API

StrokeOutline re-exports the following geometry types from PlanarCurve:

- `Point2D`: a 2D point represented by two coordinates.
- `QuadraticBezier`: a quadratic Bézier segment.
- `CubicBezier`: a cubic Bézier segment.
- `CubicPath`: a sequence of cubic segments. `outline()` accepts it directly.
- `Segment`: the union of accepted line, quadratic Bézier, and cubic Bézier segment types.

These are re-exported for convenient construction and type annotations. `segment_start()` and `segment_end()` are internal model helpers, not top-level public exports.
