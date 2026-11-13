# Concepts

## Centerline versus outline

A **centerline** is an ordered geometric path through the middle of a stroke. **Width** is the full diameter centered on that path. An **outline** is one or more closed contours built by sampling the centerline and offsetting its samples.

```{figure} _static/basic-outline.svg
:alt: A centerline with left and right offsets, joined by open-path caps into a closed outline.

A sampled open centerline expanded by half the full stroke width on each side.
```

## Sampling and determinism

StrokeOutline does not construct a mathematically exact analytic offset. It deterministically:

1. Adaptively samples the centerline.
2. Checks centerline deviation, width-profile deviation, and tangent direction change.
3. Computes local normals and offsets samples by half the requested width.
4. Adds caps for open paths.
5. Closes each resulting contour.

The adaptive tolerances are configurable with `OutlineConfig`. More accuracy generally means more samples and more work.

## Output contract

The main operations return an `OutlineResult` with this shape:

```python
OutlineResult(
    contours: tuple[Contour, ...],
    bounds: tuple[float, float, float, float] | None,
)
```

A `Contour` is a tuple of 2D points. Every non-empty output contour is explicitly closed by repeating its first point as its last point. Bounds aggregate all returned contours in `(min_x, min_y, max_x, max_y)` order. Bounds are `None` when there are no contours, as with `combine_outlines(())`.

Closed centerlines return two contours with opposite winding. Open paths return one contour per subpath. A `Path2D` can contain multiple independent subpaths, each outlined separately.

## Units

StrokeOutline has no fixed unit system. Coordinates and widths must use the same units, such as pixels, font units, millimeters, or arbitrary model coordinates. No DPI conversion is performed.
