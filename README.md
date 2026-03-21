# pykonica

Python package to control Konica Minolta CL-200A Chroma Meter devices via serial communication (RS-232 / USB).

## Features

- Read illuminance and chromaticity in multiple color spaces
- Four measurement modes: Ev/x/y, X/Y/Z, Ev/u'/v', Ev/TCP/delta-uv
- Automatic device discovery (FTDI-based USB connection)
- Custom exception hierarchy for all CL-200A error codes
- Context manager support for safe resource handling
- CLI tool for quick measurements
- Based on Konica Minolta communication spec KMSE CS-A32T.0100

## Requirements

- Python 3.10 or later
- Konica Minolta CL-200A connected via USB (FTDI cable T-A15) or RS-232 (cable T-A11)

## Installation

```bash
pip install konica
```

Or install from source:

```bash
git clone https://github.com/kanazawabruno/pykonica.git
cd pykonica
pip install -e .
```

## Usage

### Python API

```python
from konica import ChromaMeterKonica

# Using context manager (recommended)
with ChromaMeterKonica() as meter:
    # Illuminance and chromaticity (Ev, x, y)
    result = meter.get_ev_x_y()
    print(f"Ev={result.ev} lux, x={result.x}, y={result.y}")

    # Tristimulus values (X, Y, Z)
    xyz = meter.get_x_y_z()
    print(f"X={xyz.x}, Y={xyz.y}, Z={xyz.z}")

    # CIE 1976 chromaticity (Ev, u', v')
    uv = meter.get_ev_u_v()
    print(f"Ev={uv.ev}, u'={uv.u_prime}, v'={uv.v_prime}")

    # Correlated color temperature (Ev, TCP, delta-uv)
    cct = meter.get_ev_tcp_delta_uv()
    print(f"Ev={cct.ev}, TCP={cct.tcp}K, delta_uv={cct.delta_uv}")

    # Backward-compatible lux reading (returns string)
    lux = meter.get_lux()
    print(f"{lux} lux")
```

### Error Handling

```python
from konica import ChromaMeterKonica, CL200AError, LowLuminanceError

with ChromaMeterKonica() as meter:
    try:
        result = meter.get_ev_x_y()
    except LowLuminanceError:
        print("Luminance too low for accurate chromaticity")
    except CL200AError as e:
        print(f"Device error: {e}")
```

Exception hierarchy:
- `CL200AError` -- base exception
  - `CL200ACriticalError` -- ERR codes 1-3, device restart needed
  - `MeasurementValueOverError` -- ERR code 5, exceeds measurement range
  - `LowLuminanceError` -- ERR code 6, reduced chromaticity accuracy
  - `ValueOutOfRangeError` -- ERR code 7, TCP/delta-uv out of range
  - `LowBatteryError` -- battery low

### CLI

```bash
# Read lux value
konica_cli --lux

# Read Ev, x, y
konica_cli --mode ev_xy

# Read X, Y, Z tristimulus values
konica_cli --mode xyz

# Read Ev, u', v'
konica_cli --mode ev_uv

# Read Ev, TCP, delta-uv
konica_cli --mode ev_tcp_duv

# Enable debug output
konica_cli --mode ev_xy -V

# Show version
konica_cli -v
```

## Supported Measurement Modes

| Method | Command | Returns | Description |
|--------|---------|---------|-------------|
| `get_ev_x_y()` | 02 | `EvXY(ev, x, y)` | Illuminance + CIE 1931 chromaticity |
| `get_x_y_z()` | 01 | `XYZ(x, y, z)` | CIE 1931 tristimulus values |
| `get_ev_u_v()` | 03 | `EvUV(ev, u_prime, v_prime)` | Illuminance + CIE 1976 chromaticity |
| `get_ev_tcp_delta_uv()` | 08 | `EvTcpDuv(ev, tcp, delta_uv)` | Illuminance + correlated color temp |
| `get_lux()` | 02 | `str` | Backward-compatible lux reading |

## Supported Python Versions

- Python 3.10, 3.11, 3.12, 3.13, 3.14

## Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
python -m unittest discover tests/

# Run tests with pytest
pytest tests/
```

## License

MIT
