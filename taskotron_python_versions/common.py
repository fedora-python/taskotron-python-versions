import collections
import logging
import os

import mmap
import rpm

log = logging.getLogger('python-versions')
log.setLevel(logging.DEBUG)
log.addHandler(logging.NullHandler())

BUG_URL = 'https://github.com/fedora-python/task-python-versions/issues'

TEMPLATE = """
{message}

Read the following document to find more information and a possible cause:
{info_url}
Or ask at #fedora-python IRC channel for help.

If you think the result is false or intentional, file a bug against:
{bug_url}

-----------
"""


def write_to_artifact(artifact, message, info_url):
    """Write failed check result details to atrifact."""
    with open(artifact, 'a') as f:
        f.write(TEMPLATE.format(
            message=message,
            info_url=info_url,
            bug_url=BUG_URL))


def packages_by_version(packages):
    """Given the list of packages, group them by the Python
    version they are built for.

    Return: (dict) Python version: list of packages
    """
    pkg_by_version = collections.defaultdict(list)
    for package in packages:
        if package.py_versions is None:  # SRPMS
            continue
        for version in package.py_versions:
            pkg_by_version[version].append(package)
    return pkg_by_version


def file_contains(path, needle):
    """Check if the file residing on the given path contains the given needle
    """
    # Since we have no idea if build.log is valid utf8, let's convert our ASCII
    # needle to bytes and use bytes everywhere.
    # This also allow us to use mmap on Python 3.
    # Be explicit here, to make it fail early if our needle is not ASCII.
    needle = needle.encode('ascii')

    with open(path, 'rb') as f:
        # build.logs tend to be laaaarge, so using a single read() is bad idea;
        # let's optimize prematurely because practicality beats purity

        # Memory-mapped file object behaving like bytearray
        with mmap.mmap(f.fileno(),
                       length=0,  # = determine automatically
                       access=mmap.ACCESS_READ) as mmf:
            return mmf.find(needle) != -1


class PackageException(Exception):

    """Base Exception class for Package API."""


class Package(object):

    """RPM Package API."""

    def __init__(self, path):
        """Given the path to the RPM package, initialize
        the RPM package header containing its metadata.
        """
        self.filename = os.path.basename(path)
        self.path = path
        # To be populated in the first check.
        self.py_versions = None

        ts = rpm.TransactionSet()
        with open(path, 'rb') as fdno:
            try:
                self.hdr = ts.hdrFromFdno(fdno)
            except rpm.error as err:
                raise PackageException('{}: {}'.format(self.filename, err))

    @property
    def is_srpm(self):
        return self.filename.endswith('.src.rpm')

    @property
    def name(self):
        """Package name as a string."""
        return self.hdr[rpm.RPMTAG_NAME].decode()

    @property
    def nvr(self):
        """Package name and version as a string."""
        return self.hdr[rpm.RPMTAG_NVR].decode()

    @property
    def require_names(self):
        return [r.decode() for r in self.hdr[rpm.RPMTAG_REQUIRENAME]]

    @property
    def require_nevrs(self):
        return [r.decode() for r in self.hdr[rpm.RPMTAG_REQUIRENEVRS]]

    @property
    def files(self):
        """Package file names as a list of strings."""
        return [name.decode() for name in self.hdr[rpm.RPMTAG_FILENAMES]]
