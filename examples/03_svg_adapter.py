import math

from strokeoutline.svg import outline_svg_path


def main():
    path_data = "M 0 0 C 0 60 60 60 60 0 M 80 0 Q 100 40 120 0"
    result = outline_svg_path(path_data, width=5.0)

    assert len(result.contours) == 2
    assert result.bounds is not None
    assert all(math.isfinite(value) for value in result.bounds)
    print("contours:", len(result.contours))
    print("bounds:", result.bounds)


if __name__ == "__main__":
    main()
