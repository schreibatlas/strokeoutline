# Core API

The names below are re-exported from the top-level `strokeoutline` package.

## Types and configuration

`WidthProfile` is a positive constant, a sequence of `(u, width)` knots, or a callable from normalized progress to width. Knot positions span `0..1` and are strictly increasing. Width progress is based on segment index, not arc length; see [width profiles](../width-profiles.md).

`Contour` is a tuple of 2D points. `CapStyle` is the literal choice `"round"` or `"square"`, used for open paths.

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

| Exception               | Meaning                                           | Typical cause                                                              |
| ----------------------- | ------------------------------------------------- | -------------------------------------------------------------------------- |
| `OutlineError`          | Base outlining failure                            | Base class for package geometry failures                                   |
| `InvalidWidthError`     | Invalid width specification or value              | Non-positive/non-finite width, malformed knots, or invalid callable result |
| `DegeneratePathError`   | Degenerate centerline geometry                    | Zero-length segment or tangent                                             |
| `SubdivisionLimitError` | Adaptive subdivision could not satisfy tolerances | Tolerances or geometry/profile too difficult within the configured depth   |

Model constructors may separately raise ordinary `ValueError` or `TypeError` for invalid arguments.

## Version

```{autodata} strokeoutline.__version__

```
