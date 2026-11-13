from strokeoutline.svg import outline_svg_path

# FontTools' SVG parser handles ordinary SVG path syntax; the adapter turns it
# into strokeoutline's neutral path model before expansion.
d = "M 0 0 C 0 60 60 60 60 0 M 80 0 Q 100 40 120 0"
result = outline_svg_path(d, width=5.0)
print("contours:", len(result.contours))
print("bounds:", result.bounds)
