from planarcurve import CubicPath, CubicSegment
from strokeoutline import outline

centerline = CubicPath(
    (0, 0),
    (
        CubicSegment((15, 30), (35, 30), (50, 0)),
        CubicSegment((65, -30), (85, -30), (100, 0)),
    ),
)

result = outline(centerline, lambda u: 3.0 + 7.0 * u)
print("contours:", len(result.contours))
print("vertices:", len(result.contours[0]))
print("bounds:", result.bounds)
