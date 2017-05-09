from collections import namedtuple
import subprocess
import sys
from textwrap import dedent

import yaml

import pytest


PASSED = 'PASSED'
FAILED = 'FAILED'
FAILED_NEVR = 'tracer-0.6.9-1.fc23'


Result = namedtuple('Result', ['outcome', 'artifact'])


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
    Returns the outcome and artifact in the Result namedtuple
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

    outcome = results[0]['outcome']  # this might be longer list in the future
    artifact = results[0].get('artifact')
    return Result(outcome, artifact)


@pytest.mark.parametrize('nevr', ('eric-6.1.6-2.fc25',
                                  'python-six-1.10.0-3.fc25',
                                  'python-admesh-0.98.5-3.fc25'))
def test_nevr_passed(nevr):
    assert run_task(nevr).outcome == PASSED


@pytest.mark.parametrize('nevr', (FAILED_NEVR,))
def test_nevr_failed(nevr):
    assert run_task(nevr).outcome == FAILED


def test_artifact_looks_as_expected():
    artifact = run_task(FAILED_NEVR).artifact
    with open(artifact) as f:
        artifact = f.read()

    assert artifact.strip().startswith(dedent('''
        These RPMs require both Python 2 and Python 3:
        {}.noarch.rpm
    ''').format(FAILED_NEVR).strip())
