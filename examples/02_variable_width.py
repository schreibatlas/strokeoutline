from strokeoutline import Line, OutlineConfig, Path2D, Subpath, outline

path = Path2D((Subpath((Line((0, 0), (100, 0)),)),))
profile = [(0.0, 2.0), (0.3, 4.0), (0.7, 16.0), (1.0, 6.0)]

result = outline(
    path,
    profile,
    config=OutlineConfig(max_width_error=0.05),
)
print("vertices:", len(result.contours[0]))
print("bounds:", result.bounds)
