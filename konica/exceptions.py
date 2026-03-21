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


class CA410Error(Exception):
    """Base exception for CA-410 errors."""

    # Error code mapping from CA-410 Communication Specifications
    ERROR_CODES = {
        'ER00': 'Command error or communication error',
        'ER02': 'Forced termination of measurement due to conditions not being met',
        'ER05': 'Measurement value over the displayable range',
        'ER10': 'Undefined command',
        'ER11': 'Unacceptable command in current state',
        'ER13': 'Invalid data or parameter',
        'ER17': 'Insufficient number of probes',
        'ER19': 'No valid calibration data',
        'ER20': 'Memory data access error',
        'ER30': 'Zero calibration error',
        'ER52': 'EEPROM access error',
        'ER80': 'USB communication error',
    }

    def __init__(self, error_code: str, message: str = '') -> None:
        self.error_code = error_code
        if not message:
            message = self.ERROR_CODES.get(error_code, 'Unknown error: {}'.format(error_code))
        super().__init__(message)


class CA410CommandError(CA410Error):
    """Command syntax or communication error (ER00, ER10, ER11, ER13)."""
    pass


class CA410MeasurementError(CA410Error):
    """Measurement-related error (ER02, ER05)."""
    pass


class CA410CalibrationError(CA410Error):
    """Calibration or hardware error (ER19, ER30, ER52)."""
    pass
