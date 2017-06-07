import pytest

from taskotron_python_versions.executables import (
    is_binary,
    have_binaries,
    get_binaries,
)

from .common import gpkg


@pytest.mark.parametrize('filepath', (
    '/usr/bin/foo',
    '/usr/bin/foo.py',
    '/usr/sbin/foo',
))
def test_is_binary(filepath):
    assert is_binary(filepath)


@pytest.mark.parametrize('filepath', (
    'foo',
    '/usr/lib/foo',
    '/usr/lib64/foo.py',
))
def test_is_not_binary(filepath):
    assert not is_binary(filepath)


@pytest.mark.parametrize('pkgglob', (
    'pyserial*',
    'python3-pyserial*',
    'tracer*',
    'yum*',
))
def test_have_binaries(pkgglob):
    assert have_binaries([gpkg(pkgglob)])


@pytest.mark.parametrize('pkgglob', (
    'python2-geoip2*',
    'libgccjit-devel*',
    'python-peak-rules*',
))
def test_does_not_have_binaries(pkgglob):
    assert not have_binaries([gpkg(pkgglob)])


@pytest.mark.parametrize(('pkgglob', 'expected'), (
    ('python2-geoip2*', set()),
    ('pyserial*', {'/usr/bin/miniterm-2.7.py',
                   '/usr/bin/miniterm-2.py',
                   '/usr/bin/miniterm.py'}),
    ('python3-pyserial*', {'/usr/bin/miniterm-3.5.py',
                           '/usr/bin/miniterm-3.py'}),
    ('tracer*', {'/usr/bin/tracer'}),
    ('yum*', {'/usr/bin/yum-deprecated'}),
))
def test_get_binaries(pkgglob, expected):
    package = gpkg(pkgglob)
    assert get_binaries([package])[package.nvr] == expected
