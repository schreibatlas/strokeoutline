# Width profiles

Width is the full stroke diameter. The local offset on each side is half the requested width.

## Supported profiles

### Constant width

```python
result = outline(path, 4.0)
```

A positive `numbers.Real` scalar is accepted; booleans are not widths.

### Piecewise-linear width

A knot iterable defines linear interpolation between `(u, width)` pairs:

```python
profile = [
    (0.0, 2.0),
    (0.3, 4.0),
    (0.7, 16.0),
    (1.0, 6.0),
]
result = outline(path, profile)
```

A profile requires at least two knots, begins at `0`, ends at `1`, and has strictly increasing finite positions. Widths must be finite and positive. Every interior knot is sampled exactly, including knots that fall inside a segment.

```{figure} _static/variable-width.svg
:alt: A centerline expanded from narrow to wide and back to narrow, with full diameter against normalized progress.

A pressure-like width profile over normalized progress.
```

### Callable width

```python
result = outline(path, lambda u: 3.0 + 7.0 * u)
```

The callable must return a finite positive numeric width. Successful results are normalized and memoized for each distinct progress value during one `outline()` call. The callback should be deterministic and pure for a given `u`, and sufficiently continuous for the configured `max_width_error` to be satisfiable. A discontinuous or too rapidly changing callback may raise `SubdivisionLimitError`.

## Segment-index progress, the compatibility default

For `width_parameterization="segment"`, progress follows:

```text
u = (segment_index + local_segment_parameter) / segment_count
```

For a two-segment subpath, the first segment spans `u=0..0.5` and the second spans `u=0.5..1`. A short and a long segment receive equal normalized spans. Splitting a segment changes where the profile applies. This extracted behavior remains the default.

The implicit closing segment of a closed subpath is inserted before sampling and participates in the legacy segment count. Progress restarts at zero for every independent subpath.

## Arc-length progress

Select `OutlineConfig(width_parameterization="arclength")` to use cumulative physical path length normalized to `0..1` for each subpath. Line lengths are direct; Bézier segment lengths are numerically integrated. This mode is opt-in and does not change compatibility behavior.

For two unequal segments, a knot at `u=0.5` lies halfway along the combined physical path in arc-length mode. In segment mode it lies at the boundary between the segments, regardless of their lengths.

## `outline_disc()` and aliases

A point has no path progression, so `outline_disc(center, diameter)` evaluates a supplied width profile at `u == 0.5`. `expand_tap` remains a compatibility alias for `outline_disc`; new code should use the canonical name.

See [limitations](limitations.md) for sampled geometry and offset-topology caveats.
