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


def run_task(nevr):
    '''
    Run the task on a Koji build.
    Returns a dict with Results (outcome, artifact, item)
    '''
    proc = subprocess.Popen(
        ['runtask', '-i', nevr, '-t', 'koji_build', 'runtask.yml'],
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )
    _, err = proc.communicate()
    print(err, file=sys.stderr)
    if proc.returncode != 0:
        raise RuntimeError('runtask exited with {}'.format(proc.returncode))
    results = parse_results(err)

    return {r['checkname']: Result(r.get('outcome'),
                                   r.get('artifact'),
                                   r.get('item')) for r in results}


@pytest.mark.parametrize('nevr', ('eric-6.1.6-2.fc25',
                                  'python-six-1.10.0-3.fc25',
                                  'python-admesh-0.98.5-3.fc25'))
def test_two_three_nevr_passed(nevr):
    assert run_task(nevr)['python-versions.two_three'].outcome == 'PASSED'


@pytest.fixture()
def tracer_results():
    '''This should FAIL the two_three check'''
    return run_task('tracer-0.6.9-1.fc23')


def test_two_three_nevr_failed(tracer_results):
    assert tracer_results['python-versions.two_three'].outcome == 'FAILED'


def test_one_failed_result_is_total_failed(tracer_results):
    assert tracer_results['python-versions'].outcome == 'FAILED'


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
