from planarcurve import CubicBezier, QuadraticBezier
from strokeoutline import Line, Path2D, Subpath, outline

path = Path2D((
    Subpath((
        Line((0, 0), (25, 0)),
        QuadraticBezier((25, 0), (40, 25), (55, 0)),
        CubicBezier((55, 0), (65, -20), (80, 20), (90, 0)),
    )),
))

result = outline(path, width=6.0)
print("contours:", len(result.contours))
print("vertices:", [len(contour) for contour in result.contours])
print("bounds:", result.bounds)
