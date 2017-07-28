import glob
import os

from taskotron_python_versions.common import Package


def pkg_path(filename):
    """Returns a path for given rpm in fixture"""
    return os.path.join(os.path.dirname(__file__), '..', 'fixtures', filename)


def gpkg_path(pkgglob):
    """Returns a path for the first rpm satisfying given glob"""
    return glob.glob(pkg_path(pkgglob))[0]


def gpkg(pkgglob):
    """Returns a Package object for the first rpm satisfying given glob"""
    return Package(gpkg_path(pkgglob))
