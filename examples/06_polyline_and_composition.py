from strokeoutline import combine_outlines, outline, path_from_polyline


def main():
    first = outline(path_from_polyline([(0, 0), (10, 0)]), 2.0)
    second = outline(path_from_polyline([(20, 0), (30, 0)]), 4.0)
    combined = combine_outlines((first, second))

    assert combined.contours == first.contours + second.contours
    assert combined.bounds is not None
    assert combined.bounds[0] == min(first.bounds[0], second.bounds[0])
    assert combined.bounds[2] == max(first.bounds[2], second.bounds[2])
    print("contours:", len(combined.contours))
    print("bounds:", combined.bounds)


if __name__ == "__main__":
    main()
