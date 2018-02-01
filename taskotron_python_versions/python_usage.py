import mmap

from .common import log, write_to_artifact


MESSAGE = """You've used /usr/bin/python during build on the following arches:

  {}

Use /usr/bin/python3 or /usr/bin/python2 explicitly.
/usr/bin/python will be removed or switched to Python 3 in the future.
"""

INFO_URL = ('https://fedoraproject.org/wiki/Changes/'
            'Avoid_usr_bin_python_in_RPM_Build')
WARNING = 'DEPRECATION WARNING: python2 invoked with /usr/bin/python'


def file_contains(path, needle):
    """Check if the file residing on the given path contains the given needle
    """
    # Since we have no idea if build.log is valid utf8, let's convert our ASCII
    # needle to bytes and use bytes everywhere.
    # This also allow us to use mmap on Python 3.
    # Be explicit here, to make it fail early if our needle is not ASCII.
    needle = needle.encode('ascii')

    with open(path, 'rb') as f:
        # build.logs tend to be laaaarge, so using a single read() is bad idea;
        # let's optimize prematurely because practicality beats purity

        # Memory-mapped file object behaving like bytearray
        mmf = mmap.mmap(f.fileno(),
                        length=0,  # = determine automatically
                        access=mmap.ACCESS_READ)
        try:
            return mmf.find(needle) != -1
        finally:
            # mmap context manager is Python 3 only
            mmf.close()


def task_python_usage(logs, koji_build, artifact):
    """Parses the build.logs for /usr/bin/python invocation warning
    """
    # libtaskotron is not available on Python 3, so we do it inside
    # to make the above functions testable anyway
    from libtaskotron import check

    outcome = 'PASSED'

    problem_arches = set()

    for buildlog in logs:  # not "log" because we use that name for logging
        log.debug('Will parse {}'.format(buildlog))

        if file_contains(buildlog, WARNING):
            log.debug('{} contains our warning'.format(buildlog))
            _, _, arch = buildlog.rpartition('.')
            problem_arches.add(arch)
            outcome = 'FAILED'

    detail = check.CheckDetail(
        checkname='python-versions.python_usage',
        item=koji_build,
        report_type=check.ReportType.KOJI_BUILD,
        outcome=outcome)

    if problem_arches:
        detail.artifact = artifact
        info = '{}: {}'.format(koji_build, ', '.join(sorted(problem_arches)))
        write_to_artifact(artifact, MESSAGE.format(info), INFO_URL)
        problems = 'Problematic architectures: ' + info
    else:
        problems = 'No problems found.'

    summary = 'python-versions.python_usage {} for {}. {}'.format(
        outcome, koji_build, problems)
    log.info(summary)

    return detail
