# strokeoutline

`strokeoutline` converts 2D centerlines into deterministic filled contours with constant or variable width. It is reusable geometry extracted from InkGrammar's stroke outlining engine, without glyph, shaping, OCR, or handwriting-model responsibilities.

Use it for vector brushes, pressure-like width profiles, centerline fonts, skeleton thickening, corridors, and other centerline-based applications. The MVP preserves current geometry behavior; see the documentation for its limitations and compatibility contracts.

## Install

```bash
python -m pip install strokeoutline
```

For SVG path parsing, install the optional extra:

```bash
python -m pip install 'strokeoutline[svg]'
```

## Documentation

The complete guides and deliberate API reference are in the [documentation source](docs/index.md):

- [Getting started](docs/getting-started.md)
- [Examples](docs/examples.md)
- [API reference](docs/api/index.md)
- [Limitations](docs/limitations.md)

## Core example

```python
from strokeoutline import Line, Path2D, Subpath, outline

path = Path2D((Subpath((Line((0, 0), (10, 0)),)),))

result = outline(path, width=4.0)
print(result.bounds)
for contour in result.contours:
    print(contour)
```

Width is the full stroke diameter, not radius. Width profiles may be a positive constant, a strictly increasing piecewise-linear knot sequence spanning `0..1`, or a callable.

For compatibility, normalized width progress is based on segment index, not physical arc length:

```text
u = (segment_index + local_segment_parameter) / segment_count
```

Progress restarts at zero for each independent subpath. See [width profiles](docs/width-profiles.md) for details.

## Integration boundary

StrokeOutline owns centerline-to-contour geometry. Integrations such as InkGrammar own shaped-text traversal and domain-specific adaptation, and should call StrokeOutline rather than copy its outlining algorithm. The core package does not require FontTools; only the optional `strokeoutline.svg` adapter does.

## Development

```bash
python -m pip install -e '.[dev]'
ruff format --check .
ruff check .
pytest
python docs/make.py html
python docs/make.py doctest
```

## License

Apache-2.0.
