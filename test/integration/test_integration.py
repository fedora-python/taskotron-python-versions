from collections import namedtuple
import subprocess
import sys
from textwrap import dedent

import yaml

import pytest


Result = namedtuple('Result', ['outcome', 'artifact', 'item'])


def parse_results(log):
    '''
    From the given stdout log, parse the results
    '''
    start = 'results:'
    results = []
    record = False

    for line in log.splitlines():
        if line.strip() == start:
            record = True
        if record:
            results.append(line)
            if not line:
                break

    if not results:
        raise RuntimeError('Could not parse output')
    return yaml.load('\n'.join(results))['results']


def run_task(nevr, *, reterr=False):
    '''
    Run the task on a Koji build.
    Returns a dict with Results (outcome, artifact, item)
    If reterr is true, returns a tuple with the above and captured stderr
    If reterr is false, prints the stderr
    '''
    proc = subprocess.Popen(
        ['runtask', '-i', nevr, '-t', 'koji_build', 'runtask.yml'],
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )
    _, err = proc.communicate()
    if proc.returncode != 0:
        print(err, file=sys.stderr)  # always print stderr in this case
        raise RuntimeError('runtask exited with {}'.format(proc.returncode))
    results = parse_results(err)

    ret = {r['checkname']: Result(r.get('outcome'),
                                  r.get('artifact'),
                                  r.get('item')) for r in results}

    if reterr:
        return ret, err

    print(err, file=sys.stderr)
    return ret


def fixtures_factory(nevr):
    '''Given the NEVR and later name, create a fixture with the results

    Note that this has to be called twice and assigned to correct names!

    See examples bellow.'''
    if not nevr.startswith('_'):
        @pytest.fixture(scope="session")
        def _results():
            return run_task(nevr, reterr=True)

        return _results

    @pytest.fixture()
    def results(request):
        _results = request.getfixturevalue(nevr)
        print(_results[1], file=sys.stderr)
        return _results[0]

    return results


_tracer = fixtures_factory('tracer-0.6.9-1.fc23')
tracer = fixtures_factory('_tracer')

_copr = fixtures_factory('python-copr-1.77-1.fc26')
copr = fixtures_factory('_copr')

_eric = fixtures_factory('eric-6.1.6-2.fc25')
eric = fixtures_factory('_eric')

_six = fixtures_factory('python-six-1.10.0-3.fc25')
six = fixtures_factory('_six')

_admesh = fixtures_factory('python-admesh-0.98.5-3.fc25')
admesh = fixtures_factory('_admesh')

_epub = fixtures_factory('python-epub-0.5.2-8.fc26')
epub = fixtures_factory('_epub')

_twine = fixtures_factory('python-twine-1.8.1-3.fc26')
twine = fixtures_factory('_twine')

_yum = fixtures_factory('yum-3.4.3-512.fc26')
yum = fixtures_factory('_yum')


@pytest.mark.parametrize('results', ('eric', 'six', 'admesh', 'tracer',
                                     'copr', 'epub', 'twine', 'yum'))
def test_number_of_results(results, request):
    # getting a fixture by name
    # https://github.com/pytest-dev/pytest/issues/349#issuecomment-112203541
    results = request.getfixturevalue(results)

    # Each time a new check is added, this number needs to be increased
    assert len(results) == 4


@pytest.mark.parametrize('results', ('eric', 'six', 'admesh',
                                     'copr', 'epub', 'twine'))
def test_two_three_passed(results, request):
    results = request.getfixturevalue(results)
    assert results['python-versions.two_three'].outcome == 'PASSED'


def test_two_three_failed(tracer):
    assert tracer['python-versions.two_three'].outcome == 'FAILED'


@pytest.mark.parametrize('results', ('tracer', 'copr', 'admesh'))
def test_one_failed_result_is_total_failed(results, request):
    results = request.getfixturevalue(results)
    assert results['python-versions'].outcome == 'FAILED'


@pytest.mark.parametrize(('results', 'task'),
                         (('tracer', 'two_three'),
                          ('copr', 'naming_scheme'),
                          ('admesh', 'requires_naming_scheme')))
def test_artifact_is_the_same(results, task, request):
    results = request.getfixturevalue(results)
    assert (results['python-versions'].artifact ==
            results['python-versions.' + task].artifact)


def test_artifact_contains_two_three_and_looks_as_expected(tracer):
    result = tracer['python-versions.two_three']
    with open(result.artifact) as f:
        artifact = f.read()

    assert dedent('''
        These RPMs require both Python 2 and Python 3:
        {}.noarch.rpm
         * Python 2 dependency: python(abi) = 2.7
         * Python 3 dependecny: python(abi) = 3.4
    ''').strip().format(result.item) in artifact.strip()


@pytest.mark.parametrize('results', ('eric', 'epub', 'twine'))
def test_naming_scheme_passed(results, request):
    results = request.getfixturevalue(results)
    assert results['python-versions.naming_scheme'].outcome == 'PASSED'


@pytest.mark.parametrize('results', ('copr', 'six', 'admesh'))
def test_naming_scheme_failed(results, request):
    results = request.getfixturevalue(results)
    assert results['python-versions.naming_scheme'].outcome == 'FAILED'


def test_artifact_contains_naming_scheme_and_looks_as_expected(copr):
    result = copr['python-versions.naming_scheme']
    with open(result.artifact) as f:
        artifact = f.read()

    assert dedent("""
        These RPMs' names violate the new Python package naming guidelines:
        {}
    """).strip().format(result.item) in artifact.strip()


@pytest.mark.parametrize('results', ('eric', 'twine', 'six'))
def test_requires_naming_scheme_passed(results, request):
    results = request.getfixturevalue(results)
    task_result = results['python-versions.requires_naming_scheme']
    assert task_result.outcome == 'PASSED'


@pytest.mark.parametrize('results', ('admesh', 'copr'))
def test_requires_naming_scheme_failed(results, request):
    results = request.getfixturevalue(results)
    task_result = results['python-versions.requires_naming_scheme']
    assert task_result.outcome == 'FAILED'


def test_artifact_contains_requires_naming_scheme_and_looks_as_expected(
        tracer):
    result = tracer['python-versions.requires_naming_scheme']
    with open(result.artifact) as f:
        artifact = f.read()

    print(artifact)

    assert dedent("""
        These RPMs use `python-` prefix without Python version in *Requires:

        tracer-0.6.9-1.fc23 BuildRequires:
         * python-psutil (python2-psutil is available)

        tracer-0.6.9-1.fc23 Requires:
         * python-psutil (python2-psutil is available)

        This is strongly discouraged and should be avoided. Please check
        the required packages, and use names with either `python2-` or
        `python3-` prefix.
    """).strip() in artifact.strip()


def test_requires_naming_scheme_contains_python(yum):
    result = yum['python-versions.requires_naming_scheme']
    with open(result.artifact) as f:
        artifact = f.read()

    print(artifact)

    assert 'python (python2 is available)' in artifact.strip()
