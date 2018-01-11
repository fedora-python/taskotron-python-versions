import pytest

from taskotron_python_versions.naming_scheme import (
    has_pythonX_package,
    is_unversioned,
    check_naming_policy,
)

from .common import gpkg


@pytest.mark.parametrize(('pkgglob', 'name_by_version'), (
    ('pyserial*', {2: ('pyserial',), 3: ('python3-pyserial',)}),
    ('python-peak-rules*', {2: ('python-peak-rules',)}),
))
def test_package_is_misnamed(pkgglob, name_by_version):
    assert check_naming_policy(gpkg(pkgglob), name_by_version)


@pytest.mark.parametrize(('pkgglob', 'name_by_version'), (
    ('python2-geoip2*', {2: ('python2-geoip2',), 3: ('python3-geoip2',)}),
    ('python3-pyserial*', {2: ('pyserial',), 3: ('python3-pyserial',)}),
    ('tracer*', {3: ('tracer',)}),
))
def test_package_is_named_correctly(pkgglob, name_by_version):
    assert not check_naming_policy(gpkg(pkgglob), name_by_version)


@pytest.mark.parametrize('name', (
    'python-foo',
    'foo-python-foo'
    'foo-python'
))
def test_is_unversioned_positive(name):
    assert is_unversioned(name)


@pytest.mark.parametrize('name', (
    'python2-foo',
    'foo-python2',
    'foo-python2-foo',
    'python3-foo',
    'foo-python3',
    'foo-python3-foo',
    'python3-foo-python',
    'python2-foo-python',
    'python3-foo-python-foo',
    'python2-foo-python-foo',
    '/usr/libexec/system-python',
    'libsamba-python-samba4.so',
))
def test_is_unversioned_negative(name):
    assert not is_unversioned(name)


@pytest.mark.parametrize(('pkg_name', 'name_by_version', 'version'), (
    ('foo', {2: ('python2-foo',)}, 2),
    ('foo', {2: ('foo-python2',)}, 2),
    ('foo', {3: ('python3-foo',)}, 3),
    ('foo', {3: ('foo-python3',)}, 3),
))
def test_has_pythonX_package_positive(pkg_name, name_by_version, version):
    assert has_pythonX_package(pkg_name, name_by_version, version)


@pytest.mark.parametrize(('pkg_name', 'name_by_version', 'version'), (
    ('foo', {2: (), 3: ()}, 3),
    ('foo', {2: ('python2-foo',), 3: ()}, 3),
    ('foo', {2: (), 3: ('python3-foo',)}, 2),
))
def test_has_pythonX_package_negative(pkg_name, name_by_version, version):
    assert not has_pythonX_package(pkg_name, name_by_version, version)
