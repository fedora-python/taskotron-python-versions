import pytest
from xdist.scheduler import LoadScopeScheduling


def parse_fixture_name(nodeid):
    if '[' in nodeid:
        parameters = nodeid.rsplit('[')[-1].replace(']', '')
        return parameters.split('-')[0]
    return None


def pytest_addoption(parser):
    parser.addoption('--fake', action='store_true', default=False,
                     help='don\'t run the code, reuse the result from '
                          'last tests')


class FixtureScheduling(LoadScopeScheduling):
    """Split by [] value. This is very hackish and might blow up any time!
    See https://github.com/pytest-dev/pytest-xdist/issues/18
    """
    def _split_scope(self, nodeid):
        return parse_fixture_name(nodeid)


def pytest_xdist_make_scheduler(log, config):
    return FixtureScheduling(config, log)


def pytest_collection_modifyitems(items):
    for item in items:
        fixture = parse_fixture_name(item.nodeid)
        if fixture:
            item.add_marker(getattr(pytest.mark, fixture))
