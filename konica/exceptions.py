# coding=utf-8


class CL200AError(Exception):
    """Base exception for CL-200A errors."""
    pass


class CL200ACriticalError(CL200AError):
    """ERR codes 1, 2, 3: Device needs power cycle."""
    pass


class MeasurementValueOverError(CL200AError):
    """ERR code 5: Measurement exceeds device range."""
    pass


class LowLuminanceError(CL200AError):
    """ERR code 6: Low luminance, reduced chromaticity accuracy."""
    pass


class ValueOutOfRangeError(CL200AError):
    """ERR code 7: TCP/delta-uv values out of range."""
    pass


class LowBatteryError(CL200AError):
    """Battery byte is '1': battery low."""
    pass
