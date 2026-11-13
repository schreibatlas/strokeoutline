# SVG adapter API

> This module requires the optional `svg` extra and FontTools. Install it with `python -m pip install 'strokeoutline[svg]'`.

The adapter returns StrokeOutline's neutral path model and outline result. It does not implement complete SVG/CSS stroke rendering.

```{autofunction} strokeoutline.svg.path_from_svg

```

```{autofunction} strokeoutline.svg.outline_svg_path

```

`expand_path` is a compatibility alias of `outline_svg_path`:

```{autofunction} strokeoutline.svg.expand_path

```
