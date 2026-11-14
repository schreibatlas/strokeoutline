# Integration and migration

## Standalone use

StrokeOutline is a standalone geometry library. The core package depends on PlanarCurve for segment geometry, but has no InkGrammar or FontTools runtime dependency. Inputs are neutral 2D paths, and outputs are immutable closed contours.

## InkGrammar boundary

The architectural boundary is intentional:

- StrokeOutline owns centerline sampling, contour expansion, point/disc expansion, and width, cap, and join policy.
- InkGrammar integrations own shaped-text traversal, glyph-specific concerns, handwriting-model concerns, and adaptation into StrokeOutline inputs.
- Integrations should call StrokeOutline instead of copying its outlining algorithm.

## PlanarCurve ownership

PlanarCurve owns `Point2D`, `QuadraticBezier`, `CubicBezier`, `CubicPath`, and its segment types. StrokeOutline re-exports selected types for convenient construction and annotations, but does not redefine their semantics. A `planarcurve.CubicPath` can be passed directly to `outline()`. `path_from_cubic_path()` is available when an explicit adaptation to `Path2D` is useful.

This documents the current dependency boundary. It does not propose moving SVG parsing to PlanarCurve.

## Compatibility aliases

`expand_tap` is an alias of `outline_disc`. `strokeoutline.svg.expand_path` is an alias of `strokeoutline.svg.outline_svg_path`. These names are migration conveniences; new standalone code should prefer the canonical names.

## Compatibility defaults

The default join remains `"legacy"`, open paths retain round caps, and variable-width progress remains segment-index based. Miter, bevel, round joins, butt caps, and arc-length width progression are opt-in. This permits integrations to adopt the new modes without changing existing output by default.
