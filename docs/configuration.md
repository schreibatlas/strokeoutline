# Configuration

`OutlineConfig` controls adaptive sampling, caps, joins, and normalized width progress. Defaults are:

```python
OutlineConfig(
    max_centerline_error=0.25,
    max_width_error=0.25,
    max_normal_angle_degrees=3.0,
    cap="round",
    join="legacy",
    miter_limit=4.0,
    width_parameterization="segment",
    max_subdivision_depth=18,
)
```

All tolerances and `miter_limit` must be positive and finite. `max_normal_angle_degrees` must also be less than 180. `max_subdivision_depth` is a positive integer.

## Sampling tolerances

### `max_centerline_error`

Maximum tolerated geometric deviation from a straight chord, in input coordinate units. Smaller values generally produce more samples. This tolerance also controls sampled cap and round-join arcs.

### `max_width_error`

Maximum tolerated deviation between width progress and linear interpolation over a candidate interval, in width units. Piecewise-linear knot intervals are split at their exact knots; this tolerance governs additional adaptive sampling within an interval.

### `max_normal_angle_degrees`

Maximum accepted tangent direction change over a sampling interval. Smaller values increase sampling around curvature.

### `max_subdivision_depth`

Maximum adaptive subdivision depth for each interval. The implementation uses an explicit stack, not Python recursion. If the tolerances cannot be met by this depth, or floating-point subdivision stops making progress, outlining raises `SubdivisionLimitError`.

## `cap`

Choose `"round"`, `"square"`, or `"butt"` for open paths. The setting has no effect on closed centerlines.

- Round caps are semicircular around the endpoint.
- Square caps extend by half the endpoint width along the endpoint tangent.
- Butt caps stop at the centerline endpoint plane.

Endpoint tangents use analytic segment derivatives where available, with a secant fallback for a degenerate endpoint derivative.

## `join` and `miter_limit`

`join="legacy"` is the compatibility default. It retains the extracted sampled bisector algorithm and its clamps. It is not a standard SVG/CSS miter or bevel join.

Opt into `"miter"`, `"bevel"`, or `"round"` to select explicit sampled joins. `miter_limit` is the maximum ratio of miter length to half-width. A miter that exceeds the limit falls back to bevel geometry. Join styles do not imply Boolean cleanup or robust handling of arbitrary self-intersections.

## `width_parameterization`

`"segment"` is the compatibility default. Each segment receives an equal share of normalized width progress. `"arclength"` maps progress to cumulative physical path length, normalized over the subpath; Bézier lengths are numerically integrated. For a closed subpath, its implicit closing segment participates in either mode.

See [width profiles](width-profiles.md) for the mapping formulas and examples.

## Tuning guidance

Retain the defaults unless the application has a reason to tune them. Decreasing tolerances generally increases accuracy, contour vertices, and work. Do not rely on a particular adaptive vertex count.
