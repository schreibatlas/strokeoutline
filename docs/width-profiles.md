# Width profiles

## Constant width

```python
result = outline(path, 4.0)
```

> **Width is the full stroke diameter, not the radius.** The offset on each side is based on half the requested width.

## Piecewise-linear width

A sequence of `(u, width)` knots defines linear interpolation between widths:

```python
profile = [
    (0.0, 2.0),
    (0.3, 4.0),
    (0.7, 16.0),
    (1.0, 6.0),
]
result = outline(path, profile)
```

```{figure} _static/variable-width.svg
:alt: A centerline expanded from narrow to wide and back to narrow, with a chart of full diameter against normalized segment-index progress.

A pressure-like width profile over normalized segment-index progress.
```

A profile requires at least two knots, starts at position `0`, ends at `1`, and has strictly increasing positions. Every position and width must be finite, and every width must be positive.

## Callable width

A callable receives normalized progress and returns a width:

```python
result = outline(path, lambda u: 3.0 + 7.0 * u)
```

The return value is converted to `float` when possible and must be finite and positive. Adaptive sampling may evaluate the callable multiple times, so it should be deterministic and safe to call repeatedly.

## Normalized progress is based on segment index

Width progress uses this formula:

```text
u = (segment_index + local_segment_parameter) / segment_count
```

For a two-segment subpath, segment 0 spans approximately `u = 0.0..0.5` and segment 1 spans `u = 0.5..1.0`. A very short segment and a very long segment receive equal normalized spans. Splitting one geometric segment into two changes where a profile is applied.

This is preserved compatibility behavior. It is **not** parameterized by physical arc length.

## Independent subpaths

Progress restarts at zero for each `Subpath`, including when a `Path2D` contains multiple strokes.

## `outline_disc()`

A point has no path progression. `outline_disc(center, width)` therefore evaluates a variable width profile at `u == 0.5` to choose the disc diameter.

See [limitations](limitations.md) for cases where variable-width offsets need special care.
