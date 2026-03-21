# -*- coding: utf-8 -*-

import unittest

from konica.utils import cmd_formatter, cl200a_cmd_dict
from konica.cl200a import ChromaMeterKonica, EvXY, XYZ, EvUV, EvTcpDuv
from konica.exceptions import (
    CL200ACriticalError,
    LowBatteryError,
    LowLuminanceError,
    MeasurementValueOverError,
    ValueOutOfRangeError,
)

from konica.utils import cmd_formatter, cl200a_cmd_dict
from konica.cl200a import ChromaMeterKonica, EvXY, XYZ, EvUV, EvTcpDuv
from konica.exceptions import (
    CL200ACriticalError,
    LowBatteryError,
    LowLuminanceError,
    MeasurementValueOverError,
    ValueOutOfRangeError,
)


class TestCmdFormatter(unittest.TestCase):
    """Tests for the cmd_formatter BCC/frame generation."""


    def test_frame_starts_with_stx(self):
        result = cmd_formatter('00021200')
        self.assertEqual(result[0], chr(2))

    def test_frame_ends_with_crlf(self):
        result = cmd_formatter('00021200')
        self.assertTrue(result.endswith('\r\n'))

    def test_frame_contains_etx(self):
        result = cmd_formatter('00021200')
        # ETX should be right after the command payload
        etx_pos = len(chr(2)) + len('00021200')
        self.assertEqual(result[etx_pos], chr(3))

    def test_command_01_produces_valid_frame(self):
        """command_01 was previously empty; verify it now produces a valid frame."""
        cmd = cl200a_cmd_dict['command_01']
        self.assertEqual(cmd, '00011200')
        result = cmd_formatter(cmd)
        self.assertEqual(result[0], chr(2))
        self.assertTrue(result.endswith('\r\n'))

    def test_bcc_is_two_digit_hex_string(self):
        result = cmd_formatter('00021200')
        # BCC is between ETX and CRLF, encoded as 2-digit uppercase hex
        bcc = result[-4:-2]  # 2 chars before \r\n
        self.assertEqual(len(bcc), 2)
        self.assertTrue(all(c in '0123456789ABCDEF' for c in bcc))

    def test_known_bcc_for_command_54(self):
        """Command 54 BCC computed via XOR of payload + ETX, encoded as 2 hex digits."""
        result = cmd_formatter('00541   ')
        bcc = result[-4:-2]
        self.assertEqual(bcc, '13')


class TestExtractValue(unittest.TestCase):
    """Tests for the static _extract_value method."""

    def test_positive_value(self):
        # +1234 with exponent 5 => 1 * 1234 * 10^(5-4) = 12340.0
        result = ChromaMeterKonica._extract_value('+12345xxxxx', start_index=0)
        self.assertEqual(result, 12340.0)

    def test_negative_value(self):
        # -1234 with exponent 5 => -1 * 1234 * 10^1 = -12340.0
        result = ChromaMeterKonica._extract_value('-12345xxxxx', start_index=0)
        self.assertEqual(result, -12340.0)

    def test_exponent_zero(self):
        # +1234 with exponent 0 => 1234 * 10^(-4) = 0.1234 => rounded to 3 decimals = 0.123
        result = ChromaMeterKonica._extract_value('+12340xxxxx', start_index=0)
        self.assertEqual(result, 0.123)

    def test_exponent_four(self):
        # +1234 with exponent 4 => 1234 * 10^0 = 1234.0
        result = ChromaMeterKonica._extract_value('+12344xxxxx', start_index=0)
        self.assertEqual(result, 1234.0)

    def test_with_offset(self):
        # Value starts at index 9
        response = '000000000+32545xxxxxx'
        result = ChromaMeterKonica._extract_value(response, start_index=9)
        # +3254 with exponent 5 => 3254 * 10^1 = 32540.0
        self.assertEqual(result, 32540.0)


class TestExtractThreeValues(unittest.TestCase):
    """Tests for extracting all three values from a long-format response."""

    def test_three_values(self):
        # Build a fake response: 9 chars prefix + 3 values of 6 chars each
        # Value 1 at index 9: +32543 => 3254 * 10^(3-4) = 325.4 => wait, exponent is char at index 14
        # Let me be precise:
        # Index 9: sign, 10-13: mantissa, 14: exponent
        # Index 15: sign, 16-19: mantissa, 20: exponent
        # Index 21: sign, 22-25: mantissa, 26: exponent
        response = '000020 20+32543+38564+40404'
        v1, v2, v3 = ChromaMeterKonica._extract_three_values(response)
        # v1: +3254, exp 3 => 3254 * 10^(3-4) = 325.4
        self.assertEqual(v1, 325.4)
        # v2: +3856, exp 4 => 3856 * 10^0 = 3856.0
        self.assertEqual(v2, 3856.0)
        # v3: +4040, exp 4 => 4040 * 10^0 = 4040.0
        self.assertEqual(v3, 4040.0)


