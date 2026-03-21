# coding=utf-8

"""
Konica Minolta CA-410 Display Color Analyzer interface.

Communication is ASCII text-based over RS-232C or USB (virtual COM port).
Commands are terminated with CR. Responses start with OK00 (success) or ERxx (error).
Default serial params: 38400 baud, 7-bit, even parity, 2 stop bits.

Compatible with CA-210/CA-310 command set.
"""

import logging
from time import sleep
from typing import NamedTuple, Optional

from serial import Serial, PARITY_EVEN, SEVENBITS, STOPBITS_TWO, SerialException
from serial.tools import list_ports

from konica.exceptions import (
    CA410Error,
    CA410CommandError,
    CA410MeasurementError,
    CA410CalibrationError,
)


class LvXY(NamedTuple):
    lv: float
    x: float
    y: float


class LvUV(NamedTuple):
    lv: float
    u_prime: float
    v_prime: float


class LvTcpDuv(NamedTuple):
    lv: float
    tcp: float
    delta_uv: float


# Display mode codes for the MDS command
DISPLAY_MODES = {
    'lv_xy': 0,
    'lv_uv': 1,
    'lv_tcp_duv': 2,
    'xyz': 3,
    'flicker_jis': 6,
    'flicker_vesa': 7,
    'lv_dominant_wavelength': 8,
}


