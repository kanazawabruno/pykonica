# coding=utf-8
import logging

__all__ = ['log']

logging.basicConfig(level=logging.INFO,
                    format='%(levelname)s: %(asctime)s -'
                           ' %(funcName)s - %(message)s')
log = logging.getLogger('pk')
