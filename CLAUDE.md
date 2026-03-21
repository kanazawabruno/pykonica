# CLAUDE.md

## Project Overview

**pykonica** is a Python package for controlling Konica Minolta CL-200A Chroma Meter devices via RS-232 serial communication. It provides a programmatic interface and CLI for reading luminance/chromaticity measurements.

- **License**: MIT
- **Python**: >=3.10
- **Package name**: `konica`
- **Version**: 2.0.0 (defined in `konica/version.py`)
- **Communication spec**: KMSE CS-A32T.0100

## Repository Structure

```
konica/                  # Main package
├── cl200a.py            # ChromaMeterKonica class - device interface, NamedTuple result types
├── exceptions.py        # Custom exception hierarchy (CL200AError base)
├── utils.py             # Serial port utilities, command formatting, checksums
├── konica_cli.py        # CLI entry point (argparse)
├── logger.py            # Logging configuration
└── version.py           # Version string
tests/                   # Unit tests (unittest)
├── context.py           # Import path setup
└── test_basic.py        # Tests for parsing, formatting, error handling (27 tests)
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
- CI runs tests across Python 3.10, 3.11, 3.12, 3.13, 3.14
- Tests focus on parsing, formatting, and error handling; hardware access may be required for full end-to-end verification

## CI/CD

GitHub Actions workflow at `.github/workflows/python-tests.yml`:
- Triggers on push/PR to `master`/`main`
- Matrix: Python 3.10–3.14
- Steps: checkout, setup Python, install deps, run tests

## Code Conventions

- **Style**: `snake_case` for functions/variables, `PascalCase` for classes
- **Encoding**: UTF-8 declaration at file top (`# coding=utf-8`)
- **Private methods**: single underscore prefix (`_connection()`)
- **Type hints**: on all public and private methods in `cl200a.py`
- **Return types**: NamedTuples (`EvXY`, `XYZ`, `EvUV`, `EvTcpDuv`)
- **Exceptions**: Custom hierarchy rooted at `CL200AError` in `exceptions.py`
- **Docstrings**: present on public classes and methods
- **Logging**: use `logging.getLogger(__name__)` pattern

## Dependencies

- **Runtime**: `pyserial` (serial port communication)
- **Dev/Test**: `pytest`, `sphinx`

## Key Architecture

- `ChromaMeterKonica` (in `cl200a.py`) is the main interface class. Supports context manager protocol (`with` statement).
- Measurement methods: `get_ev_x_y()`, `get_x_y_z()`, `get_ev_u_v()`, `get_ev_tcp_delta_uv()`, `get_lux()` (backward compat)
- `exceptions.py` defines error types for each CL-200A ERR code (1-3: critical, 5: over range, 6: low luminance, 7: out of range) and battery status
- `utils.py` contains the command dictionary, serial port helpers, XOR checksum (BCC) calculation, and FTDI device auto-detection
- Serial protocol: 9600 baud, even parity, 7 data bits, 1 stop bit (per KMSE CS-A32T.0100)
- Frame format: `[STX] + payload + [ETX] + BCC (2-digit XOR) + CR+LF`
- CLI entry point: `konica_cli` console script mapped to `konica.konica_cli:main`