class ColorAnalyzerCA410:
    """
    Konica Minolta CA-410 Display Color Analyzer.

    Provides measurement of luminance (Lv), chromaticity (xy, u'v'),
    correlated color temperature (TCP), tristimulus values (XYZ),
    and flicker for display testing.

    Compatible with CA-210 and CA-310 command sets.

    Serial params: 38400 baud (default), 7-bit, even parity, 2 stop bits.
    """

    def __init__(self, port: Optional[str] = None, baudrate: int = 38400,
                 timeout: float = 5.0, probe: int = 0) -> None:
        """
        Initialize connection to the CA-410.

        Args:
            port: Serial port (e.g. 'COM3', '/dev/ttyUSB0'). Auto-detected if None.
            baudrate: Baud rate (default 38400, the factory setting).
            timeout: Serial read timeout in seconds.
            probe: Probe number to select (0-based). Default is 0 (first probe).
        """
        self.log = logging.getLogger(__name__)
        self.probe = probe

        if port is None:
            port = self._find_device()
        if port is None:
            raise SerialException('No CA-410 device found. Check that the device is connected.')

        try:
            self.ser = Serial(
                port=port,
                baudrate=baudrate,
                bytesize=SEVENBITS,
                parity=PARITY_EVEN,
                stopbits=STOPBITS_TWO,
                timeout=timeout,
            )
        except SerialException:
            self.log.exception('Could not connect to CA-410 on port %s', port)
            raise

        self._setup_remote()

    @staticmethod
    def _find_device() -> Optional[str]:
        """Auto-detect a CA-410/CA-310 device by scanning USB serial ports."""
        for p in list_ports.comports():
            desc = (p.description or '').lower()
            manufacturer = (p.manufacturer or '').lower()
            if 'konica' in manufacturer or 'konica' in desc or 'ca-410' in desc or 'ca-310' in desc:
                return p.device
        # Fall back to any FTDI device
        for p in list_ports.comports():
            if p.manufacturer and 'FTDI' in p.manufacturer:
                return p.device
        return None

    def _send_command(self, command: str) -> str:
        """
        Send a command to the CA-410 and return the response.

        Args:
            command: ASCII command string (without CR terminator).

        Returns:
            Response string (without CR terminator).

        Raises:
            CA410Error: If the response indicates an error.
        """
        self.ser.reset_input_buffer()
        self.ser.write((command + '\r').encode('ascii'))
        self.log.debug('Sent: %s', command)

        response = self.ser.read_until(b'\r').decode('ascii').strip()
        self.log.debug('Received: %s', response)

        if not response:
            raise CA410Error('ER00', 'No response from CA-410 (timeout)')

        if response.startswith('ER'):
            error_code = response[:4]
            self._raise_error(error_code)

        return response

    @staticmethod
    def _raise_error(error_code: str) -> None:
        """Raise the appropriate CA410 exception for the given error code."""
        if error_code in ('ER10', 'ER11', 'ER13', 'ER00'):
            raise CA410CommandError(error_code)
        elif error_code in ('ER02', 'ER05'):
            raise CA410MeasurementError(error_code)
        elif error_code in ('ER19', 'ER30', 'ER52'):
            raise CA410CalibrationError(error_code)
        else:
            raise CA410Error(error_code)

    def _setup_remote(self) -> None:
        """Set the CA-410 into remote mode for PC control."""
        try:
            self._send_command('COM,1')
        except CA410Error:
            self.log.warning('COM,1 command failed; device may already be in remote mode')

    def set_display_mode(self, mode: str) -> None:
        """
        Set the measurement display mode.

        Args:
            mode: One of 'lv_xy', 'lv_uv', 'lv_tcp_duv', 'xyz',
                  'flicker_jis', 'flicker_vesa', 'lv_dominant_wavelength'.
        """
        if mode not in DISPLAY_MODES:
            raise ValueError('Unknown display mode: {}. Choose from: {}'.format(
                mode, ', '.join(DISPLAY_MODES.keys())))
        self._send_command('MDS,{}'.format(DISPLAY_MODES[mode]))

    def zero_calibration(self) -> None:
        """Perform zero calibration (close the probe cap first)."""
        self._send_command('ZRC')

    def _parse_measurement(self, response: str) -> list:
        """Parse comma-separated values from an OK00 response."""
        if not response.startswith('OK00'):
            raise CA410Error('ER00', 'Unexpected response format: {}'.format(response))
        parts = response.split(',')
        # Skip the 'OK00' prefix and the probe/channel info
        return parts

    def measure(self) -> str:
        """
        Trigger a measurement and return the raw response.

        Returns:
            Raw response string from the CA-410.
        """
        return self._send_command('MES')

    def get_lv_x_y(self) -> LvXY:
        """
        Read measurement data as Lv, x, y.

        Returns:
            LvXY: Named tuple with lv (luminance), x, y chromaticity coordinates.
        """
        self.set_display_mode('lv_xy')
        response = self.measure()
        parts = self._parse_measurement(response)
        # Response format: OK00,P<n>,<Lv>,<x>,<y>
        lv = float(parts[2])
        x = float(parts[3])
        y = float(parts[4])
        self.log.debug('Lv=%s, x=%s, y=%s', lv, x, y)
        return LvXY(lv=lv, x=x, y=y)

    def get_x_y_z(self) -> 'XYZ':
        """
        Read measurement data as X, Y, Z tristimulus values.

        Returns:
            XYZ: Named tuple with x, y, z values (from cl200a module).
        """
        from konica.cl200a import XYZ
        self.set_display_mode('xyz')
        response = self.measure()
        parts = self._parse_measurement(response)
        # Response format: OK00,P<n>,<X>,<Y>,<Z>
        x = float(parts[2])
        y = float(parts[3])
        z = float(parts[4])
        self.log.debug('X=%s, Y=%s, Z=%s', x, y, z)
        return XYZ(x=x, y=y, z=z)

    def get_lv_u_v(self) -> LvUV:
        """
        Read measurement data as Lv, u', v'.

        Returns:
            LvUV: Named tuple with lv, u_prime, v_prime values.
        """
        self.set_display_mode('lv_uv')
        response = self.measure()
        parts = self._parse_measurement(response)
        # Response format: OK00,P<n>,<Lv>,<u'>,<v'>
        lv = float(parts[2])
        u = float(parts[3])
        v = float(parts[4])
        self.log.debug("Lv=%s, u'=%s, v'=%s", lv, u, v)
        return LvUV(lv=lv, u_prime=u, v_prime=v)

    def get_lv_tcp_duv(self) -> LvTcpDuv:
        """
        Read measurement data as Lv, TCP, delta-uv.

        Returns:
            LvTcpDuv: Named tuple with lv, tcp (correlated color temperature), delta_uv.
        """
        self.set_display_mode('lv_tcp_duv')
        response = self.measure()
        parts = self._parse_measurement(response)
        # Response format: OK00,P<n>,<Lv>,<TCP>,<duv>
        lv = float(parts[2])
        tcp = float(parts[3])
        delta_uv = float(parts[4])
        self.log.debug('Lv=%s, TCP=%s, delta_uv=%s', lv, tcp, delta_uv)
        return LvTcpDuv(lv=lv, tcp=tcp, delta_uv=delta_uv)

    def get_luminance(self) -> float:
        """
        Read luminance (Lv) value.

        Returns:
            float: Luminance in cd/m².
        """
        result = self.get_lv_x_y()
        return result.lv

    def get_flicker(self, mode: str = 'jis') -> float:
        """
        Read flicker measurement.

        Args:
            mode: 'jis' for JIS flicker or 'vesa' for VESA flicker.

        Returns:
            float: Flicker percentage.
        """
        if mode == 'jis':
            self.set_display_mode('flicker_jis')
        elif mode == 'vesa':
            self.set_display_mode('flicker_vesa')
        else:
            raise ValueError("Flicker mode must be 'jis' or 'vesa'")
        response = self.measure()
        parts = self._parse_measurement(response)
        flicker = float(parts[2])
        self.log.debug('Flicker (%s)=%s%%', mode, flicker)
        return flicker

    def close(self) -> None:
        """Close the serial connection and exit remote mode."""
        try:
            self._send_command('COM,0')
        except (CA410Error, SerialException):
            pass
        if hasattr(self, 'ser') and self.ser and self.ser.is_open:
            self.ser.close()

    def __enter__(self) -> 'ColorAnalyzerCA410':
        return self

    def __exit__(self, *args: object) -> None:
        self.close()
