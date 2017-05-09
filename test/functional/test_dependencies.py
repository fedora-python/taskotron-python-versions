import glob
import os

import pytest

from pyversions import two_three_check


def pkg(filename):
    return os.path.join(os.path.dirname(__file__), '..', 'fixtures', filename)


def gpkg(pkgglob):
    return glob.glob(pkg(pkgglob))[0]


@pytest.mark.parametrize('pkgglob', ('pyserial*', 'python-peak-rules*',
                                     'python2-geoip2*'))
def test_package_depends_on_2_only(pkgglob):
    name, versions = two_three_check(gpkg(pkgglob))
    assert versions == {2}


@pytest.mark.parametrize('pkgglob', ('python3-pyserial*',))
def test_package_depends_on_3_only(pkgglob):
    name, versions = two_three_check(gpkg(pkgglob))
    assert versions == {3}


@pytest.mark.parametrize('pkgglob', ('tracer*',))
def test_package_depends_on_2_and_3(pkgglob):
    name, versions = two_three_check(gpkg(pkgglob))
    assert versions == {2, 3}


@pytest.mark.parametrize('pkgglob', ('libgccjit-devel*',))
def test_package_depends_on_no_python(pkgglob):
    name, versions = two_three_check(gpkg(pkgglob))
    assert not versions
