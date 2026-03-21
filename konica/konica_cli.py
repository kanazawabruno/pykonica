# coding=utf-8
import argparse
from logging import DEBUG

from konica.version import __version__
from konica.cl200a import ChromaMeterKonica
from konica.logger import log


MODES = {
    'ev_xy': 'get_ev_x_y',
    'xyz': 'get_x_y_z',
    'ev_uv': 'get_ev_u_v',
    'ev_tcp_duv': 'get_ev_tcp_delta_uv',
}


def main():
    """Main function for Konica Minolta CL-200A CLI."""
    parser = argparse.ArgumentParser(description='Konica Minolta CL-200A CLI')
    parser.add_argument('--lux', action='store_true',
                        help='Read lux (Ev) measurement')
    parser.add_argument('--mode', choices=MODES.keys(),
                        help='Measurement mode: ev_xy, xyz, ev_uv, ev_tcp_duv')
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

    k = ChromaMeterKonica()

    if args.lux:
        print(k.get_lux())
    elif args.mode:
        method = getattr(k, MODES[args.mode])
        result = method()
        for field, value in zip(result._fields, result):
            print("{0}={1}".format(field, value))
    else:
        parser.print_help()

    k.close()


if __name__ == '__main__':
    main()
