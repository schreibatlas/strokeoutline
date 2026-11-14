# Concepts

## Centerline and full stroke width

A **centerline** is an ordered path through the middle of a stroke. **Width** is the full diameter centered on that path. StrokeOutline samples the centerline, computes offsets by half the local width, and joins the samples into closed contours.

```{figure} _static/basic-outline.svg
:alt: A centerline with left and right offsets, joined by open-path caps into a closed outline.

A sampled open centerline expanded by half its full stroke width.
```

## Geometry pipeline

For each independent subpath, StrokeOutline:

1. Normalizes the path and width profile.
2. Adaptively samples centerline geometry and width progress.
3. Computes sampled normals and applies the selected join construction.
4. Adds the configured cap for an open path, or constructs two offsets for a closed centerline.
5. Closes the output contours and computes aggregate bounds.

This is a deterministic sampled expansion, not an analytic offset curve or a polygon Boolean operation.

## Sampling and approximation

Sampling checks chord deviation, width-profile deviation from linear interpolation, and tangent direction change. Piecewise width knots split intervals so each specified knot is sampled. Callable profiles are memoized by normalized progress during a single outline operation.

`OutlineConfig` provides the tolerances and subdivision limit. If a profile is discontinuous or too difficult to approximate, outlining can raise `SubdivisionLimitError`. The subdivision process is iterative and detects floating-point no-progress rather than leaking `RecursionError`.

## Join and cap choices

The default join, `"legacy"`, preserves the extracted sampled bisector construction. Its denominator and offset-length clamps are compatibility behavior, not standard miter or bevel semantics. Opt-in `"miter"`, `"bevel"`, and `"round"` joins use explicit sampled constructions. `miter_limit` bounds miter length; over-limit miters fall back to bevel geometry.

Open paths default to round caps. Square caps extend by half the endpoint width along an analytic endpoint tangent, with a secant fallback for a degenerate endpoint derivative. Butt caps stop at the endpoint plane. Closed paths have no caps.

## Output and immutability

The main operations return an immutable `OutlineResult`. Its outer contour collection, each contour, each point, and bounds are normalized to tuples. Contours must be finite and explicitly closed. Bounds must be finite and match the contour coordinates; an empty result has no bounds.

Open subpaths produce one contour each. Closed centerlines produce two contours with opposite winding. `combine_outlines()` concatenates contours in input order and recomputes bounds; it does not union geometry.

## Coordinates and ownership

StrokeOutline has no fixed unit system. Coordinates and widths must use consistent units. There is no DPI conversion or absolute coordinate epsilon. Exact zero-length geometry is rejected, while IEEE floating-point precision still limits features that are tiny relative to a large translation.

PlanarCurve owns its neutral point and Bézier types. StrokeOutline re-exports some of them for convenience, but owns the expansion policy and output contours.
