# CLAUDE.md

## Project Overview

**pykonica** is a Python package for controlling Konica Minolta measurement devices via serial communication. It supports the CL-200A Chroma Meter and CA-410 Display Color Analyzer (also compatible with CA-210/CA-310).

- **License**: MIT
- **Python**: >=3.10
- **Package name**: `konica`
- **Version**: 2.0.0 (defined in `konica/version.py`)
- **CL-200A spec**: KMSE CS-A32T.0100
- **CA-410 spec**: CA-410 Communication Specifications v1.08

## Repository Structure

```
konica/                  # Main package
├── cl200a.py            # ChromaMeterKonica class - CL-200A device interface
├── ca410.py             # ColorAnalyzerCA410 class - CA-410 device interface
├── exceptions.py        # Custom exception hierarchies (CL200AError, CA410Error)
├── utils.py             # Serial port utilities, command formatting, checksums
├── konica_cli.py        # CLI entry point (argparse) with device selection
├── logger.py            # Logging configuration
└── version.py           # Version string
tests/                   # Unit tests (unittest)
├── context.py           # Import path setup
├── test_basic.py        # CL-200A tests (27 tests)
└── test_ca410.py        # CA-410 tests (19 tests)
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
- **Type hints**: on all public and private methods
- **Return types**: NamedTuples (`EvXY`, `XYZ`, `EvUV`, `EvTcpDuv`, `LvXY`, `LvUV`, `LvTcpDuv`)
- **Exceptions**: Custom hierarchies rooted at `CL200AError` and `CA410Error` in `exceptions.py`
- **Docstrings**: present on public classes and methods
- **Logging**: use `logging.getLogger(__name__)` pattern

## Dependencies

- **Runtime**: `pyserial` (serial port communication)
- **Dev/Test**: `pytest`, `sphinx`

## Key Architecture

### CL-200A (cl200a.py)
- `ChromaMeterKonica` is the CL-200A interface class. Supports context manager protocol.
- Measurement methods: `get_ev_x_y()`, `get_x_y_z()`, `get_ev_u_v()`, `get_ev_tcp_delta_uv()`, `get_lux()`
- Serial protocol: 9600 baud, even parity, 7 data bits, 1 stop bit
- Frame format: `[STX] + payload + [ETX] + BCC (2-digit hex XOR) + CR+LF`

### CA-410 (ca410.py)
- `ColorAnalyzerCA410` is the CA-410 interface class. Supports context manager protocol.
- Measurement methods: `get_lv_x_y()`, `get_x_y_z()`, `get_lv_u_v()`, `get_lv_tcp_duv()`, `get_luminance()`, `get_flicker()`
- Serial protocol: 38400 baud (default), even parity, 7 data bits, 2 stop bits
- Command format: ASCII text commands with CR delimiter, `OK00` success / `ERxx` error responses
- Compatible with CA-210/CA-310 command set

### Shared
- `exceptions.py` defines error types for both devices
- `utils.py` contains CL-200A command dictionary, serial port helpers, XOR checksum (BCC), FTDI auto-detection
- CLI entry point: `konica_cli` console script with `--device` flag for device selection
