from collections import namedtuple

import pytest

from taskotron_python_versions.requires import (
    DNFQuery,
    get_versioned_name,
    check_requires_naming_scheme,
)

from .common import gpkg


Package = namedtuple('Package', 'name')


class QueryStub(object):

    """Stub object for dnf repoquery."""

    def __init__(self, data):
        """Provide data as {<provide_name>: [<package_name>, ..], ..}, where
            `provide_name`: (str) name expected to be passed to filter method
            `package_name`: (str) package name providing it in query result
        """
        self.data = data

    def get_packages_by(self, provides):
        """Return repoquery result for the `provides` specified in filter.
        With each call, the result will be removed from provided data.

        Raises: ValueError if there is no data for the `provides` in filter.
        """
        if provides not in self.data:
            raise ValueError('Running repoquery on {} is not expected'.format(
                provides))
        package_names = self.data.pop(provides)
        return [Package(name=name) for name in package_names]


@pytest.mark.parametrize(('require', 'repoquery', 'expected'), (
    ('python-foo', QueryStub({'python-foo': []}), None),
    ('python-foo', QueryStub({'python-foo': ['python-foo']}), None),
    ('python-foo', QueryStub({'python-foo': ['python2-foo']}), 'python2-foo'),
    ('python', QueryStub({'python': ['python2']}), 'python2'),
))
def test_get_versioned_name(require, repoquery, expected):
    assert get_versioned_name(require, repoquery) == expected


@pytest.mark.parametrize(('pkgglob', 'repoquery'), (
    ('python2-geoip2*', QueryStub({})),
    ('pyserial*', QueryStub({})),
    ('python-peak-rules*', QueryStub({
        'python-decoratortools': ['python-decoratortools'],
        'python-peak-util-addons': ['python-peak-util-addons'],
        'python-peak-util-assembler': ['python-peak-util-assembler'],
        'python-peak-util-extremes': ['python-peak-util-extremes'],
    })),
))
def test_package_requires_are_correct(pkgglob, repoquery,):
    assert not check_requires_naming_scheme(gpkg(pkgglob), repoquery)
    # Make sure all items from repoquery.data were popped out.
    assert not repoquery.data, (
        'Repoquery was not called for: {}'.format(repoquery.data))


@pytest.mark.parametrize(('pkgglob', 'repoquery', 'expected'), (
    ('tracer*', QueryStub({
        'python': ['python'],
        'python-beautifulsoup4': ['python-beautifulsoup4'],
        'python-psutil': ['python2-psutil'],
        'rpm-python': ['rpm-python', 'python2-rpm']}),
     {'python-psutil (python2-psutil is available)',
      'rpm-python (python2-rpm is available)'}),
    ('yum*', QueryStub({
        'python': ['python2'],
        'python-iniparse': ['python2-iniparse'],
        'python-urlgrabber': ['python-urlgrabber'],
        'rpm-python': ['rpm-python', 'python2-rpm']}),
     {'python (python2 is available)',
      'python-iniparse (python2-iniparse is available)',
      'rpm-python (python2-rpm is available)'}),
))
def test_package_requires_are_misnamed(pkgglob, repoquery, expected):
    assert check_requires_naming_scheme(gpkg(pkgglob), repoquery) == expected
    # Make sure all items from repoquery.data were popped out.
    assert not repoquery.data, (
        'Repoquery was not called for: {}'.format(repoquery.data))


@pytest.mark.slow
def test_repoquery():
    repoquery = DNFQuery('25')
    packages = repoquery.get_packages_by(provides='python-setuptools')
    first = packages[0]
    assert first.name == 'python2-setuptools'
