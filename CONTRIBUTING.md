# Contributing to gformlib

Thank you for considering contributing!

## Development setup

```bash
git clone https://github.com/andhit-r/gformlib.git
cd gformlib
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

## Running the tests

```bash
pytest                          # single environment
tox                             # full matrix (Python 3.9–3.12 + lint + type-check)
```

## Code style

The project uses **Black** for formatting and **isort** for import ordering.
Run the linter with:

```bash
black src tests
isort src tests
flake8 src tests
```

Or via tox:

```bash
tox -e lint
```

## Submitting a pull request

1. Fork the repository and create a feature branch.
2. Add tests for any new functionality.
3. Ensure `tox` passes without errors.
4. Open a pull request against the `main` branch with a clear description.

## Reporting bugs

Please open an issue at https://github.com/andhit-r/gformlib/issues and include:

- Python version
- Library version (`pip show gformlib`)
- Minimal reproduction case
- Full traceback