class TestCheckStatus(unittest.TestCase):
    """Tests for _check_status error detection."""

    def _make_result(self, err_byte='0', ba_byte='0'):
        """Build a minimal fake result string with given ERR and BA bytes."""
        # Indices: 0-5 = header, 6 = ERR, 7 = RNG, 8 = BA, 9+ = data
        return '000020' + err_byte + '0' + ba_byte + '+12344+12344+12344'

    def test_normal_status(self):
        ChromaMeterKonica._check_status(self._make_result('0', '0'))

    def test_critical_error_1(self):
        with self.assertRaises(CL200ACriticalError):
            ChromaMeterKonica._check_status(self._make_result('1'))

    def test_critical_error_2(self):
        with self.assertRaises(CL200ACriticalError):
            ChromaMeterKonica._check_status(self._make_result('2'))

    def test_critical_error_3(self):
        with self.assertRaises(CL200ACriticalError):
            ChromaMeterKonica._check_status(self._make_result('3'))

    def test_measurement_over_range(self):
        with self.assertRaises(MeasurementValueOverError):
            ChromaMeterKonica._check_status(self._make_result('5'))

    def test_low_luminance(self):
        with self.assertRaises(LowLuminanceError):
            ChromaMeterKonica._check_status(self._make_result('6'))

    def test_value_out_of_range(self):
        with self.assertRaises(ValueOutOfRangeError):
            ChromaMeterKonica._check_status(self._make_result('7'))

    def test_low_battery(self):
        with self.assertRaises(LowBatteryError):
            ChromaMeterKonica._check_status(self._make_result('0', '1'))


class TestNamedTuples(unittest.TestCase):
    """Tests for result type NamedTuples."""

    def test_ev_xy(self):
        r = EvXY(ev=100.0, x=0.312, y=0.329)
        self.assertEqual(r.ev, 100.0)
        self.assertEqual(r.x, 0.312)
        self.assertEqual(r.y, 0.329)

    def test_xyz(self):
        r = XYZ(x=1.0, y=2.0, z=3.0)
        self.assertEqual(r.x, 1.0)
        self.assertEqual(r.y, 2.0)
        self.assertEqual(r.z, 3.0)

    def test_ev_uv(self):
        r = EvUV(ev=100.0, u_prime=0.2, v_prime=0.5)
        self.assertEqual(r.u_prime, 0.2)
        self.assertEqual(r.v_prime, 0.5)

    def test_ev_tcp_duv(self):
        r = EvTcpDuv(ev=100.0, tcp=6500.0, delta_uv=0.001)
        self.assertEqual(r.tcp, 6500.0)
        self.assertEqual(r.delta_uv, 0.001)


class TestCommandDictionary(unittest.TestCase):
    """Tests that the command dictionary has all expected entries."""

    def test_all_commands_present(self):
        expected = [
            'command_01', 'command_02', 'command_03', 'command_08',
            'command_15', 'command_40', 'command_40r', 'command_45',
            'command_47a', 'command_47b', 'command_47c',
            'command_48a', 'command_48b', 'command_48c',
            'command_54', 'command_54r', 'command_55',
        ]
        for cmd in expected:
            self.assertIn(cmd, cl200a_cmd_dict, msg=f'{cmd} missing from command dictionary')

    def test_command_01_not_empty(self):
        self.assertEqual(cl200a_cmd_dict['command_01'], '00011200')

    def test_measurement_commands_have_correct_prefix(self):
        self.assertTrue(cl200a_cmd_dict['command_01'].startswith('0001'))
        self.assertTrue(cl200a_cmd_dict['command_02'].startswith('0002'))
        self.assertTrue(cl200a_cmd_dict['command_03'].startswith('0003'))
        self.assertTrue(cl200a_cmd_dict['command_08'].startswith('0008'))
        self.assertTrue(cl200a_cmd_dict['command_15'].startswith('0015'))


if __name__ == '__main__':
    unittest.main()
