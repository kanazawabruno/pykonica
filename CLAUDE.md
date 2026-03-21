# CLAUDE.md

## Project Overview

**pykonica** is a Python package for controlling Konica Minolta CL-200A Chroma Meter devices via RS-232 serial communication. It provides a programmatic interface and CLI for reading luminance/chromaticity measurements.

- **License**: MIT
- **Python**: >=3.8
- **Package name**: `konica`
- **Version**: 1.0.0 (defined in `konica/version.py`)

## Repository Structure

```
konica/                  # Main package
├── cl200a.py            # ChromaMeterKonica class - device interface
├── utils.py             # Serial port utilities, command formatting, checksums
├── konica_cli.py        # CLI entry point (argparse)
├── logger.py            # Logging configuration
└── version.py           # Version string
tests/                   # Unit tests (unittest)
├── context.py           # Import path setup
└── test_basic.py        # Basic test suite
docs/                    # Sphinx documentation (minimal)
setup.py                 # Package config, metadata, entry points
```

## Development Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
python -m unittest discover tests/

# Install package in dev mode
pip install -e .
```

## Testing

- Framework: `unittest` (standard library)
- Test discovery: `python -m unittest discover tests/`
- Tests live in `tests/` directory
- CI runs tests across Python 3.8, 3.9, 3.10, 3.11, 3.12

## CI/CD

GitHub Actions workflow at `.github/workflows/python-tests.yml`:
- Triggers on push/PR to `master`/`main`
- Matrix: Python 3.8–3.12
- Steps: checkout, setup Python, install deps, run tests

## Code Conventions

- **Style**: `snake_case` for functions/variables, `PascalCase` for classes
- **Encoding**: UTF-8 declaration at file top (`# coding=utf-8`)
- **Private methods**: double underscore prefix (`__connection()`)
- **Docstrings**: present on public classes and methods
- **Logging**: use the logger from `konica/logger.py`

## Dependencies

- **Runtime**: `pyserial` (serial port communication)
- **Dev/Test**: `nose`, `sphinx`

## Key Architecture

- `ChromaMeterKonica` (in `cl200a.py`) is the main interface class. It handles device discovery, connection, and measurement reading.
- `utils.py` contains the command dictionary, serial port helpers, XOR checksum calculation, and FTDI device auto-detection.
- Serial protocol: 9600 baud, even parity, 7 data bits, 2 stop bits.
- CLI entry point: `konica_cli` console script mapped to `konica.konica_cli:main`.
