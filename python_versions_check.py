import logging
if __name__ == '__main__':
    # Set up logging ASAP to see potential problems during import.
    # Don't set it up when not running as the main script, someone else handles
    # that then.
    logging.basicConfig()

import os
import rpm
from libtaskotron import check

log = logging.getLogger('python-versions')
log.setLevel(logging.DEBUG)
log.addHandler(logging.NullHandler())

INFO_URL = ('https://python-rpm-porting.readthedocs.io/en/latest/applications.html'
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


NEVRS_STARTS = {
    2: (b'python(abi) = 2.',),
    3: (b'python(abi) = 3.',)
}

NAME_STARTS = {
    2: (
        b'python-',
        b'python2',
        b'/usr/bin/python2',
        b'libpython2',
        b'pygtk2',
        b'pygobject2',
        b'pycairo',
        b'py-',
    ),
    3: (
        b'python3',
        b'/usr/bin/python3',
        b'libpython3',
        b'system-python'
    )
}

NAME_EXACTS = {
    2: (
        b'/usr/bin/python',
        b'python',
    )
}

NAME_NOTS = (
    b'python-rpm-macros',
    b'python-srpm-macros',
    b'python-sphinx-locale',
    b'python-multilib-conf',
)

WHITELIST = (
    'eric',  # https://bugzilla.redhat.com/show_bug.cgi?id=1342492
    'pungi',  # https://bugzilla.redhat.com/show_bug.cgi?id=1342497
)


def python_versions_check(path):
    '''
    For the binary RPM in path, report back what Python
    versions it depends on
    '''
    ts = rpm.TransactionSet()
    with open(path, 'rb') as fdno:
        try:
            hdr = ts.hdrFromFdno(fdno)
        except rpm.error as e:
            log.error('{}: {}'.format(os.path.basename(path), e))
            return None, None

    py_versions = set()

    for nevr in hdr[rpm.RPMTAG_REQUIRENEVRS]:
        for py_version, starts in NEVRS_STARTS.items():
            for start in starts:
                if nevr.startswith(start):
                    log.debug('Found dependency {}'.format(nevr.decode()))
                    log.debug('Requires Python {}'.format(py_version))
                    py_versions.add(py_version)
                    break

    for name in hdr[rpm.RPMTAG_REQUIRENAME]:
        for py_version, starts in NAME_STARTS.items():
            if py_version not in py_versions:
                for start in starts:
                    if name.startswith(start) and name not in NAME_NOTS:
                        log.debug('Found dependency {}'.format(name.decode()))
                        log.debug('Requires Python {}'.format(py_version))
                        py_versions.add(py_version)
                        break
        for py_version, exacts in NAME_EXACTS.items():
            if py_version not in py_versions:
                if name in exacts:
                    log.debug('Found dependency {}'.format(name.decode()))
                    log.debug('Requires Python {}'.format(py_version))
                    py_versions.add(py_version)

    return hdr[rpm.RPMTAG_NAME], py_versions


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
        name, py_versions = python_versions_check(path)
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
