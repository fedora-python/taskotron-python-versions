from __future__ import print_function

import subprocess
import sys


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
    if proc.returncode != 0:
        raise RuntimeError('runtask exited with {}'.format(proc.returncode))
        print(err, file=sys.stderr)


def test_eric():
    run_task('eric-6.1.6-2.fc25')
