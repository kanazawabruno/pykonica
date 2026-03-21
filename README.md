# pykonica

Python package to control Konica Minolta measurement devices via serial communication (RS-232 / USB).

## Supported Devices

- **CL-200A** Chroma Meter -- illuminance and chromaticity measurement
- **CA-410** Display Color Analyzer -- luminance, chromaticity, and flicker measurement for displays (also compatible with CA-210/CA-310)

## Features

- Read illuminance/luminance and chromaticity in multiple color spaces
- Multiple measurement modes per device (see tables below)
- Automatic device discovery (FTDI-based USB / virtual COM port)
- Custom exception hierarchy for device-specific error codes
- Context manager support for safe resource handling
- CLI tool with device selection for quick measurements

## Requirements

- Python 3.10 or later
- Konica Minolta CL-200A or CA-410 connected via USB or RS-232

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

### CL-200A Chroma Meter

```python
from konica import ChromaMeterKonica

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
```

### CA-410 Display Color Analyzer

```python
from konica import ColorAnalyzerCA410

with ColorAnalyzerCA410() as analyzer:
    # Luminance and chromaticity (Lv, x, y)
    result = analyzer.get_lv_x_y()
    print(f"Lv={result.lv} cd/m², x={result.x}, y={result.y}")

    # Tristimulus values (X, Y, Z)
    xyz = analyzer.get_x_y_z()
    print(f"X={xyz.x}, Y={xyz.y}, Z={xyz.z}")

    # CIE 1976 chromaticity (Lv, u', v')
    uv = analyzer.get_lv_u_v()
    print(f"Lv={uv.lv}, u'={uv.u_prime}, v'={uv.v_prime}")

    # Correlated color temperature (Lv, TCP, delta-uv)
    cct = analyzer.get_lv_tcp_duv()
    print(f"Lv={cct.lv}, TCP={cct.tcp}K, delta_uv={cct.delta_uv}")

    # Flicker measurement
    flicker = analyzer.get_flicker(mode='jis')
    print(f"Flicker (JIS): {flicker}%")

    # Specify port and baud rate explicitly
    # analyzer = ColorAnalyzerCA410(port='/dev/ttyUSB0', baudrate=38400)
```

### Error Handling

```python
# CL-200A errors
from konica import ChromaMeterKonica, CL200AError, LowLuminanceError

with ChromaMeterKonica() as meter:
    try:
        result = meter.get_ev_x_y()
    except LowLuminanceError:
        print("Luminance too low for accurate chromaticity")
    except CL200AError as e:
        print(f"Device error: {e}")

# CA-410 errors
from konica import ColorAnalyzerCA410, CA410Error, CA410MeasurementError

with ColorAnalyzerCA410() as analyzer:
    try:
        result = analyzer.get_lv_x_y()
    except CA410MeasurementError as e:
        print(f"Measurement error ({e.error_code}): {e}")
    except CA410Error as e:
        print(f"Device error: {e}")
```

CL-200A exception hierarchy:
- `CL200AError` -- base exception
  - `CL200ACriticalError` -- ERR codes 1-3, device restart needed
  - `MeasurementValueOverError` -- ERR code 5, exceeds measurement range
  - `LowLuminanceError` -- ERR code 6, reduced chromaticity accuracy
  - `ValueOutOfRangeError` -- ERR code 7, TCP/delta-uv out of range
  - `LowBatteryError` -- battery low

CA-410 exception hierarchy:
- `CA410Error` -- base exception (includes error code mapping)
  - `CA410CommandError` -- command/syntax errors (ER00, ER10, ER11, ER13)
  - `CA410MeasurementError` -- measurement errors (ER02, ER05)
  - `CA410CalibrationError` -- calibration/hardware errors (ER19, ER30, ER52)

### CLI

```bash
# CL-200A (default device)
konica_cli --lux
konica_cli --mode ev_xy
konica_cli --mode xyz
konica_cli --mode ev_uv
konica_cli --mode ev_tcp_duv

# CA-410
konica_cli -d ca410 --lux
konica_cli -d ca410 --mode lv_xy
konica_cli -d ca410 --mode xyz
konica_cli -d ca410 --mode lv_uv
konica_cli -d ca410 --mode lv_tcp_duv
konica_cli -d ca410 --flicker jis
konica_cli -d ca410 --flicker vesa

# Specify serial port
konica_cli -d ca410 -p /dev/ttyUSB0 --mode lv_xy

# Debug output / version
konica_cli -V --mode ev_xy
konica_cli -v
```

## Supported Measurement Modes

### CL-200A

| Method | Command | Returns | Description |
|--------|---------|---------|-------------|
| `get_ev_x_y()` | 02 | `EvXY(ev, x, y)` | Illuminance + CIE 1931 chromaticity |
| `get_x_y_z()` | 01 | `XYZ(x, y, z)` | CIE 1931 tristimulus values |
| `get_ev_u_v()` | 03 | `EvUV(ev, u_prime, v_prime)` | Illuminance + CIE 1976 chromaticity |
| `get_ev_tcp_delta_uv()` | 08 | `EvTcpDuv(ev, tcp, delta_uv)` | Illuminance + correlated color temp |
| `get_lux()` | 02 | `str` | Backward-compatible lux reading |

### CA-410

| Method | Command | Returns | Description |
|--------|---------|---------|-------------|
| `get_lv_x_y()` | MES (MDS=0) | `LvXY(lv, x, y)` | Luminance + CIE 1931 chromaticity |
| `get_x_y_z()` | MES (MDS=3) | `XYZ(x, y, z)` | CIE 1931 tristimulus values |
| `get_lv_u_v()` | MES (MDS=1) | `LvUV(lv, u_prime, v_prime)` | Luminance + CIE 1976 chromaticity |
| `get_lv_tcp_duv()` | MES (MDS=2) | `LvTcpDuv(lv, tcp, delta_uv)` | Luminance + correlated color temp |
| `get_luminance()` | MES (MDS=0) | `float` | Luminance (Lv) in cd/m² |
| `get_flicker()` | MES (MDS=6/7) | `float` | Flicker percentage (JIS or VESA) |

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
