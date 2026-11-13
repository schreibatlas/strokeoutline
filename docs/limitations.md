# Limitations and non-goals

StrokeOutline is a sampled centerline expander. It is useful for many ordinary paths, but it is not a general-purpose offset or polygon-cleanup solver.

## Not a complete SVG/CSS stroker

The package does not expose complete SVG/CSS join and stroke semantics. It currently offers only round or square cap selection for open paths. SVG path parsing is an optional adapter, not SVG rendering.

## No robust Boolean cleanup

Generated contours are not guaranteed to be free of arbitrary self-intersections. StrokeOutline does not perform Boolean union or resolve topology changes. Use particular care with sharp cusps, self-intersecting centerlines, large widths relative to local curvature, degenerate or near-degenerate tangents, and offsets that overlap themselves.

## Width progress is not arc length

Variable width is parameterized by segment index and local segment parameter, not physical distance along the path. Progress restarts for every independent subpath. See [width profiles](width-profiles.md).

## Degenerate geometry

Zero-length segments and zero-length tangents are rejected during outlining with `DegeneratePathError`. Path model constructors may also raise ordinary `ValueError` or `TypeError` for invalid input; not every constructor error is wrapped in the outlining exception hierarchy.

## Adaptive subdivision limit

If adaptive sampling cannot satisfy its tolerances before `max_subdivision_depth`, outlining raises `SubdivisionLimitError`. Relaxing tolerances may permit the operation, at the cost of a less finely sampled result.

## Sampled output, not an analytic offset

The result is a deterministic sampled contour. It is not an exact symbolic offset curve for a line or Bézier path.
