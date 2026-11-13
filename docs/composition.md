# Combining results

`combine_outlines()` concatenates contours from multiple results in input order and recomputes aggregate bounds:

```python
from strokeoutline import combine_outlines, outline_disc

a = outline_disc((0, 0), 4.0)
b = outline_disc((10, 0), 6.0)
combined = combine_outlines([a, b])
```

This operation does not clip, union, merge, or clean up overlaps. The contour order is preserved. Consumers that need polygon Boolean operations should use a separate geometry/Boolean library after StrokeOutline.

Combining an empty iterable returns an empty result:

```python
OutlineResult((), None)
```

Stable doctest for the empty case:

```{doctest}
>>> from strokeoutline import combine_outlines
>>> combined = combine_outlines(())
>>> combined.contours
()
>>> combined.bounds is None
True
```
