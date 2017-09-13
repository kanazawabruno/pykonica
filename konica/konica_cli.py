# coding=utf-8
import argparse
from logging import DEBUG

from konica.version import __version__
from konica.cl200a import ChromaMeterKonica
from konica.logger import log


def main():
    """
    Main function
    """
    parser = argparse.ArgumentParser(description='Konica Minolta CL200a CLI')
    parser.add_argument('--lux', help='foo help')
    parser.add_argument('-V', '--verbose', action='store_true',
                        help='Show more information on what''s happening.')
    parser.add_argument('-v', '--version', action='store_true',
                        help='Shows current version of the program')
    args = parser.parse_args()

    k = ChromaMeterKonica()

    if args.version:
        log.info("pykonica v{0}".format(__version__))
        exit(0)

    if args.lux:
        log.info(k.get_lux())

    if args.verbose:
        log.setLevel(DEBUG)

    log.info('Starting spotify_dl')
    log.debug('Setting debug mode on spotify_dl')


if __name__ == '__main__':
    main()
