# Examples

The repository includes five executable examples. They demonstrate the public API; run them from the repository root with Python after installing the project and optional SVG extra if using example 3. Source links point to the project's GitHub repository.

## 1. Basic centerline

[`examples/01_basic_centerline.py`](https://github.com/schreibatlas/strokeoutline/blob/main/examples/01_basic_centerline.py) combines a line, quadratic Bézier, and cubic Bézier into one path and outlines it at constant width. The implementation adaptively samples the curved segments.

```python
from planarcurve import CubicBezier, QuadraticBezier
from strokeoutline import Line, Path2D, Subpath, outline

path = Path2D(
    (
        Subpath(
            (
                Line((0, 0), (25, 0)),
                QuadraticBezier((25, 0), (40, 25), (55, 0)),
                CubicBezier((55, 0), (65, -20), (80, 20), (90, 0)),
            )
        ),
    )
)
result = outline(path, width=6.0)
```

It produces one explicitly closed contour for this open subpath.

```{figure} _static/basic-outline.svg
:alt: A representative open centerline expanded into one rounded, explicitly closed contour.

Illustrative outline for an open centerline.
```

## 2. Variable width

[`examples/02_variable_width.py`](https://github.com/schreibatlas/strokeoutline/blob/main/examples/02_variable_width.py) applies piecewise-linear width knots and customizes `OutlineConfig(max_width_error=...)` to control width-profile sampling.

```python
profile = [(0.0, 2.0), (0.3, 4.0), (0.7, 16.0), (1.0, 6.0)]
result = outline(path, profile, config=OutlineConfig(max_width_error=0.05))
```

Widths are full diameters. Progress uses segment-index parameterization, not physical arc length.

```{figure} _static/variable-width.svg
:alt: A centerline expanded from narrow to wide and back to narrow with the corresponding width-profile chart.

Illustrative variable-width outline and profile.
```

## 3. SVG adapter

[`examples/03_svg_adapter.py`](https://github.com/schreibatlas/strokeoutline/blob/main/examples/03_svg_adapter.py) passes SVG path data containing multiple subpaths to the optional FontTools adapter.

```python
from strokeoutline.svg import outline_svg_path

result = outline_svg_path(
    "M 0 0 C 0 60 60 60 60 0 M 80 0 Q 100 40 120 0",
    width=5.0,
)
```

Install `strokeoutline[svg]` to run this example. Each parsed subpath is outlined independently.

## 4. Closed centerline

[`examples/04_closed_centerline.py`](https://github.com/schreibatlas/strokeoutline/blob/main/examples/04_closed_centerline.py) uses an implicit closing segment, then reports the signed area and winding of the two resulting contours.

```python
from strokeoutline import outline, path_from_polyline, signed_area, winding

path = path_from_polyline(
    [(0, 0), (40, 0), (40, 30), (0, 30)],
    closed=True,
)
result = outline(path, width=4.0)
for contour in result.contours:
    print(signed_area(contour), winding(contour))
```

The contours are explicitly closed and have opposite winding. No outer-contour ordering is promised.

```{figure} _static/closed-centerline.svg
:alt: A closed centerline expands to two explicitly closed contours with opposite winding.

Illustrative result for the closed-centerline example.
```

## 5. PlanarCurve interoperability

[`examples/05_planarcurve_interop.py`](https://github.com/schreibatlas/strokeoutline/blob/main/examples/05_planarcurve_interop.py) passes a `planarcurve.CubicPath` directly to `outline()` and uses a callable width profile.

```python
result = outline(centerline, lambda u: 3.0 + 7.0 * u)
```

The callable may be evaluated repeatedly during adaptive sampling.

## Domain-neutral examples

A polyline corridor can represent a route or any other centerline in consistent application units:

```python
from strokeoutline import outline, path_from_polyline

route = path_from_polyline(
    [
        (0, 0),
        (20, 5),
        (40, 5),
        (55, 20),
    ]
)
corridor = outline(route, width=8.0)
```

A pressure-like profile describes width variation, but StrokeOutline does not read stylus pressure events itself:

```python
pressure_like = [
    (0.0, 2.0),
    (0.2, 4.0),
    (0.6, 10.0),
    (1.0, 3.0),
]
result = outline(route, pressure_like)
```

Multiple independent strokes can be represented with `Path2D`. Width progress restarts at zero for each subpath:

```python
from strokeoutline import Line, Path2D, Subpath, outline

path = Path2D(
    (
        Subpath((Line((0, 0), (20, 0)),)),
        Subpath((Line((0, 10), (20, 10)),)),
    )
)
result = outline(path, 4.0)
```
