# Limitations and non-goals

StrokeOutline is a sampled centerline expander. It is useful for ordinary strokes, but is not a general-purpose analytic offset or polygon-cleanup solver.

## Joins, caps, and SVG/CSS semantics

Open caps can be round, square, or butt. The default join, `legacy`, preserves a sampled bisector construction with hidden compatibility clamps. It is not a standard miter or bevel join. Explicit sampled `miter`, `bevel`, and `round` joins are available, with an over-limit miter falling back to bevel geometry. These choices do not provide complete SVG/CSS stroke semantics.

The optional SVG adapter parses path geometry through FontTools. It does not render SVG, styles, transforms, or CSS strokes.

## No robust Boolean cleanup

Generated contours are not guaranteed to be free of arbitrary self-intersections. StrokeOutline does not perform Boolean union or resolve topology changes. Use care with sharp cusps, self-intersecting centerlines, large widths relative to local curvature, and offsets that overlap themselves.

## Width progress

The compatibility default distributes width progress evenly by segment index, not physical distance. Progress restarts for each independent subpath and includes the implicit closing segment of a closed path. Opt into `width_parameterization="arclength"` for normalized physical path-length progress. See [width profiles](width-profiles.md).

## Numerical geometry

Coordinates and widths may use any consistent units; there is no fixed absolute geometry epsilon. Exact zero-length segments or tangent directions are rejected. Finite precision still limits features that are much smaller than the local floating-point spacing, especially after large coordinate translations. Near reversals and endpoint cusps can be ill-conditioned even when coordinates are finite.

## Adaptive subdivision

Sampling may fail for discontinuous or extremely demanding profiles. If tolerances cannot be met within `max_subdivision_depth`, or a floating-point midpoint no longer lies strictly inside its interval, outlining raises `SubdivisionLimitError`. The implementation is iterative and does not leak Python `RecursionError` for large accepted depth settings.

## Sampled output

The result is a deterministic sampled contour, not an exact symbolic offset curve. Tolerances constrain the sampling checks; they do not guarantee simple polygon topology or Boolean-clean output.
