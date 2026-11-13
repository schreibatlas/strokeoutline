# Integration and migration

## Standalone use

StrokeOutline can be used directly as a geometry library. The core package depends on PlanarCurve for segment geometry, but has no InkGrammar dependency. Inputs are neutral 2D paths, and outputs are closed contours.

## InkGrammar boundary

The architectural boundary is intentional:

- StrokeOutline owns centerline-to-contour geometry and point/disc expansion.
- InkGrammar integrations own shaped-text traversal, glyph-specific concerns, handwriting-model concerns, and adaptation into StrokeOutline inputs.
- Integrations should call StrokeOutline instead of copying its outlining algorithm.

## Compatibility aliases

`expand_tap` is an alias of `outline_disc`. `strokeoutline.svg.expand_path` is an alias of `strokeoutline.svg.outline_svg_path`. These names are migration conveniences; new standalone code should prefer the canonical names.

## PlanarCurve

PlanarCurve provides the segment geometry types used by StrokeOutline. A `planarcurve.CubicPath` can be passed directly to `outline()`. `path_from_cubic_path()` is available when an explicit adaptation to `Path2D` is useful.

This documents the current dependency boundary. It does not propose moving SVG parsing to PlanarCurve.
