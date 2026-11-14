# Closed centerlines

Closed centerlines are expanded differently from open paths:

```python
from strokeoutline import outline, path_from_polyline, signed_area, winding

path = path_from_polyline(
    [(0, 0), (40, 0), (40, 30), (0, 30)],
    closed=True,
)
result = outline(path, 4.0)

for contour in result.contours:
    print(signed_area(contour), winding(contour))
```

A closed centerline returns two explicitly closed contours with opposite winding. The cap setting is irrelevant. Do not rely on a particular returned contour index being the geometric outer contour. Its implicit closing segment participates in width progress; segment-index progress remains the default, and arc-length progress is opt-in.

```{figure} _static/closed-centerline.svg
:alt: A closed rectangular centerline expanded into two contours with opposite winding directions.

The two offsets of a closed centerline have opposite winding.
```

## `signed_area()` and `winding()`

`signed_area(points)` computes the signed polygon area. The final point may repeat the first point, but closure is not required. `winding(points)` returns `"ccw"`, `"cw"`, or `"degenerate"` based on that area.
