# coding=utf-8
import argparse
from logging import DEBUG

from konica.version import __version__
from konica.logger import log


CL200A_MODES = {
    'ev_xy': 'get_ev_x_y',
    'xyz': 'get_x_y_z',
    'ev_uv': 'get_ev_u_v',
    'ev_tcp_duv': 'get_ev_tcp_delta_uv',
}

CA410_MODES = {
    'lv_xy': 'get_lv_x_y',
    'xyz': 'get_x_y_z',
    'lv_uv': 'get_lv_u_v',
    'lv_tcp_duv': 'get_lv_tcp_duv',
    'flicker_jis': 'get_flicker',
    'flicker_vesa': 'get_flicker',
}


def _create_device(device_type, port=None):
    """Create the appropriate device instance."""
    if device_type == 'ca410':
        from konica.ca410 import ColorAnalyzerCA410
        return ColorAnalyzerCA410(port=port)
    else:
        from konica.cl200a import ChromaMeterKonica
        return ChromaMeterKonica()


def main():
    """Main function for Konica Minolta instrument CLI."""
    parser = argparse.ArgumentParser(description='Konica Minolta Instrument CLI')
    parser.add_argument('-d', '--device', choices=['cl200a', 'ca410'], default='cl200a',
                        help='Device type (default: cl200a)')
    parser.add_argument('-p', '--port', type=str, default=None,
                        help='Serial port (e.g. COM3, /dev/ttyUSB0). Auto-detected if omitted.')
    parser.add_argument('--lux', action='store_true',
                        help='Read lux/luminance measurement')
    parser.add_argument('--mode', type=str,
                        help='Measurement mode (device-dependent)')
    parser.add_argument('--flicker', choices=['jis', 'vesa'],
                        help='Read flicker measurement (CA-410 only)')
    parser.add_argument('-V', '--verbose', action='store_true',
                        help='Show more debug information')
    parser.add_argument('-v', '--version', action='store_true',
                        help='Shows current version of the program')
    args = parser.parse_args()

    if args.version:
        print("pykonica v{0}".format(__version__))
        exit(0)

    if args.verbose:
        log.setLevel(DEBUG)

    modes = CA410_MODES if args.device == 'ca410' else CL200A_MODES

    if args.mode and args.mode not in modes:
        valid = ', '.join(modes.keys())
        parser.error('Invalid mode for {}: {}. Choose from: {}'.format(
            args.device, args.mode, valid))

    if args.lux or args.mode or args.flicker:
        k = _create_device(args.device, args.port)
        try:
            if args.flicker:
                if args.device != 'ca410':
                    parser.error('--flicker is only supported with --device ca410')
                print(k.get_flicker(mode=args.flicker))
            elif args.lux:
                if args.device == 'ca410':
                    print(k.get_luminance())
                else:
                    print(k.get_lux())
            elif args.mode:
                method_name = modes[args.mode]
                if args.mode.startswith('flicker'):
                    flicker_type = 'jis' if args.mode == 'flicker_jis' else 'vesa'
                    result = k.get_flicker(mode=flicker_type)
                    print("flicker={}".format(result))
                else:
                    method = getattr(k, method_name)
                    result = method()
                    for field, value in zip(result._fields, result):
                        print("{0}={1}".format(field, value))
        finally:
            k.close()
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
