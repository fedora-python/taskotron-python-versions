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


@pytest.fixture()
def tracer_results(_tracer_results):
    '''This should FAIL the two_three check'''
    print(_tracer_results[1], file=sys.stderr)
    return _tracer_results[0]


@pytest.fixture(scope="session")
def _tracer_results():
    return run_task('tracer-0.6.9-1.fc23', reterr=True)


@pytest.fixture()
def copr_results(_copr_results):
    '''This should FAIL the name_scheme check'''
    print(_copr_results[1], file=sys.stderr)
    return _copr_results[0]


@pytest.fixture(scope="session")
def _copr_results():
    return run_task('python-copr-1.77-1.fc26', reterr=True)


@pytest.mark.parametrize('nevr', ('eric-6.1.6-2.fc25',
                                  'python-six-1.10.0-3.fc25',
                                  'python-admesh-0.98.5-3.fc25'))
def test_two_three_nevr_passed(nevr):
    assert run_task(nevr)['python-versions.two_three'].outcome == 'PASSED'


def test_two_three_nevr_failed(tracer_results):
    assert tracer_results['python-versions.two_three'].outcome == 'FAILED'


@pytest.mark.parametrize('results', ('tracer_results', 'copr_results'))
def test_one_failed_result_is_total_failed(results, request):
    # getting a fixture by name
    # https://github.com/pytest-dev/pytest/issues/349#issuecomment-112203541
    results = request.getfixturevalue(results)
    assert results['python-versions'].outcome == 'FAILED'


def test_artifact_is_the_same(tracer_results):
    assert (tracer_results['python-versions'].artifact ==
            tracer_results['python-versions.two_three'].artifact)


def test_artifact_contains_two_three_and_looks_as_expected(tracer_results):
    result = tracer_results['python-versions.two_three']
    with open(result.artifact) as f:
        artifact = f.read()

    assert dedent('''
        These RPMs require both Python 2 and Python 3:
        {}.noarch.rpm
         * Python 2 dependency: python(abi) = 2.7
         * Python 3 dependecny: python(abi) = 3.4
    ''').strip().format(result.item) in artifact.strip()


@pytest.mark.parametrize('nevr', ('eric-6.1.6-2.fc25',
                                  'python-epub-0.5.2-8.fc26'))
def test_naming_scheme_nevr_passed(nevr):
    assert run_task(nevr)['python-versions.naming_scheme'].outcome == 'PASSED'


def test_naming_scheme_nevr_failed(copr_results):
    assert copr_results['python-versions.naming_scheme'].outcome == 'FAILED'


def test_artifact_contains_naming_scheme_and_looks_as_expected(copr_results):
    result = copr_results['python-versions.naming_scheme']
    with open(result.artifact) as f:
        artifact = f.read()

    assert dedent("""
        These RPMs' names violate the new Python package naming guidelines:
        {}
    """).strip().format(result.item) in artifact.strip()


@pytest.mark.parametrize('nevr', ('eric-6.1.6-2.fc25',
                                  'python-twine-1.8.1-3.fc26'))
def test_requires_naming_scheme_nevr_passed(nevr):
    task_result = run_task(nevr)['python-versions.requires_naming_scheme']
    assert task_result.outcome == 'PASSED'


def test_requires_naming_scheme_nevr_failed(copr_results):
    task_result = copr_results['python-versions.requires_naming_scheme']
    assert task_result.outcome == 'FAILED'


def test_artifact_contains_requires_naming_scheme_and_looks_as_expected(
        tracer_results):
    result = tracer_results['python-versions.requires_naming_scheme']
    with open(result.artifact) as f:
        artifact = f.read()

    print(artifact)

    expected_requires = 'python-psutil (python2-psutil is available)'

    assert dedent("""
        These RPMs use `python-` prefix without Python version in *Requires:
        {}
         * Requires: {}

        This is strongly discouraged and should be avoided. Please check
        the required packages, and use names with either `python2-` or
        `python3-` prefix.
    """).strip().format(result.item, expected_requires) in artifact.strip()
