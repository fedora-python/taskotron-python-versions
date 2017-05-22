import glob
import os

from taskotron_python_versions.common import Package


def pkg(filename):
    return os.path.join(os.path.dirname(__file__), '..', 'fixtures', filename)


def gpkg(pkgglob):
    return Package(glob.glob(pkg(pkgglob))[0])
