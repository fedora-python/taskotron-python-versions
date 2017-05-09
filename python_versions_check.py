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

from pyversions import log, two_three_check


INFO_URL = ('https://python-rpm-porting.readthedocs.io/en/'
            'latest/applications.html'
            '#are-shebangs-dragging-you-down-to-python-2')
BUG_URL = 'https://github.com/fedora-python/task-python-versions/issues'
TEMPLATE = '''These RPMs require both Python 2 and Python 3:
{rpms}

Read the following document to find more information and a possible cause:
{info_url}
Or ask at #fedora-python IRC channel for help.

If you think the result is false or intentional, file a bug against:
{bug_url}
'''

WHITELIST = (
    'eric',  # https://bugzilla.redhat.com/show_bug.cgi?id=1342492
    'pungi',  # https://bugzilla.redhat.com/show_bug.cgi?id=1342497
)


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

    outcome = 'PASSED'
    bads = []

    if not rpms:
        log.warn('No binary rpm files found in: {}'.format(workdir))
    for path in rpms:
        filename = os.path.basename(path)
        log.debug('Checking {}'.format(filename))
        name, py_versions = two_three_check(path)
        if name is None:
            # RPM could not read that file, not our problem
            # error is already logged
            pass
        elif name in WHITELIST:
            log.warn('{} is excluded from this check'.format(name))
        elif len(py_versions) == 0:
            log.info('{} does not require Python, that\'s OK'.format(filename))
        elif len(py_versions) == 1:
            py_version = next(iter(py_versions))
            log.info('{} requires Python {} only, that\'s OK'
                     .format(filename, py_version))
        else:
            log.error('{} requires both Python 2 and 3, that\'s usually bad.'
                      .format(filename))
            outcome = 'FAILED'
            bads.append(filename)

    detail = check.CheckDetail(koji_build,
                               check.ReportType.KOJI_BUILD,
                               outcome)

    if bads:
        detail.artifact = os.path.join(artifactsdir, 'output.log')
        rpms = '\n'.join(bads)
        with open(detail.artifact, 'w') as f:
            f.write(TEMPLATE.format(rpms=rpms,
                                    info_url=INFO_URL,
                                    bug_url=BUG_URL))
        problems = 'Problematic RPMs:\n' + rpms
    else:
        problems = 'No problems found.'

    summary = 'python-versions {} for {}. {}'.format(
              outcome, koji_build, problems)
    log.info(summary)

    output = check.export_YAML(detail)
    return output


if __name__ == '__main__':
    run('test')
