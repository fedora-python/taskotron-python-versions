import subprocess
import sys

import yaml

import pytest


PASSED = 'PASSED'
FAILED = 'FAILED'


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
    Run the task on a Koji build
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
    return results[0]['outcome']  # this might be longer list in the future


@pytest.mark.parametrize('nevr', ('eric-6.1.6-2.fc25',
                                  'python-six-1.10.0-3.fc25',
                                  'python-admesh-0.98.5-3.fc25'))
def test_nevr_passed(nevr):
    assert run_task(nevr) == PASSED


@pytest.mark.parametrize('nevr', ('tracer-0.6.9-1.fc23',))
def test_nevr_failed(nevr):
    assert run_task(nevr) == FAILED
