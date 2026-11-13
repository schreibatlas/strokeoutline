# Configuration

`OutlineConfig` controls adaptive sampling and open-path caps. The defaults are:

```python
OutlineConfig(
    max_centerline_error=0.25,
    max_width_error=0.25,
    max_normal_angle_degrees=3.0,
    cap="round",
    max_subdivision_depth=18,
)
```

## `max_centerline_error`

Maximum tolerated geometric deviation from a straight chord during adaptive flattening, in the same units as the input coordinates. Smaller values generally produce more samples.

## `max_width_error`

Maximum tolerated deviation between the width profile and linear interpolation over a candidate sampling interval, in coordinate/width units. This matters for nonlinear callables and changes in piecewise profiles.

## `max_normal_angle_degrees`

Maximum accepted tangent direction change over a sampling interval, in degrees. Smaller values increase sampling around curvature. The value must be positive and less than 180.

## `cap`

Choose `"round"` or `"square"` for open paths. This setting has no effect on closed centerlines. StrokeOutline exposes no public CSS-style join selection.
Round caps are semicircular. Square caps extend the outline by half the endpoint width along the centerline tangent.

## `max_subdivision_depth`

Safety limit for recursive adaptive subdivision. It must be a positive integer. If the requested tolerances cannot be met by this depth, outlining raises `SubdivisionLimitError`.

## Tuning guidance

Retain the defaults unless the application has a reason to tune them. Decreasing tolerances generally increases geometric accuracy, contour vertex count, and work. Do not assume a particular vertex count or complexity for a given curve.
