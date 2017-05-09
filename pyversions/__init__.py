import logging

log = logging.getLogger('python-versions')
log.setLevel(logging.DEBUG)
log.addHandler(logging.NullHandler())

from .dependencies import two_three_check

__all__ = ('log', 'two_three_check')
