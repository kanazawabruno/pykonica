# -*- coding: utf-8 -*-

import unittest
from unittest.mock import patch, MagicMock

from konica.ca410 import (
    ColorAnalyzerCA410,
    LvXY, LvUV, LvTcpDuv,
    DISPLAY_MODES,
)
from konica.exceptions import (
    CA410Error,
    CA410CommandError,
    CA410MeasurementError,
    CA410CalibrationError,
)


class TestCA410NamedTuples(unittest.TestCase):
    """Tests for CA-410 result type NamedTuples."""

    def test_lv_xy(self):
        r = LvXY(lv=150.0, x=0.312, y=0.329)
        self.assertEqual(r.lv, 150.0)
        self.assertEqual(r.x, 0.312)
        self.assertEqual(r.y, 0.329)

    def test_lv_uv(self):
        r = LvUV(lv=150.0, u_prime=0.198, v_prime=0.468)
        self.assertEqual(r.lv, 150.0)
        self.assertEqual(r.u_prime, 0.198)
        self.assertEqual(r.v_prime, 0.468)

    def test_lv_tcp_duv(self):
        r = LvTcpDuv(lv=150.0, tcp=6500.0, delta_uv=0.001)
        self.assertEqual(r.tcp, 6500.0)
        self.assertEqual(r.delta_uv, 0.001)


class TestCA410DisplayModes(unittest.TestCase):
    """Tests for display mode constants."""

    def test_all_modes_present(self):
        expected = ['lv_xy', 'lv_uv', 'lv_tcp_duv', 'xyz',
                    'flicker_jis', 'flicker_vesa', 'lv_dominant_wavelength']
        for mode in expected:
            self.assertIn(mode, DISPLAY_MODES,
                          msg='{} missing from DISPLAY_MODES'.format(mode))

    def test_mode_values_are_integers(self):
        for mode, value in DISPLAY_MODES.items():
            self.assertIsInstance(value, int,
                                 msg='{} mode value should be int'.format(mode))


class TestCA410Errors(unittest.TestCase):
    """Tests for CA-410 error handling."""

    def test_error_code_stored(self):
        err = CA410Error('ER05')
        self.assertEqual(err.error_code, 'ER05')

    def test_error_message_from_code(self):
        err = CA410Error('ER00')
        self.assertIn('Command error', str(err))

    def test_unknown_error_code(self):
        err = CA410Error('ER99')
        self.assertIn('Unknown error', str(err))

    def test_custom_message(self):
        err = CA410Error('ER00', 'Custom message')
        self.assertEqual(str(err), 'Custom message')

    def test_command_error_hierarchy(self):
        err = CA410CommandError('ER10')
        self.assertIsInstance(err, CA410Error)

    def test_measurement_error_hierarchy(self):
        err = CA410MeasurementError('ER05')
        self.assertIsInstance(err, CA410Error)

    def test_calibration_error_hierarchy(self):
        err = CA410CalibrationError('ER30')
        self.assertIsInstance(err, CA410Error)


class TestCA410RaiseError(unittest.TestCase):
    """Tests for _raise_error classification."""

    def test_command_errors(self):
        for code in ('ER00', 'ER10', 'ER11', 'ER13'):
            with self.assertRaises(CA410CommandError, msg='Expected CA410CommandError for {}'.format(code)):
                ColorAnalyzerCA410._raise_error(code)

    def test_measurement_errors(self):
        for code in ('ER02', 'ER05'):
            with self.assertRaises(CA410MeasurementError, msg='Expected CA410MeasurementError for {}'.format(code)):
                ColorAnalyzerCA410._raise_error(code)

    def test_calibration_errors(self):
        for code in ('ER19', 'ER30', 'ER52'):
            with self.assertRaises(CA410CalibrationError, msg='Expected CA410CalibrationError for {}'.format(code)):
                ColorAnalyzerCA410._raise_error(code)

    def test_unknown_error(self):
        with self.assertRaises(CA410Error):
            ColorAnalyzerCA410._raise_error('ER99')


class TestCA410ParseMeasurement(unittest.TestCase):
    """Tests for response parsing."""

    def test_parse_ok_response(self):
        obj = ColorAnalyzerCA410.__new__(ColorAnalyzerCA410)
        parts = obj._parse_measurement('OK00,P1,  123.4,0.3127,0.3290')
        self.assertEqual(parts[0], 'OK00')
        self.assertEqual(parts[1], 'P1')
        self.assertEqual(parts[2].strip(), '123.4')
        self.assertEqual(parts[3], '0.3127')
        self.assertEqual(parts[4], '0.3290')

    def test_parse_error_response(self):
        obj = ColorAnalyzerCA410.__new__(ColorAnalyzerCA410)
        with self.assertRaises(CA410Error):
            obj._parse_measurement('ER05')

    def test_parse_xyz_response(self):
        obj = ColorAnalyzerCA410.__new__(ColorAnalyzerCA410)
        parts = obj._parse_measurement('OK00,P1,  45.12,  38.56,  20.10')
        self.assertAlmostEqual(float(parts[2]), 45.12)
        self.assertAlmostEqual(float(parts[3]), 38.56)
        self.assertAlmostEqual(float(parts[4]), 20.10)


if __name__ == '__main__':
    unittest.main()
