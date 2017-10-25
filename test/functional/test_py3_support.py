from collections import namedtuple

import pytest

from taskotron_python_versions.py3_support import (
    ignored,
    filter_urls,
    ported_to_py3,
    PY3_TRACKER_BUG,
    IGNORE_TRACKER_BUGS,
)
from taskotron_python_versions.two_three import check_two_three
from .common import gpkg


BugStub = namedtuple('BugStub', 'blocks, weburl, status')
BugStub.__new__.__defaults__ = (None, 'http://test', 'NEW')


@pytest.mark.parametrize('bug', (
    BugStub(blocks=IGNORE_TRACKER_BUGS),
    BugStub(blocks=[PY3_TRACKER_BUG] + IGNORE_TRACKER_BUGS),
    BugStub(blocks=IGNORE_TRACKER_BUGS + ['X']),
    BugStub(blocks=IGNORE_TRACKER_BUGS, status='NEW'),
    BugStub(blocks=[PY3_TRACKER_BUG], status='CLOSED'),
    BugStub(blocks=[PY3_TRACKER_BUG], status='VERIFIED'),
    BugStub(blocks=[PY3_TRACKER_BUG], status='RELEASE_PENDING'),
    BugStub(blocks=[PY3_TRACKER_BUG], status='ON_QA'),
))
def test_ignored(bug):
    assert ignored(bug)


@pytest.mark.parametrize('bug', (
    BugStub(blocks=[PY3_TRACKER_BUG]),
    BugStub(blocks=[PY3_TRACKER_BUG, 'X']),
    BugStub(blocks=[PY3_TRACKER_BUG], status='NEW'),
    BugStub(blocks=[PY3_TRACKER_BUG], status='ASSIGNED'),
))
def test_not_ignored(bug):
    assert not ignored(bug)


@pytest.mark.parametrize(('bugs', 'expected'), (
    ([BugStub(blocks=[PY3_TRACKER_BUG])], ['http://test']),
    ([BugStub(blocks=[PY3_TRACKER_BUG], status='NEW')], ['http://test']),
    ([BugStub(blocks=[PY3_TRACKER_BUG], status='CLOSED')], []),
    ([BugStub(blocks=IGNORE_TRACKER_BUGS)], []),
    ([BugStub(blocks=IGNORE_TRACKER_BUGS, status='NEW')], []),
    ([BugStub(blocks=[PY3_TRACKER_BUG], weburl='test1'),
      BugStub(blocks=IGNORE_TRACKER_BUGS, weburl='test2')], ['test1']),
))
def test_filter_urls(bugs, expected):
    assert filter_urls(bugs) == expected


@pytest.mark.parametrize(('pkgglobs', 'expected'), (
    (('pyserial*', 'python3-pyserial*'), True),
    (('pyserial*',), False),
    (('python3-pyserial*',), True),
))
def test_ported_to_py3(pkgglobs, expected):
    packages = [gpkg(pkg) for pkg in pkgglobs]
    for package in packages:
        check_two_three(package)
    assert ported_to_py3(packages) == expected
