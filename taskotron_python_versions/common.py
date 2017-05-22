import logging
import os

import rpm

log = logging.getLogger('python-versions')
log.setLevel(logging.DEBUG)
log.addHandler(logging.NullHandler())

BUG_URL = 'https://github.com/fedora-python/task-python-versions/issues'


class PackageException(Exception):

    """Base Exception class for Package API."""


class Package(object):

    """RPM Package API."""

    def __init__(self, path):
        """Given the path to the RPM package, initialize
        the RPM package header containing its metadata.
        """
        self.filename = os.path.basename(path)
        # To be populated in the first check.
        self.py_versions = None

        ts = rpm.TransactionSet()
        with open(path, 'rb') as fdno:
            try:
                self.hdr = ts.hdrFromFdno(fdno)
            except rpm.error as err:
                raise PackageException('{}: {}'.format(self.filename, err))

    @property
    def name(self):
        """Package name as a string."""
        return self.hdr[rpm.RPMTAG_NAME].decode()

    @property
    def require_names(self):
        return self.hdr[rpm.RPMTAG_REQUIRENAME]

    @property
    def require_nevrs(self):
        return self.hdr[rpm.RPMTAG_REQUIRENEVRS]

    @property
    def files(self):
        return self.hdr[rpm.RPMTAG_FILENAMES]
