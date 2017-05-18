import logging
if __name__ == '__main__':
    # Set up logging ASAP to see potential problems during import.
    # Don't set it up when not running as the main script, someone else handles
    # that then.
    logging.basicConfig()

import os
import sys

from libtaskotron import check

# before we import from pyversions, let's add our dir to sys.path
sys.path.insert(0, os.path.dirname(__file__))

from taskotron_python_versions import task_two_three
from taskotron_python_versions.common import log


def run(koji_build, workdir='.', artifactsdir='artifacts'):
    '''The main method to run from Taskotron'''
    workdir = os.path.abspath(workdir)

    # find files to run on
    files = sorted(os.listdir(workdir))
    rpms = []
    for file_ in files:
        path = os.path.join(workdir, file_)
        if file_.endswith('.rpm'):
            rpms.append(path)
        else:
            log.debug('Ignoring non-rpm file: {}'.format(path))
    if not rpms:
        log.warn('No binary rpm files found')

    artifact = os.path.join(artifactsdir, 'output.log')

    # put all the details form subtask in this list
    details = []
    details.append(task_two_three(rpms, koji_build, artifact))

    # finally, the main detail with overall results
    outcome = 'PASSED'
    for detail in details:
        if detail.outcome == 'FAILED':
            outcome = 'FAILED'
            break

    details.append(check.CheckDetail(checkname='python-versions',
                                     item=koji_build,
                                     report_type=check.ReportType.KOJI_BUILD,
                                     outcome=outcome))
    if outcome == 'FAILED':
        details[-1].artifact = artifact

    summary = 'python-versions {} for {}.'.format(outcome, koji_build)
    log.info(summary)

    output = check.export_YAML(details)
    return output


if __name__ == '__main__':
    run('test')
