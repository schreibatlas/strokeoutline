# Core API

The primary API is re-exported from `strokeoutline`. The optional parser is in `strokeoutline.svg`.

## Public type aliases

- `WidthProfile`: a positive real scalar, an iterable of `(u, width)` real-valued knots, or a callable from normalized progress to width. Knot positions span `0..1`, increase strictly, and have positive finite widths. Boolean values are rejected.
- `Contour`: a tuple of 2D points.
- `CapStyle`: `"round"`, `"square"`, or `"butt"`.
- `JoinStyle`: `"legacy"`, `"miter"`, `"bevel"`, or `"round"`.
- `WidthParameterization`: `"segment"` or `"arclength"`.

Width progress defaults to segment-index mapping for compatibility. Arc-length mapping is opt-in. See [width profiles](../width-profiles.md).


The direct `width_parameterization="arclength"` keyword opts into physical path progress and overrides the config value. When omitted, `config.width_parameterization` applies, defaulting to `"segment"` for compatibility.
```{autodata} strokeoutline.DEFAULT_OUTLINE_CONFIG

```

```{autoclass} strokeoutline.OutlineConfig
:members:
```

```{autoclass} strokeoutline.OutlineResult
:members:
```

## Main operations

```{autofunction} strokeoutline.outline

```

```{autofunction} strokeoutline.outline_disc

```

`expand_tap` is a compatibility alias of `outline_disc`; prefer the canonical name for new code.

```{autofunction} strokeoutline.combine_outlines

```

`combine_outlines()` preserves contour order and recomputes bounds. It does not perform a Boolean union.

## Contour helpers

```{autofunction} strokeoutline.signed_area

```

```{autofunction} strokeoutline.winding

```

## Exceptions

```{autoclass} strokeoutline.OutlineError

```

```{autoclass} strokeoutline.InvalidWidthError

```

```{autoclass} strokeoutline.DegeneratePathError

```

```{autoclass} strokeoutline.SubdivisionLimitError

```

| Exception | Meaning | Typical cause |
| --- | --- | --- |
| `OutlineError` | Base outlining failure | Base class for package geometry failures |
| `InvalidWidthError` | Invalid width specification or value | Non-positive or non-finite width, malformed knots, or invalid callable result |
| `DegeneratePathError` | Degenerate centerline geometry | Zero-length sampled segment or tangent |
| `SubdivisionLimitError` | Adaptive subdivision could not satisfy tolerances | Depth exhaustion, floating-point no-progress, or geometry/profile too difficult at the configured tolerances |

Path-model constructors may separately raise ordinary `ValueError` or `TypeError` for invalid arguments.

## Version

```{autodata} strokeoutline.__version__

```
