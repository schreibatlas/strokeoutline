from strokeoutline import Line, Path2D, Subpath, outline, signed_area, winding

path = Path2D((
    Subpath((
        Line((0, 0), (40, 0)),
        Line((40, 0), (40, 30)),
        Line((40, 30), (0, 30)),
    ), closed=True),
))

result = outline(path, width=4.0)
print("contours:", len(result.contours))
for i, contour in enumerate(result.contours):
    print(i, "area=", signed_area(contour), "winding=", winding(contour))
print("bounds:", result.bounds)
