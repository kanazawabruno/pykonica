# coding=utf-8

import logging
from typing import NamedTuple

from serial import PARITY_EVEN, SEVENBITS, SerialException
from konica.utils import cl200a_cmd_dict, cmd_formatter, write_serial_port, serial_port_luxmeter, connect_serial_port
from konica.exceptions import (
    CL200ACriticalError,
    LowBatteryError,
    LowLuminanceError,
    MeasurementValueOverError,
    ValueOutOfRangeError,
)


class EvXY(NamedTuple):
    ev: float
    x: float
    y: float


class XYZ(NamedTuple):
    x: float
    y: float
    z: float


class EvUV(NamedTuple):
    ev: float
    u_prime: float
    v_prime: float


class EvTcpDuv(NamedTuple):
    ev: float
    tcp: float
    delta_uv: float


class ChromaMeterKonica:
    """
    Konica Minolta CL-200A Chroma Meter.

    All documentation can be found:
    http://www.konicaminolta.com.cn/instruments/download/software/pdf/CL-200A_communication_specifications.pdf

    Communication spec: KMSE CS-A32T.0100
    Serial params: 9600 baud, 7-bit, even parity, 1 stop bit
    """

    def __init__(self, port: str | None = None) -> None:
        self.cmd_dict = cl200a_cmd_dict
        self.log = logging.getLogger(__name__)

        if port is not None:
            self.port = port
        else:
            self.port = serial_port_luxmeter()
        if self.port is None:
            self.log.error('No CL-200A device found. Check USB connection.')
            raise SerialException('No CL-200A device found. Check that the device is connected.')
        try:
            self.ser = connect_serial_port(self.port, parity=PARITY_EVEN, bytesize=SEVENBITS)
        except SerialException:
            self.log.exception('Could not connect to Lux Meter')
            raise
        try:
            self._connection()
            self._hold_mode()
            self._ext_mode()
        except SerialException:
            err = 'Lux meter not found. Check that the cable is properly connected.'
            self.log.exception(err)
            raise

    def _connection(self) -> None:
        """
        Switch the CL-200A to PC connection mode. (Command "54").
        In order to perform communication with a PC,
        this command must be used to set the CL-200A to PC connection mode.
        """
        cmd_request = cmd_formatter(self.cmd_dict['command_54'])
        cmd_response = cmd_formatter(self.cmd_dict['command_54r'])

        for i in range(2):
            write_serial_port(ser=self.ser, cmd=cmd_request, sleep_time=0.5)
            pc_connected_mode = self.ser.readline().decode('ascii')
            self.ser.reset_input_buffer()
            self.ser.reset_output_buffer()
            if cmd_response in pc_connected_mode:
                break
            elif i == 0:
                self.log.debug('PC connection mode: attempt one more time')
                continue
            else:
                self.log.error('Konica Minolta CL-200A has an error. Please verify USB cable.')

    def _hold_mode(self) -> None:
        """
        Sets the CL-200A to Hold status. (Command "55").
        """
        cmd = cmd_formatter(self.cmd_dict['command_55'])
        self.ser.reset_input_buffer()
        self.ser.reset_output_buffer()
        write_serial_port(ser=self.ser, cmd=cmd, sleep_time=0.5)

    def _ext_mode(self) -> None:
        """
        Set the CL-200A into EXT mode. (Command "40").
        EXT mode controls measurements from the PC.
        EXT mode cannot be set unless the CL-200A is in Hold status.
        """
        cmd = cmd_formatter(self.cmd_dict['command_40'])
        self.ser.reset_input_buffer()
        self.ser.reset_output_buffer()

        for i in range(2):
            write_serial_port(ser=self.ser, cmd=cmd, sleep_time=0.125)
            ext_mode_err = self.ser.readline().decode('ascii')
            if ext_mode_err[6:7] == '4':
                self._hold_mode()
                continue
            elif ext_mode_err[6:7] in ['1', '2', '3']:
                self.log.error('Set hold mode error')
                raise CL200ACriticalError('Switch off the CL-200A and then switch it back on')
            else:
                break

    @staticmethod
    def _check_status(result: str) -> None:
        """
        Check the ERR and battery bytes in the CL-200A response.

        ERR byte at index 6:
            '1','2','3' = Critical error, device restart needed
            '5' = Measurement value over range
            '6' = Low luminance, reduced chromaticity accuracy
            '7' = TCP/delta-uv values out of range
        Battery byte at index 8:
            '1' = Low battery
        """
        if result[6] in ['1', '2', '3']:
            raise CL200ACriticalError('Switch off the CL-200A and then switch it back on')
        if result[6] == '5':
            raise MeasurementValueOverError(
                'Measurement value over error. The measurement exceeds the CL-200A measurement range.'
            )
        if result[6] == '6':
            raise LowLuminanceError(
                'Low luminance error. Luminance is low, resulting in reduced '
                'calculation accuracy for determining chromaticity.'
            )
        if result[6] == '7':
            raise ValueOutOfRangeError('The TCP/delta-uv measured values are out of range.')
        if result[8] == '1':
            raise LowBatteryError(
                'Battery is low. The battery should be changed immediately or the AC adapter should be used.'
            )

    @staticmethod
    def _extract_value(result: str, start_index: int) -> float:
        """
        Extract one measurement value from the CL-200A response string.

        Data format: sign (1 char) + mantissa (4 digits) + exponent (1 digit)
        Value = sign * mantissa * 10^(exponent - 4)
        """
        sign = 1 if result[start_index] == '+' else -1
        mantissa = float(result[start_index + 1:start_index + 5])
        exponent = float(result[start_index + 5]) - 4
        return round(float(sign * mantissa * (10 ** exponent)), 3)

    @classmethod
    def _extract_three_values(cls, result: str) -> tuple:
        """
        Extract all three measurement values from a long-format CL-200A response.

        Values are at byte positions 9, 15, and 21.
        """
        v1 = cls._extract_value(result, start_index=9)
        v2 = cls._extract_value(result, start_index=15)
        v3 = cls._extract_value(result, start_index=21)
        return v1, v2, v3

    def _perform_measurement(self, read_cmd_key: str) -> str:
        """
        Trigger a measurement and read the result.

        Sends command_40r to trigger, then the specified read command.
        Returns the raw response string from the CL-200A.
        """
        self.ser.reset_input_buffer()
        self.ser.reset_output_buffer()

        cmd_ext = cmd_formatter(self.cmd_dict['command_40r'])
        cmd_read = cmd_formatter(self.cmd_dict[read_cmd_key])
        write_serial_port(self.ser, cmd=cmd_ext, sleep_time=0.5)
        write_serial_port(ser=self.ser, cmd=cmd_read, sleep_time=0)

        result = self.ser.readline().decode('ascii')
        if not result or len(result) < 22:
            raise CL200ACriticalError(
                'Invalid or incomplete response from CL-200A '
                '(expected at least 22 bytes, got {}): {!r}'.format(len(result), result)
            )
        self._check_status(result)
        return result

    def get_ev_x_y(self) -> EvXY:
        """
        Read measurement data as Ev, x, y. (Command "02").

        Returns:
            EvXY: Named tuple with ev (lux), x, y chromaticity coordinates.
        """
        result = self._perform_measurement('command_02')
        ev, x, y = self._extract_three_values(result)
        self.log.debug('Ev=%s, x=%s, y=%s', ev, x, y)
        return EvXY(ev=ev, x=x, y=y)

    def get_x_y_z(self) -> XYZ:
        """
        Read measurement data as X, Y, Z tristimulus values. (Command "01").

        Returns:
            XYZ: Named tuple with x, y, z values.
        """
        result = self._perform_measurement('command_01')
        x, y, z = self._extract_three_values(result)
        self.log.debug('X=%s, Y=%s, Z=%s', x, y, z)
        return XYZ(x=x, y=y, z=z)

    def get_ev_u_v(self) -> EvUV:
        """
        Read measurement data as Ev, u', v'. (Command "03").

        Returns:
            EvUV: Named tuple with ev, u_prime, v_prime values.
        """
        result = self._perform_measurement('command_03')
        ev, u, v = self._extract_three_values(result)
        self.log.debug('Ev=%s, u\'=%s, v\'=%s', ev, u, v)
        return EvUV(ev=ev, u_prime=u, v_prime=v)

    def get_ev_tcp_delta_uv(self) -> EvTcpDuv:
        """
        Read measurement data as Ev, TCP, delta-uv. (Command "08").

        Returns:
            EvTcpDuv: Named tuple with ev, tcp (correlated color temperature), delta_uv.
        """
        result = self._perform_measurement('command_08')
        ev, tcp, delta_uv = self._extract_three_values(result)
        self.log.debug('Ev=%s, TCP=%s, delta_uv=%s', ev, tcp, delta_uv)
        return EvTcpDuv(ev=ev, tcp=tcp, delta_uv=delta_uv)

    def get_lux(self) -> str:
        """
        Perform lux level measurement. (Backward-compatible).

        Returns:
            str: Lux (Ev) value as string, rounded to 3 decimal places.
        """
        result = self.get_ev_x_y()
        return str(result.ev)

    def close(self) -> None:
        """Close the serial connection."""
        if hasattr(self, 'ser') and self.ser and self.ser.is_open:
            self.ser.close()

    def __enter__(self) -> 'ChromaMeterKonica':
        return self

    def __exit__(self, *args: object) -> None:
        self.close()
