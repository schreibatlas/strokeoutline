# Development

## Environment

From a checkout, install package development dependencies and Sphinx requirements:

```bash
python -m pip install -e '.[dev]'
python -m pip install -r docs/requirements.txt
```

The documentation requirements include FontTools so autodoc can import the optional SVG adapter. This does not make FontTools a core runtime dependency.

## Tests and lint

```bash
ruff format --check .
ruff check .
pytest
```

## Documentation

```bash
python docs/make.py html
python docs/make.py doctest
```

The build helper invokes Sphinx with `-W --keep-going`. Warnings fail the build and should be fixed, not broadly suppressed.

Other useful targets include:

```bash
python docs/make.py clean
python docs/make.py dirhtml
python docs/make.py linkcheck
python docs/make.py help
```

`linkcheck` is useful as a manual or release check. It is not an ordinary CI gate because external network reliability can make it flaky.
