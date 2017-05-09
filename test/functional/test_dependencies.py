import os

from pyversions import two_three_check


def pkg(filename):
    return os.path.join(os.path.dirname(__file__), '..', 'fixtures', filename)


def test_pyserial_depends_on_2_only():
    name, versions = two_three_check(pkg('pyserial-2.7-6.fc25.noarch.rpm'))
    assert name == b'pyserial'
    assert versions == {2}
